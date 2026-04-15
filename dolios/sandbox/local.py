"""Local sandbox backend — no isolation, development-only.

SECURITY WARNING: This backend provides NO sandboxing. Commands run directly
as the current OS user with full filesystem and network access.

Only activated when ``config.allow_unsandboxed = True``. Should never be used
in production deployments.
"""

from __future__ import annotations

import asyncio
import logging
import shlex
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

from dolios.sandbox.backend import (
    STATE_DIR_BASE,
    BlueprintPlan,
    CommandResult,
    SandboxBackend,
    SandboxState,
)

if TYPE_CHECKING:
    from dolios.config import DoliosConfig

logger = logging.getLogger(__name__)


class LocalBackend(SandboxBackend):
    """Runs commands directly in the local process — no isolation.

    Intended only for development environments where Docker and OpenShell
    are not available and the user has explicitly opted in via
    ``allow_unsandboxed=True``.
    """

    def __init__(self, config: DoliosConfig) -> None:
        self.config = config
        self.state = SandboxState(sandbox_name=config.sandbox.sandbox_name)
        self._plan: BlueprintPlan | None = None

    def plan(self, dry_run: bool = False) -> BlueprintPlan:
        """PLAN: Produce a minimal plan — no external resources to validate."""
        logger.warning(
            "SECURITY: LocalBackend.plan() — no sandbox isolation will be applied. "
            "Set allow_unsandboxed=True is True in config."
        )

        timestamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
        run_id = f"dolios-local-{timestamp}-{uuid.uuid4().hex[:8]}"

        self._plan = BlueprintPlan(
            run_id=run_id,
            profile="local",
            sandbox={"name": self.config.sandbox.sandbox_name, "image": "", "forward_ports": []},
            inference={
                "provider_type": "openai",
                "provider_name": self.config.inference.default_provider,
                "endpoint": "",
                "model": self.config.inference.default_model,
                "credential_env": "",
            },
            policy_additions={},
            dry_run=dry_run,
        )

        state_dir = STATE_DIR_BASE / run_id
        state_dir.mkdir(parents=True, exist_ok=True)

        from dolios.io import save_json, utc_now_iso

        save_json(
            state_dir / "plan.json",
            {
                "run_id": run_id,
                "profile": "local",
                "backend": "LocalBackend (no isolation)",
                "planned_at": utc_now_iso(),
            },
        )

        return self._plan

    async def apply(self) -> None:
        """APPLY: No-op — local backend has no sandbox to create."""
        if not self._plan:
            self._plan = self.plan()

        logger.warning(
            "SECURITY: LocalBackend.apply() — running WITHOUT sandbox isolation. "
            "All filesystem, network, and process isolation is bypassed."
        )

        self.state.running = True
        self.state.run_id = self._plan.run_id

        from dolios.io import save_json, utc_now_iso

        state_dir = STATE_DIR_BASE / self._plan.run_id
        save_json(state_dir / "state.json", {"running": True, "applied_at": utc_now_iso()})

    async def execute(
        self,
        command: str,
        timeout: float = 120.0,
        workdir: str | None = None,
    ) -> CommandResult:
        """Execute a command directly in the local environment.

        SECURITY: No sandbox isolation. Full OS access.
        """
        if not self.state.running:
            raise RuntimeError("Local backend not started. Call start() first.")

        cwd = workdir or str(Path.cwd())
        logger.debug("LOCAL EXEC cwd=%s cmd=%s", cwd, command)

        try:
            # SEC-C3: Use create_subprocess_exec (not shell=True) to prevent shell
            # injection. shlex.split tokenises the command without invoking a shell.
            args = shlex.split(command)
            proc = await asyncio.create_subprocess_exec(
                *args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd,
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
            return CommandResult(
                exit_code=proc.returncode or 0,
                stdout=stdout.decode() if stdout else "",
                stderr=stderr.decode() if stderr else "",
            )
        except TimeoutError:
            proc.kill()
            return CommandResult(
                exit_code=-1,
                stdout="",
                stderr=f"Command timed out after {timeout}s",
                timed_out=True,
            )

    def status(self) -> dict[str, Any]:
        """STATUS: Report local backend state."""
        return {
            "running": self.state.running,
            "sandbox_name": self.state.sandbox_name,
            "run_id": self.state.run_id,
            "backend": "local (no isolation)",
            "profile": "local",
        }

    async def rollback(self) -> None:
        """ROLLBACK: No-op for local backend."""
        logger.info("LocalBackend.rollback() — nothing to tear down")

        if self.state.run_id:
            from dolios.io import save_json, utc_now_iso

            state_dir = STATE_DIR_BASE / self.state.run_id
            save_json(
                state_dir / "state.json",
                {"running": False, "rolled_back_at": utc_now_iso()},
            )

        self.state.running = False
