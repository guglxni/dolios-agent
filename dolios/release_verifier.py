"""Release-readiness verification checks for Dolios."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from dolios.io import load_yaml

if TYPE_CHECKING:
    from pathlib import Path

    from dolios.config import DoliosConfig


REQUIRED_UPSTREAM_REPOS = {
    "hermes-agent",
    "nemoclaw",
    "hermes-agent-self-evolution",
}


@dataclass(frozen=True)
class ReleaseCheckResult:
    """Result for a single release verification check."""

    name: str
    passed: bool
    details: str


class ReleaseVerifier:
    """Runs production-readiness checks for release gating."""

    def __init__(self, config: DoliosConfig, project_dir: Path):
        self.config = config
        self.project_dir = project_dir

    def run_checks(self) -> list[ReleaseCheckResult]:
        """Run all release checks and return results."""
        return [
            self._check_upstream_manifest(),
            self._check_aidlc_sync_metadata(),
            self._check_optional_hermes_tool_dependencies(),
            self._check_fusion_compatibility(),
            self._check_policy_generation(),
        ]

    @staticmethod
    def is_ready(results: list[ReleaseCheckResult]) -> bool:
        """Return whether all checks passed."""
        return all(item.passed for item in results)

    def _check_upstream_manifest(self) -> ReleaseCheckResult:
        manifest_path = self.project_dir / "vendor" / "upstream-manifest.yaml"
        if not manifest_path.exists():
            return ReleaseCheckResult(
                name="upstream-manifest",
                passed=False,
                details="vendor/upstream-manifest.yaml is missing",
            )

        manifest = load_yaml(manifest_path, default={}) or {}
        repos = manifest.get("repos", [])
        names = {item.get("name") for item in repos if isinstance(item, dict)}
        missing = sorted(REQUIRED_UPSTREAM_REPOS - names)
        if missing:
            return ReleaseCheckResult(
                name="upstream-manifest",
                passed=False,
                details=f"missing repos: {', '.join(missing)}",
            )

        return ReleaseCheckResult(
            name="upstream-manifest",
            passed=True,
            details=f"tracked repos: {len(names)}",
        )

    def _check_aidlc_sync_metadata(self) -> ReleaseCheckResult:
        sync_path = self.project_dir / ".aidlc-rule-details" / "upstream-sync.yaml"
        if not sync_path.exists():
            return ReleaseCheckResult(
                name="aidlc-sync",
                passed=False,
                details=".aidlc-rule-details/upstream-sync.yaml is missing",
            )

        metadata = load_yaml(sync_path, default={}) or {}
        source_sha = metadata.get("source_sha", "")
        files_synced = int(metadata.get("files_synced", 0) or 0)

        if not source_sha or files_synced <= 0:
            return ReleaseCheckResult(
                name="aidlc-sync",
                passed=False,
                details="invalid AI-DLC sync metadata",
            )

        return ReleaseCheckResult(
            name="aidlc-sync",
            passed=True,
            details=f"files synced: {files_synced}",
        )

    def _check_fusion_compatibility(self) -> ReleaseCheckResult:
        from dolios.integrations import DoliosFusionRuntime

        runtime = DoliosFusionRuntime(self.config)
        snapshot = runtime.compatibility_snapshot()

        missing: list[str] = []
        for symbol, ok in snapshot.get("hermes", {}).items():
            if not ok:
                missing.append(f"hermes:{symbol}")

        for symbol, ok in snapshot.get("evolution", {}).items():
            if not ok:
                missing.append(f"evolution:{symbol}")

        sandbox_enabled = bool(snapshot.get("sandbox", {}).get("enabled", False))
        if self.config.sandbox.enabled and not sandbox_enabled:
            missing.append("sandbox:adapter")

        if missing:
            return ReleaseCheckResult(
                name="fusion-compat",
                passed=False,
                details=f"missing symbols: {', '.join(missing)}",
            )

        return ReleaseCheckResult(
            name="fusion-compat",
            passed=True,
            details="all required symbols available",
        )

    def _check_optional_hermes_tool_dependencies(self) -> ReleaseCheckResult:
        """Surface optional Hermes tool dependency status as non-blocking info."""
        from dolios.integrations.hermes_adapter import HermesRuntimeAdapter

        status = HermesRuntimeAdapter.optional_dependency_status()
        missing = sorted(name for name, installed in status.items() if not installed)

        if missing:
            return ReleaseCheckResult(
                name="optional-tool-deps",
                passed=True,
                details=(
                    "missing optional deps: "
                    f"{', '.join(missing)} (related tools remain disabled)"
                ),
            )

        return ReleaseCheckResult(
            name="optional-tool-deps",
            passed=True,
            details="all optional Hermes tool deps available",
        )

    def _check_policy_generation(self) -> ReleaseCheckResult:
        from dolios.policy_bridge import PolicyBridge

        bridge = PolicyBridge(self.config)
        policy_path = bridge.generate_policy()

        if not policy_path.exists():
            return ReleaseCheckResult(
                name="policy-generation",
                passed=False,
                details="failed to generate active policy",
            )

        return ReleaseCheckResult(
            name="policy-generation",
            passed=True,
            details=str(policy_path),
        )
