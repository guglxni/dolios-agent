"""NemoClaw-native PolicyEngine for Dolios.

Implements the full NemoClaw policy contract as a Python-native engine:
- Deny-by-default network egress (fail-closed on missing policy)
- Three-tier system (restricted / balanced / open) from vendor tiers.yaml
- Preset composition from vendor presets/*.yaml
- Endpoint matching with wildcard / subdomain / access:full support
- Inference provider auto-registration from config
- SSRF validation (single authoritative implementation)
- Operator approval flow for unknown/blocked endpoints

Replaces the reimplemented Python dicts in policy_bridge.py and the
string-splitting endpoint logic in nemoclaw_helpers.py.
"""

from __future__ import annotations

import fcntl
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any
from urllib.parse import urlparse

from dolios.io import load_yaml, save_yaml
from dolios.policy.matcher import is_endpoint_allowed, validate_ssrf
from dolios.policy.presets import (
    load_base_policy,
    load_preset,
    load_tier_definitions,
    merge_preset_into_policy,
)

if TYPE_CHECKING:
    from dolios.config import DoliosConfig

logger = logging.getLogger(__name__)

GENERATED_POLICY_DIR = Path("policies/generated")
ACTIVE_POLICY_NAME = "dolios-active.yaml"


class PolicyEngine:
    """Native Python implementation of the NemoClaw policy contract.

    Loads and composes policy from vendor YAML files rather than
    reimplementing policy logic as static Python dicts.

    The engine is stateless except for a mtime-based cache on the
    active policy file. It is safe to instantiate once and hold for
    the lifetime of the process.
    """

    def __init__(self, config: DoliosConfig):
        self.config = config
        self._generated_dir = GENERATED_POLICY_DIR
        self._cached_policy: dict | None = None
        self._policy_mtime: float = 0.0

    @property
    def active_policy_path(self) -> Path:
        return self._generated_dir / ACTIVE_POLICY_NAME

    # ------------------------------------------------------------------
    # Policy generation
    # ------------------------------------------------------------------

    def generate_active_policy(
        self,
        tier: str | None = None,
        extra_tool_policies: dict[str, Any] | None = None,
    ) -> Path:
        """Generate and write the active NemoClaw-format policy YAML.

        Composition order (later entries win on key collision):
        1. Base NemoClaw sandbox policy (openclaw-sandbox.yaml) — deny-by-default
        2. Tier presets (from tiers.yaml + presets/*.yaml)
        3. Inference provider endpoints (from config)
        4. Extra tool policies (caller-supplied dict)

        Args:
            tier: One of 'restricted', 'balanced', 'open'.
                  Defaults to config.sandbox.policy_tier or 'balanced'.
            extra_tool_policies: Additional ``network_policies`` blocks to merge.

        Returns:
            Path to the written active policy file.
        """
        self._generated_dir.mkdir(parents=True, exist_ok=True)

        effective_tier = tier or getattr(self.config.sandbox, "policy_tier", "balanced")

        # 1. Base policy
        policy = load_base_policy()
        if "network_policies" not in policy:
            policy["network_policies"] = {}

        # 2. Tier presets
        for preset_data in self._resolve_tier_presets(effective_tier):
            merge_preset_into_policy(policy, preset_data)

        # 3. Inference provider endpoints
        self._add_inference_endpoints(policy)

        # 4. Caller-supplied tool policies
        if extra_tool_policies:
            for name, block in extra_tool_policies.items():
                policy["network_policies"][name] = block

        save_yaml(self.active_policy_path, policy)
        self._invalidate_cache()

        count = len(policy.get("network_policies", {}))
        logger.info(
            "Generated active policy: tier=%s, %d network policy blocks → %s",
            effective_tier,
            count,
            self.active_policy_path,
        )
        return self.active_policy_path

    # ------------------------------------------------------------------
    # Endpoint checking
    # ------------------------------------------------------------------

    def check_endpoint(self, host: str, port: int = 443) -> bool:
        """Check if host:port is allowed by the current active policy.

        Defaults to DENY if no active policy exists (fail-closed).
        Uses file mtime caching to avoid re-reading on every call.
        """
        try:
            current_mtime = self.active_policy_path.stat().st_mtime
        except FileNotFoundError:
            logger.warning("No active policy found — defaulting to DENY ALL")
            return False

        if current_mtime != self._policy_mtime:
            self._cached_policy = load_yaml(self.active_policy_path)
            self._policy_mtime = current_mtime

        policy = self._cached_policy
        if not policy:
            logger.warning("Active policy is empty — defaulting to DENY ALL")
            return False

        return is_endpoint_allowed(policy, host, port)

    def validate_url(self, url: str) -> str:
        """Validate an endpoint URL against SSRF rules.

        Delegates to the authoritative ``validate_ssrf`` implementation.
        Raises ValueError on violation.
        """
        return validate_ssrf(url)

    # ------------------------------------------------------------------
    # Tier / preset introspection
    # ------------------------------------------------------------------

    def get_tier_names(self) -> list[str]:
        """Return all defined tier names (from vendor tiers.yaml)."""
        return [t["name"] for t in load_tier_definitions()]

    def load_preset(self, name: str) -> dict[str, Any] | None:
        """Load a single named preset. Returns None if not found."""
        return load_preset(name)

    # ------------------------------------------------------------------
    # Operator approval flow
    # ------------------------------------------------------------------

    def request_approval(
        self,
        host: str,
        port: int,
        tool_name: str,
        reason: str,
    ) -> None:
        """Surface a blocked endpoint for operator approval.

        Appends an entry to ``~/.dolios/pending_approvals.yaml``.
        Uses exclusive file locking to prevent concurrent write races.
        """
        pending_file = self.config.home / "pending_approvals.yaml"
        pending_file.parent.mkdir(parents=True, exist_ok=True)
        lock_path = pending_file.with_suffix(".lock")

        with open(lock_path, "w") as lock_fd:
            fcntl.flock(lock_fd, fcntl.LOCK_EX)
            try:
                pending = load_yaml(pending_file, default=[])
                pending.append(
                    {
                        "host": host,
                        "port": port,
                        "tool": tool_name,
                        "reason": reason,
                        "status": "pending",
                        "requested_at": datetime.now(UTC).isoformat(),
                    }
                )
                save_yaml(pending_file, pending)
            finally:
                fcntl.flock(lock_fd, fcntl.LOCK_UN)

        logger.warning(
            "Endpoint approval requested: %s:%d (tool: %s)", host, port, tool_name
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _resolve_tier_presets(self, tier_name: str) -> list[dict[str, Any]]:
        """Load and return all preset data dicts for the given tier."""
        tiers = load_tier_definitions()
        tier_def = next((t for t in tiers if t["name"] == tier_name), None)

        if tier_def is None:
            logger.warning("Unknown tier %r — no presets loaded", tier_name)
            return []

        presets: list[dict[str, Any]] = []
        for preset_ref in tier_def.get("presets", []):
            preset_name = preset_ref["name"] if isinstance(preset_ref, dict) else preset_ref
            preset_data = load_preset(preset_name)
            if preset_data:
                presets.append(preset_data)
            else:
                logger.warning("Preset %r not found in vendor directory — skipping", preset_name)

        return presets

    def _add_inference_endpoints(self, policy: dict[str, Any]) -> None:
        """Add network_policy blocks for each configured inference provider."""
        for name, provider in self.config.inference.providers.items():
            base_url = provider.get("base_url", "")
            if not base_url:
                continue
            # SEC-M4: Check all localhost variants — "localhost", "127.0.0.1", "::1",
            # and "host.docker.internal" must not be auto-registered as policy endpoints.
            _local_markers = ("localhost", "127.0.0.1", "::1", "host.docker.internal")
            if any(m in base_url for m in _local_markers):
                continue

            parsed = urlparse(base_url)
            host = parsed.hostname or ""
            if not host:
                continue

            policy["network_policies"][f"inference_{name}"] = {
                "name": f"inference_{name}",
                "endpoints": [
                    {
                        "host": host,
                        "port": 443,
                        "protocol": "rest",
                        "enforcement": "enforce",
                        "tls": "terminate",
                        "rules": [{"allow": {"method": "POST", "path": "/v1/**"}}],
                    }
                ],
            }

    def _invalidate_cache(self) -> None:
        """Reset the mtime cache so the next check_endpoint re-reads the file."""
        self._cached_policy = None
        self._policy_mtime = 0.0
