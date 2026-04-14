"""Helper types and utilities for the NemoClaw backend (CQ-M2).

Extracted from nemoclaw_backend.py to keep both files under 400 lines.
"""

from __future__ import annotations

import logging
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

DOLIOS_BLUEPRINT_DIR = Path("dolios-blueprint")
STATE_DIR_BASE = Path.home() / ".dolios" / "state" / "runs"


@dataclass
class SandboxState:
    """Current state of the NemoClaw sandbox."""

    running: bool = False
    sandbox_name: str = ""
    run_id: str = ""
    workspace_path: str = "/sandbox/workspace"
    policy_loaded: bool = False


@dataclass
class CommandResult:
    """Result of executing a command in the sandbox."""

    exit_code: int
    stdout: str
    stderr: str
    timed_out: bool = False


@dataclass
class BlueprintPlan:
    """Plan output from the blueprint lifecycle."""

    run_id: str
    profile: str
    sandbox: dict[str, Any]
    inference: dict[str, Any]
    policy_additions: dict[str, Any]
    dry_run: bool = False


def find_openshell() -> str | None:
    """Find the OpenShell binary."""
    return shutil.which("openshell")


def run_cmd(
    args: list[str],
    *,
    check: bool = True,
    capture: bool = True,
    timeout: int = 60,
) -> subprocess.CompletedProcess[str]:
    """Run a command safely — never uses shell=True."""
    logger.debug(f"Running: {' '.join(args)}")
    return subprocess.run(
        args,
        capture_output=capture,
        text=True,
        check=check,
        timeout=timeout,
    )


def validate_endpoint_url(url: str) -> str:
    """Validate endpoint URL — prevent SSRF against private networks.

    Adapted from vendor/nemoclaw runner.py validate_endpoint_url().
    """
    import ipaddress
    import socket
    from urllib.parse import urlparse

    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise ValueError(f"Only HTTP(S) endpoints allowed, got: {parsed.scheme}")

    hostname = parsed.hostname
    if not hostname:
        raise ValueError(f"No hostname in URL: {url}")

    # Resolve and check for private IPs
    try:
        for info in socket.getaddrinfo(hostname, None):
            addr = info[4][0]
            ip = ipaddress.ip_address(addr)
            if ip.is_private or ip.is_loopback or ip.is_link_local:
                # Allow localhost only for known local inference ports
                # with path prefix validation
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
