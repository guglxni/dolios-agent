"""Policy Bridge — translates Hermes Agent tool declarations into NemoClaw policy YAML.

Generates NemoClaw-format network_policies with:
- Named policy blocks per tool/toolset
- Endpoint definitions with host, port, protocol, enforcement, tls
- HTTP method + path rules
- Support for policy presets (messaging, docker, pypi, etc.)

When Hermes Agent declares a tool that needs network access, the bridge:
1. Reads the tool's required endpoints from its manifest/registry
2. Maps them to NemoClaw network_policy format
3. Checks against the active policy
4. Surfaces unknown endpoints for operator approval
"""

from __future__ import annotations

import fcntl
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from dolios.config import DoliosConfig
from dolios.io import load_yaml, save_yaml

logger = logging.getLogger(__name__)


# Hermes tool → NemoClaw network_policies mapping
# Matches the format in vendor/nemoclaw/nemoclaw-blueprint/policies/presets/
TOOL_POLICIES: dict[str, dict[str, Any]] = {
    "web_search": {
        "name": "web_search",
        "endpoints": [
            {"host": "www.googleapis.com", "port": 443, "protocol": "rest",
             "enforcement": "enforce", "tls": "terminate",
             "rules": [{"allow": {"method": "GET", "path": "/**"}}]},
            {"host": "api.search.brave.com", "port": 443, "protocol": "rest",
             "enforcement": "enforce", "tls": "terminate",
             "rules": [{"allow": {"method": "GET", "path": "/**"}}]},
        ],
    },
    "github": {
        "name": "github_tools",
        "endpoints": [
            {"host": "api.github.com", "port": 443, "protocol": "rest",
             "enforcement": "enforce", "tls": "terminate",
             "rules": [{"allow": {"method": "*", "path": "/**"}}]},
            {"host": "github.com", "port": 443, "protocol": "rest",
             "enforcement": "enforce", "tls": "terminate",
             "rules": [{"allow": {"method": "GET", "path": "/**"}}]},
        ],
    },
    "browser": {
        "name": "browser_access",
        "endpoints": [
            {"host": "*", "port": 443, "protocol": "rest",
             "enforcement": "enforce", "tls": "passthrough",
             "rules": [{"allow": {"method": "*", "path": "/**"}}]},
            {"host": "*", "port": 80, "protocol": "rest",
             "enforcement": "enforce", "tls": "passthrough",
             "rules": [{"allow": {"method": "GET", "path": "/**"}}]},
        ],
    },
    "web_fetch": {
        "name": "web_fetch",
        "endpoints": [
            {"host": "*", "port": 443, "protocol": "rest",
             "enforcement": "enforce", "tls": "passthrough",
             "rules": [{"allow": {"method": "GET", "path": "/**"}}]},
        ],
    },
    "image_generation": {
        "name": "image_generation",
        "endpoints": [
            {"host": "fal.run", "port": 443, "protocol": "rest",
             "enforcement": "enforce", "tls": "terminate",
             "rules": [{"allow": {"method": "POST", "path": "/**"}}]},
        ],
    },
    "email": {
        "name": "email_access",
        "endpoints": [
            {"host": "gmail.googleapis.com", "port": 443, "protocol": "rest",
             "enforcement": "enforce", "tls": "terminate",
             "rules": [{"allow": {"method": "*", "path": "/**"}}]},
            {"host": "oauth2.googleapis.com", "port": 443, "protocol": "rest",
             "enforcement": "enforce", "tls": "terminate",
             "rules": [{"allow": {"method": "POST", "path": "/**"}}]},
        ],
    },
}

