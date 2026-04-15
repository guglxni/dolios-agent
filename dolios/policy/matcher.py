"""Pure functions for NemoClaw network policy endpoint matching.

Implements the host/port/access matching rules from the NemoClaw policy
schema (version 1). No I/O — all functions are deterministic and testable.

Matching rules (in order):
1. Global wildcard '*' matches any host
2. Subdomain wildcard '*.example.com' matches 'api.example.com', 'sub.api.example.com'
   and also the bare domain 'example.com'
3. Exact match 'api.example.com' matches only 'api.example.com'
4. access: full endpoints tunnel raw TCP (WebSocket CONNECT) — host still matched,
   no path/method restriction
"""

from __future__ import annotations

import ipaddress
import socket
from urllib.parse import urlparse


def match_host(allowed: str, host: str) -> bool:
    """Match a host against an endpoint host pattern.

    Handles three patterns:
    - '*' — matches everything
    - '*.example.com' — matches 'example.com' and all subdomains
    - 'api.example.com' — exact match only
    """
    if allowed == "*":
        return True
    if allowed.startswith("*."):
        # '*.example.com' → suffix is '.example.com'
        suffix = allowed[1:]
        return host.endswith(suffix) or host == allowed[2:]
    return host == allowed


def match_endpoint(endpoint: dict, host: str, port: int) -> bool:
    """Check whether an endpoint definition allows a given host:port.

    An endpoint with ``access: full`` is a raw CONNECT tunnel (WebSocket)
    that bypasses path and method inspection, but the host and port must
    still match. The "full" access refers to no path/method restrictions,
    not unrestricted host access.
    """
    allowed_host = endpoint.get("host", "")
    allowed_port = endpoint.get("port", 443)

    if allowed_port != port:
        return False
    return match_host(allowed_host, host)


def is_endpoint_allowed(policy: dict, host: str, port: int = 443) -> bool:
    """Check host:port against all network_policies blocks in a policy dict.

    Returns True if ANY endpoint in ANY policy block allows the connection.
    Defaults to DENY (fail-closed) when no match is found.
    """
    for _name, block in policy.get("network_policies", {}).items():
        for endpoint in block.get("endpoints", []):
            if match_endpoint(endpoint, host, port):
                return True
    return False


def validate_ssrf(url: str) -> str:
    """Validate an endpoint URL — prevent SSRF against private networks.

    Raises ValueError for:
    - Non-HTTP(S) schemes
    - Missing hostname
    - Hostnames that resolve to private/loopback/link-local IPs
      (except localhost:11434 and localhost:8000 with a /v1 path prefix)

    This is the single authoritative SSRF check for the codebase.
    ``environments/nemoclaw_helpers.validate_endpoint_url`` delegates here.

    SEC-H5 / SEC-M11 — DNS Rebinding Limitation:
    This check resolves DNS at validation time. An attacker controlling a DNS
    record could pass validation with a public IP, then switch the record to a
    private IP before the actual HTTP request is made (DNS rebinding / TOCTOU).
    Full protection requires the HTTP client to pin the resolved IP address from
    this call and refuse to re-resolve at request time.  For the current
    development-mode LocalBackend this is an accepted risk documented here.
    Production deployments should use a DNS-pinning HTTP client or an egress
    proxy that enforces IP allowlists at the network layer.
    """
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise ValueError(f"Only HTTP(S) endpoints allowed, got: {parsed.scheme}")

    hostname = parsed.hostname
    if not hostname:
        raise ValueError(f"No hostname in URL: {url}")

    try:
        for info in socket.getaddrinfo(hostname, None):
            addr = info[4][0]
            ip = ipaddress.ip_address(addr)
            if ip.is_private or ip.is_loopback or ip.is_link_local:
                allowed_local = (
                    ip.is_loopback
                    and parsed.port in (11434, 8000)
                    and (not parsed.path or parsed.path.startswith("/v1"))
                )
                if not allowed_local:
                    raise ValueError(
                        f"Endpoint {hostname} resolves to private IP {addr}. "
                        "Only localhost:11434 and localhost:8000 with /v1 path allowed."
                    )
    except socket.gaierror as exc:
        raise ValueError(
            f"DNS resolution failed for {hostname} — rejecting (fail-closed). "
            "If this is a valid endpoint, ensure DNS is reachable."
        ) from exc

    return url
