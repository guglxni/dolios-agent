"""SandboxBackend abstract base class, shared data types, and backend factory.

All sandbox implementations (OpenShell, Docker, Local) implement the
``SandboxBackend`` contract, matching the NemoClaw plan/apply/execute/
status/rollback lifecycle from nemoclaw-blueprint/orchestrator/runner.py.
"""

from __future__ import annotations

import abc
import shutil
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from dolios.config import DoliosConfig

STATE_DIR_BASE = Path.home() / ".dolios" / "state" / "runs"
DOLIOS_BLUEPRINT_DIR = Path("dolios-blueprint")


# ---------------------------------------------------------------------------
# Shared data types (previously in environments/nemoclaw_helpers.py)
# ---------------------------------------------------------------------------


@dataclass
class SandboxState:
    """Runtime state of the sandbox."""

    running: bool = False
    sandbox_name: str = ""
    run_id: str = ""
    workspace_path: str = "/sandbox/workspace"
    policy_loaded: bool = False


@dataclass
class CommandResult:
    """Result of executing a command inside the sandbox."""

    exit_code: int
    stdout: str
    stderr: str
    timed_out: bool = False


@dataclass
class BlueprintPlan:
    """Resolved deployment plan from the blueprint lifecycle."""

    run_id: str
    profile: str
    sandbox: dict[str, Any]
    inference: dict[str, Any]
    policy_additions: dict[str, Any]
    dry_run: bool = False


# ---------------------------------------------------------------------------
# Abstract base class
# ---------------------------------------------------------------------------


class SandboxBackend(abc.ABC):
    """Abstract contract for Dolios sandbox backends.

    Each implementation wraps a specific isolation mechanism (OpenShell,
    Docker, or bare local process) while exposing the same lifecycle.

    Subclasses that rely on the blueprint.yaml plan/apply pattern should
    extend ``BlueprintSandboxBackend`` instead, which provides a shared
    ``plan()`` and ``status()`` implementation.
    """

    @abc.abstractmethod
    def plan(self, dry_run: bool = False) -> BlueprintPlan:
        """Validate blueprint and resolve the deployment plan."""

    @abc.abstractmethod
    async def apply(self) -> None:
        """Create and configure the sandbox."""

    @abc.abstractmethod
    async def execute(
        self,
        command: str,
        timeout: float = 120.0,
        workdir: str | None = None,
    ) -> CommandResult:
        """Execute a command inside the sandbox."""

    @abc.abstractmethod
    def status(self) -> dict[str, Any]:
        """Report the current sandbox state."""

    @abc.abstractmethod
    async def rollback(self) -> None:
        """Stop and remove the sandbox."""

    async def start(self) -> None:
        """Bootstrap: plan then apply."""
        self.plan()
        await self.apply()

    async def stop(self) -> None:
        """Graceful shutdown (alias for rollback)."""
        await self.rollback()


# ---------------------------------------------------------------------------
# Shared blueprint-based planning (OpenShell and Docker inherit this)
# ---------------------------------------------------------------------------