# Messaging presets (match vendor/nemoclaw presets)
MESSAGING_POLICIES: dict[str, dict[str, Any]] = {
    "telegram": {
        "name": "telegram_bot",
        "endpoints": [
            {"host": "api.telegram.org", "port": 443, "protocol": "rest",
             "enforcement": "enforce", "tls": "terminate",
             "rules": [
                 {"allow": {"method": "GET", "path": "/bot*/**"}},
                 {"allow": {"method": "POST", "path": "/bot*/**"}},
             ]},
        ],
    },
    "discord": {
        "name": "discord",
        "endpoints": [
            {"host": "discord.com", "port": 443, "protocol": "rest",
             "enforcement": "enforce", "tls": "terminate",
             "rules": [{"allow": {"method": "*", "path": "/**"}}]},
            {"host": "gateway.discord.gg", "port": 443, "protocol": "rest",
             "enforcement": "enforce", "tls": "terminate",
             "rules": [{"allow": {"method": "*", "path": "/**"}}]},
            {"host": "cdn.discordapp.com", "port": 443, "protocol": "rest",
             "enforcement": "enforce", "tls": "terminate",
             "rules": [{"allow": {"method": "GET", "path": "/**"}}]},
        ],
    },
    "slack": {
        "name": "slack",
        "endpoints": [
            {"host": "slack.com", "port": 443, "protocol": "rest",
             "enforcement": "enforce", "tls": "terminate",
             "rules": [{"allow": {"method": "*", "path": "/**"}}]},
            {"host": "api.slack.com", "port": 443, "protocol": "rest",
             "enforcement": "enforce", "tls": "terminate",
             "rules": [{"allow": {"method": "*", "path": "/**"}}]},
            {"host": "hooks.slack.com", "port": 443, "protocol": "rest",
             "enforcement": "enforce", "tls": "terminate",
             "rules": [{"allow": {"method": "POST", "path": "/**"}}]},
        ],
    },
}


