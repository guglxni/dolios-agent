"""Policy Bridge — thin facade over the native PolicyEngine.

Translates Hermes Agent tool declarations into NemoClaw policy YAML by
delegating all policy logic to ``dolios.policy.PolicyEngine``.

This module is kept for backward-compatibility with ``orchestrator.py``
call sites. New code should import ``PolicyEngine`` directly.

When Hermes Agent declares a tool that needs network access, the bridge:
1. Looks up the tool's declared endpoints in TOOL_POLICIES
2. Delegates endpoint checking to PolicyEngine (which reads vendor YAML)
3. Generates the active policy via PolicyEngine.generate_active_policy()
4. Surfaces unknown endpoints for operator approval
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any

from dolios.io import load_yaml
from dolios.policy.engine import PolicyEngine

if TYPE_CHECKING:
    from dolios.config import DoliosConfig

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Tool endpoint declarations
# These declare *what* endpoints each Hermes tool needs.
# The actual allow/deny decision is made by PolicyEngine against the
# vendor YAML-based active policy.
# ---------------------------------------------------------------------------

TOOL_POLICIES: dict[str, dict[str, Any]] = {
    "web_search": {
        "name": "web_search",
        "endpoints": [
            {"host": "www.googleapis.com", "port": 443},
            {"host": "api.search.brave.com", "port": 443},
        ],
    },
    "github": {
        "name": "github_tools",
        "endpoints": [
            {"host": "api.github.com", "port": 443},
            {"host": "github.com", "port": 443},
        ],
    },
    "browser": {
        "name": "browser_access",
        "endpoints": [
            {"host": "*", "port": 443},
            {"host": "*", "port": 80},
        ],
    },
    "web_fetch": {
        "name": "web_fetch",
        "endpoints": [
            {"host": "*", "port": 443},
        ],
    },
    "image_generation": {
        "name": "image_generation",
        "endpoints": [
            {"host": "fal.run", "port": 443},
        ],
    },
    "email": {
        "name": "email_access",
        "endpoints": [
            {"host": "gmail.googleapis.com", "port": 443},
            {"host": "oauth2.googleapis.com", "port": 443},
        ],
    },
}

# ---------------------------------------------------------------------------
# Per-tool capability manifests (IronClaw-inspired)
# Declare the broader capability surface each tool requires beyond endpoints.
# Used by the orchestrator to enforce least-privilege at dispatch time.
# ---------------------------------------------------------------------------

CAPABILITY_MANIFESTS: dict[str, dict[str, Any]] = {
    "web_search": {
        "network": True,
        "filesystem": [],
        "description": "Query external search APIs (Google, Brave)",
    },
    "github": {
        "network": True,
        "filesystem": [],
        "description": "Access GitHub REST API for repo operations",
    },
    "browser": {
        "network": True,
        "filesystem": ["/tmp"],
        "description": "Full browser access including arbitrary URLs",
    },
    "web_fetch": {
        "network": True,
        "filesystem": [],
        "description": "Fetch content from arbitrary HTTPS endpoints",
    },
    "image_generation": {
        "network": True,
        "filesystem": ["/tmp"],
        "description": "Generate images via fal.run API",
    },
    "email": {
        "network": True,
        "filesystem": [],
        "description": "Read and send email via Gmail API",
    },
}


class PolicyBridge:
    """Facade over PolicyEngine for Hermes Agent tool policy management."""

    def __init__(self, config: DoliosConfig):
        self.config = config
        self._engine = PolicyEngine(config)
        self._skill_capabilities: dict[str, dict[str, Any]] = {}

    # ------------------------------------------------------------------
    # Path exposure — mirrors the old PolicyBridge.generated_dir attribute
    # so tests and callers can set the output directory.
    # ------------------------------------------------------------------

    @property
    def generated_dir(self) -> Path:
        return self._engine._generated_dir

    @generated_dir.setter
    def generated_dir(self, path: Path) -> None:
        self._engine._generated_dir = path
        self._engine._invalidate_cache()

    # ------------------------------------------------------------------
    # Policy generation
    # ------------------------------------------------------------------

    def generate_policy(
        self,
        enabled_tools: list[str] | None = None,
        enabled_messaging: list[str] | None = None,
        skills_dir: Path | None = None,
    ) -> Path:
        """Generate the active NemoClaw-format policy YAML.

        Converts ``enabled_tools`` declarations (from TOOL_POLICIES) and
        ``enabled_messaging`` preset names into extra network_policy blocks,
        then delegates to PolicyEngine.generate_active_policy().
        """
        extra: dict[str, Any] = {}

        for tool_key in enabled_tools or []:
            decl = TOOL_POLICIES.get(tool_key)
            if not decl:
                continue
            block_name = decl["name"]
            extra[block_name] = {
                "name": block_name,
                "endpoints": [
                    {
                        "host": ep["host"],
                        "port": ep.get("port", 443),
                        "protocol": "rest",
                        "enforcement": "enforce",
                        "tls": "terminate",
                        "rules": [{"allow": {"method": "*", "path": "/**"}}],
                    }
                    for ep in decl["endpoints"]
                ],
            }

        for preset_name in enabled_messaging or []:
            preset_data = self._engine.load_preset(preset_name)
            if preset_data:
                for block_name, block in preset_data.get("network_policies", {}).items():
                    extra[block_name] = block

        # Merge per-skill capability manifests from YAML files
        caps = self.load_skill_capabilities(skills_dir or Path("skills"))
        for cap_tool, cap_data in caps.items():
            domains = cap_data.get("network", {}).get("allow_domains", [])
            if domains:
                extra[f"skill_{cap_tool}"] = {
                    "name": f"skill_{cap_tool}",
                    "endpoints": [
                        {
                            "host": domain,
                            "port": 443,
                            "protocol": "rest",
                            "enforcement": "enforce",
                            "tls": "terminate",
                            "rules": [{"allow": {"method": "*", "path": "/**"}}],
                        }
                        for domain in domains
                    ],
                }

        return self._engine.generate_active_policy(
            tier=getattr(self.config.sandbox, "policy_tier", "balanced"),
            extra_tool_policies=extra or None,
        )

    def load_skill_capabilities(self, skills_dir: Path) -> dict[str, dict[str, Any]]:
        """Load capabilities.yaml from all skill directories."""
        result: dict[str, dict[str, Any]] = {}
        try:
            for skill_dir in sorted(skills_dir.iterdir()):
                if not skill_dir.is_dir():
                    continue
                cap_file = skill_dir / "capabilities.yaml"
                if not cap_file.exists():
                    continue
                try:
                    data = load_yaml(cap_file)
                    if data and isinstance(data, dict):
                        tool_name = data.get("tool", skill_dir.name)
                        result[tool_name] = data
                except Exception:
                    logger.warning(
                        "Malformed capabilities.yaml in %s — skipping", skill_dir.name
                    )
        except FileNotFoundError:
            pass
        self._skill_capabilities = result
        return result

    def get_capabilities_for_tool(self, tool_name: str) -> dict[str, Any] | None:
        """Return the loaded capability manifest for a tool, or None."""
        return self._skill_capabilities.get(tool_name)

    def check_endpoint(self, host: str, port: int = 443) -> bool:
        """Check if host:port is allowed by the current active policy."""
        return self._engine.check_endpoint(host, port)

    def get_policy_for_tool(self, tool_name: str) -> dict[str, Any] | None:
        """Return the endpoint declarations for a specific tool, or None."""
        return TOOL_POLICIES.get(tool_name)

    def get_capability(self, tool_name: str) -> dict[str, Any] | None:
        """Return the static capability manifest for a tool, or None."""
        return CAPABILITY_MANIFESTS.get(tool_name)

    def request_endpoint_approval(
        self, host: str, port: int, tool_name: str, reason: str
    ) -> None:
        """Surface a blocked endpoint for operator approval."""
        self._engine.request_approval(host, port, tool_name, reason)

    def load_preset(self, preset_name: str) -> dict[str, Any] | None:
        """Load a NemoClaw policy preset by name."""
        return self._engine.load_preset(preset_name)

    @property
    def engine(self) -> PolicyEngine:
        """Direct access to the underlying PolicyEngine."""
        return self._engine