class BlueprintSandboxBackend(SandboxBackend):
    """Intermediate base that implements plan() and status() from blueprint.yaml.

    OpenShellBackend and DockerBackend both use this; LocalBackend does not.
    """

    def __init__(self, config: DoliosConfig) -> None:
        self.config = config
        self.state = SandboxState(sandbox_name=config.sandbox.sandbox_name)
        self._plan: BlueprintPlan | None = None

    def plan(self, dry_run: bool = False) -> BlueprintPlan:
        """PLAN: Validate blueprint, resolve inference profile, check prerequisites."""
        from dolios.io import utc_now_iso

        blueprint = self._load_blueprint()
        profile = self._resolve_profile(blueprint)
        endpoint = profile.get("endpoint", "")

        if endpoint and "localhost" not in endpoint and "host.docker.internal" not in endpoint:
            from dolios.policy.matcher import validate_ssrf

            validate_ssrf(endpoint)

        sandbox_config = blueprint.get("components", {}).get("sandbox", {})
        policy_additions = (
            blueprint.get("components", {}).get("policy", {}).get("additions", {})
        )

        timestamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
        run_id = f"dolios-{timestamp}-{uuid.uuid4().hex[:8]}"

        self._plan = BlueprintPlan(
            run_id=run_id,
            profile=profile.get("_profile_name", "default"),
            sandbox={
                "image": sandbox_config.get("image", "dolios-agent:latest"),
                "name": self.config.sandbox.sandbox_name,
                "forward_ports": sandbox_config.get("forward_ports", [8080]),
            },
            inference={
                "provider_type": profile.get("provider_type", "openai"),
                "provider_name": profile.get("provider_name", ""),
                "endpoint": profile.get("endpoint", ""),
                "model": profile.get("model", ""),
                "credential_env": profile.get("credential_env", ""),
            },
            policy_additions=policy_additions,
            dry_run=dry_run,
        )

        state_dir = STATE_DIR_BASE / run_id
        state_dir.mkdir(parents=True, exist_ok=True)

        from dolios.io import save_json

        save_json(
            state_dir / "plan.json",
            {
                "run_id": self._plan.run_id,
                "profile": self._plan.profile,
                "sandbox": self._plan.sandbox,
                "inference": self._plan.inference,
                "policy_additions": self._plan.policy_additions,
                "dry_run": self._plan.dry_run,
                "planned_at": utc_now_iso(),
            },
        )

        return self._plan

    def status(self) -> dict[str, Any]:
        """STATUS: Report sandbox state."""
        if not self.state.run_id:
            return {"running": False, "message": "No sandbox bootstrapped"}

        from dolios.io import load_json

        plan_file = STATE_DIR_BASE / self.state.run_id / "plan.json"
        state_file = STATE_DIR_BASE / self.state.run_id / "state.json"

        profile = self._plan.profile if self._plan else "default"
        inference_endpoint = self._plan.inference.get("endpoint", "") if self._plan else ""
        inference_model = self._plan.inference.get("model", "") if self._plan else ""

        result: dict[str, Any] = {
            "running": self.state.running,
            "sandbox_name": self.state.sandbox_name,
            "run_id": self.state.run_id,
            "profile": profile,
            "inference_endpoint": inference_endpoint,
            "inference_model": inference_model,
        }

        plan_data = load_json(plan_file)
        if plan_data is not None:
            result["plan"] = plan_data
        state_data = load_json(state_file)
        if state_data is not None:
            result["state"] = state_data

        return result

    def _load_blueprint(self) -> dict[str, Any]:
        """Load the Dolios blueprint.yaml."""
        from dolios.io import load_yaml

        bp_path = DOLIOS_BLUEPRINT_DIR / "blueprint.yaml"
        if not bp_path.exists():
            raise FileNotFoundError(f"Blueprint not found: {bp_path}")
        return load_yaml(bp_path, default={})

    def _resolve_profile(self, blueprint: dict[str, Any]) -> dict[str, Any]:
        """Resolve inference profile from blueprint based on config."""
        provider = self.config.inference.default_provider
        profiles = blueprint.get("components", {}).get("inference", {}).get("profiles", {})

        profile_map = {
            "openrouter": "default",
            "nvidia": "nvidia",
            "nous": "nous",
            "openai": "openai",
            "local": "local-ollama",
        }

        profile_name = profile_map.get(provider, "default")
        profile = profiles.get(profile_name, profiles.get("default", {}))
        profile["_profile_name"] = profile_name
        return profile

    def _save_running_state(self) -> None:
        from dolios.io import save_json, utc_now_iso

        if self._plan:
            state_dir = STATE_DIR_BASE / self._plan.run_id
            save_json(state_dir / "state.json", {"running": True, "applied_at": utc_now_iso()})

    def _save_stopped_state(self) -> None:
        from dolios.io import save_json, utc_now_iso

        if self.state.run_id:
            state_dir = STATE_DIR_BASE / self.state.run_id
            save_json(
                state_dir / "state.json",
                {"running": False, "rolled_back_at": utc_now_iso()},
            )


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------


def create_backend(config: DoliosConfig) -> SandboxBackend:
    """Return the most isolated backend available in the current environment.

    Selection order:
    1. OpenShell — full Landlock/seccomp isolation
    2. Docker — container isolation
    3. Local — bare process (only when allow_unsandboxed=True)

    Raises RuntimeError when no backend is available.
    """
    from dolios.sandbox.docker import DockerBackend
    from dolios.sandbox.local import LocalBackend
    from dolios.sandbox.openshell import OpenShellBackend

    if shutil.which("openshell"):
        return OpenShellBackend(config)

    if shutil.which("docker"):
        return DockerBackend(config)

    if getattr(config, "allow_unsandboxed", False):
        return LocalBackend(config)

    raise RuntimeError(
        "No sandbox available. Install OpenShell or Docker, "
        "or set allow_unsandboxed=True in config for local-only mode."
    )
