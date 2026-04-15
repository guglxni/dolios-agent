"""NemoClaw Terminal Backend for Hermes Agent.

Adds NemoClaw as a terminal execution environment alongside Hermes Agent's
existing backends (local, docker, ssh, daytona, singularity, modal).

This module is a thin adapter that delegates all implementation to the
``dolios.sandbox`` package, which provides the typed ``SandboxBackend`` ABC
and the concrete OpenShell, Docker, and Local backends.

The ``NemoClawBackend`` class is kept here because Hermes Agent discovers
terminal backends from the ``environments/`` directory.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from dolios.sandbox.backend import (
    BlueprintPlan,
    CommandResult,
    SandboxState,
    create_backend,
)

if TYPE_CHECKING:
    from dolios.config import DoliosConfig
    from dolios.sandbox.backend import SandboxBackend

logger = logging.getLogger(__name__)


class NemoClawBackend:
    """NemoClaw terminal backend — delegates to dolios.sandbox.create_backend().

    Implements the plan/apply/status/rollback lifecycle by selecting the most
    isolated backend available (OpenShell > Docker > Local).
    """

    def __init__(self, config: DoliosConfig):
        self.config = config
        self._backend: SandboxBackend = create_backend(config)

    # -----------------------------------------------------------------------
    # Passthrough properties — expose SandboxState for callers that inspect it
    # -----------------------------------------------------------------------

    @property
    def state(self) -> SandboxState:
        backend = self._backend
        if hasattr(backend, "state"):
            return backend.state  # type: ignore[attr-defined]
        return SandboxState(sandbox_name=self.config.sandbox.sandbox_name)

    # -----------------------------------------------------------------------
    # Lifecycle — delegate to backend
    # -----------------------------------------------------------------------

    def plan(self, dry_run: bool = False) -> BlueprintPlan:
        """PLAN: Validate blueprint and resolve deployment plan."""
        return self._backend.plan(dry_run=dry_run)

    async def apply(self) -> None:
        """APPLY: Create and configure the sandbox."""
        await self._backend.apply()

    async def start(self) -> None:
        """Bootstrap the sandbox (plan + apply)."""
        await self._backend.start()

    async def execute(
        self,
        command: str,
        timeout: float = 120.0,
        workdir: str | None = None,
    ) -> CommandResult:
        """Execute a command inside the sandbox."""
        return await self._backend.execute(command=command, timeout=timeout, workdir=workdir)

    def status(self) -> dict[str, Any]:
        """STATUS: Report current sandbox state."""
        return self._backend.status()

    async def rollback(self) -> None:
        """ROLLBACK: Stop and remove the sandbox."""
        await self._backend.rollback()

    async def stop(self) -> None:
        """Gracefully stop the sandbox."""
        await self._backend.stop()