class PolicyBridge:
    """Bridges Hermes Agent tool declarations to NemoClaw network policies."""

    def __init__(self, config: DoliosConfig):
        self.config = config
        self.policy_dir = Path("policies")
        self.generated_dir = self.policy_dir / "generated"
        self._cached_policy: dict | None = None
        self._policy_mtime: float = 0.0

    def generate_policy(
        self,
        enabled_tools: list[str] | None = None,
        enabled_messaging: list[str] | None = None,
    ) -> Path:
        """Generate NemoClaw-format policy YAML from enabled Hermes tools.

        Returns:
            Path to the generated policy file.
        """
        self.generated_dir.mkdir(parents=True, exist_ok=True)

        # Start with the base Dolios sandbox policy
        policy = self._load_base_policy()

        # Ensure network_policies dict exists
        if "network_policies" not in policy:
            policy["network_policies"] = {}

        # Add inference provider policies
        for name, provider in self.config.inference.providers.items():
            base_url = provider.get("base_url", "")
            if not base_url or "localhost" in base_url or "host.docker.internal" in base_url:
                continue
            host = base_url.split("//")[-1].split("/")[0].split(":")[0]
            policy["network_policies"][f"inference_{name}"] = {
                "name": f"inference_{name}",
                "endpoints": [{
                    "host": host,
                    "port": 443,
                    "protocol": "rest",
                    "enforcement": "enforce",
                    "tls": "terminate",
                    "rules": [{"allow": {"method": "POST", "path": "/v1/**"}}],
                }],
            }

        # Add tool-specific policies
        tools = enabled_tools or list(TOOL_POLICIES.keys())
        for tool_name in tools:
            if policy_def := TOOL_POLICIES.get(tool_name):
                policy["network_policies"][policy_def["name"]] = policy_def

        # Add messaging platform policies
        messaging = enabled_messaging or []
        for platform in messaging:
            if msg_policy := MESSAGING_POLICIES.get(platform):
                policy["network_policies"][msg_policy["name"]] = msg_policy

        # Write generated policy
        output_path = self.generated_dir / "dolios-active.yaml"
        save_yaml(output_path, policy)

        policy_count = len(policy.get("network_policies", {}))
        logger.info(f"Generated policy with {policy_count} network policy blocks")
        return output_path

    def check_endpoint(self, host: str, port: int = 443) -> bool:
        """Check if an endpoint is allowed by the current policy.

        Defaults to DENY if no policy is loaded (fail-closed).
        Uses file mtime caching to avoid re-reading the policy on every call.
        """
        active_path = self.generated_dir / "dolios-active.yaml"
        try:
            current_mtime = active_path.stat().st_mtime
        except FileNotFoundError:
            logger.warning("No active policy found — defaulting to DENY ALL")
            return False
        if current_mtime != self._policy_mtime:
            self._cached_policy = load_yaml(active_path)
            self._policy_mtime = current_mtime
        policy = self._cached_policy
        if not policy:
            logger.warning("No active policy found — defaulting to DENY ALL")
            return False

        for _name, policy_block in policy.get("network_policies", {}).items():
            for endpoint in policy_block.get("endpoints", []):
                allowed_host = endpoint.get("host", "")
                allowed_port = endpoint.get("port", 443)

                if allowed_port != port:
                    continue

                if allowed_host == "*":
                    return True
                if allowed_host.startswith("*."):
                    suffix = allowed_host[1:]
                    if host.endswith(suffix) or host == allowed_host[2:]:
                        return True
                elif host == allowed_host:
                    return True

        return False

    def get_policy_for_tool(self, tool_name: str) -> dict[str, Any] | None:
        """Get the NemoClaw policy block for a specific tool."""
        return TOOL_POLICIES.get(tool_name)

    def request_endpoint_approval(
        self, host: str, port: int, tool_name: str, reason: str
    ) -> None:
        """Surface a new endpoint for operator approval.

        Uses file locking to prevent race conditions when multiple
        processes write to pending_approvals.yaml concurrently.
        """
        pending_file = self.config.home / "pending_approvals.yaml"
        pending_file.parent.mkdir(parents=True, exist_ok=True)
        lock_path = pending_file.with_suffix(".lock")

        with open(lock_path, "w") as lock_fd:
            fcntl.flock(lock_fd, fcntl.LOCK_EX)
            try:
                pending = load_yaml(pending_file, default=[])
                pending.append({
                    "host": host,
                    "port": port,
                    "tool": tool_name,
                    "reason": reason,
                    "status": "pending",
                    "requested_at": datetime.now(timezone.utc).isoformat(),
                })
                save_yaml(pending_file, pending)
            finally:
                fcntl.flock(lock_fd, fcntl.LOCK_UN)

        logger.warning(f"Endpoint approval requested: {host}:{port} (tool: {tool_name})")

    def load_preset(self, preset_name: str) -> dict[str, Any] | None:
        """Load a NemoClaw policy preset from vendor or local presets."""
        import re

        # Validate preset name to prevent path traversal
        if not re.match(r"^[a-zA-Z0-9_-]+$", preset_name):
            raise ValueError(f"Invalid preset name (alphanumeric, hyphens, underscores only): {preset_name}")

        # Check vendor presets first
        vendor_preset = (
            Path("vendor/nemoclaw/nemoclaw-blueprint/policies/presets")
            / f"{preset_name}.yaml"
        )
        result = load_yaml(vendor_preset)
        if result is not None:
            return result

        # Check local presets
        local_preset = self.policy_dir / "presets" / f"{preset_name}.yaml"
        return load_yaml(local_preset)

    def _load_base_policy(self) -> dict:
        """Load the base Dolios sandbox policy."""
        # Try Dolios-specific policy first
        dolios_policy = Path("dolios-blueprint/policies/dolios-sandbox.yaml")
        data = load_yaml(dolios_policy)
        if data is not None:
            return data

        # Fallback to policies/ directory
        base_path = self.policy_dir / "dolios-default.yaml"
        data = load_yaml(base_path)
        if data is not None:
            # Convert old format to NemoClaw format if needed
            if "network" in data and "network_policies" not in data:
                return self._convert_legacy_policy(data)
            return data

        # Minimal default
        return {
            "version": 1,
            "filesystem_policy": {
                "read_write": ["/sandbox", "/tmp"],
                "read_only": ["/usr", "/lib", "/etc"],
            },
            "process": {"run_as_user": "sandbox", "run_as_group": "sandbox"},
            "network_policies": {},
        }

    def _convert_legacy_policy(self, legacy: dict) -> dict:
        """Convert the simple allow-list format to NemoClaw network_policies."""
        policy: dict[str, Any] = {
            "version": 1,
            "filesystem_policy": {
                "read_write": legacy.get("filesystem", {}).get("writable", ["/sandbox", "/tmp"]),
                "read_only": legacy.get("filesystem", {}).get("readonly", []),
            },
            "process": {
                "run_as_user": "sandbox",
                "run_as_group": "sandbox",
            },
            "network_policies": {},
        }

        for entry in legacy.get("network", {}).get("allow", []):
            host = entry.get("host", "")
            label = entry.get("label", host).replace(" ", "_").lower()
            safe_name = "".join(c if c.isalnum() or c == "_" else "_" for c in label)

            policy["network_policies"][safe_name] = {
                "name": safe_name,
                "endpoints": [{
                    "host": host,
                    "port": entry.get("ports", [443])[0] if entry.get("ports") else 443,
                    "protocol": "rest",
                    "enforcement": "enforce",
                    "tls": "terminate",
                    "rules": [{"allow": {"method": "*", "path": "/**"}}],
                }],
            }

        return policy

    def _load_active_policy(self) -> dict | None:
        """Load the currently active generated policy."""
        active_path = self.generated_dir / "dolios-active.yaml"
        return load_yaml(active_path)
