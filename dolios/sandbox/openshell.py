"""OpenShell sandbox backend — full Landlock/seccomp isolation.

Uses the ``openshell`` CLI to create and manage sandboxes with:
- Landlock LSM filesystem isolation
- seccomp syscall filtering
- NemoClaw network policy enforcement via the gateway
"""

from __future__ import annotations

import asyncio
import logging
import os
import subprocess
from typing import TYPE_CHECKING

from dolios.sandbox.backend import BlueprintSandboxBackend, CommandResult

if TYPE_CHECKING:
    from dolios.config import DoliosConfig

logger = logging.getLogger(__name__)


def _run_cmd(
    args: list[str],
    *,
    check: bool = True,
    timeout: int = 60,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    """Run a command safely — never uses shell=True."""
    logger.debug("OpenShell: %s", " ".join(args))
    return subprocess.run(
        args,
        capture_output=True,
        text=True,
        check=check,
        timeout=timeout,
        env=env,
    )


class OpenShellBackend(BlueprintSandboxBackend):
    """Sandbox backend that delegates to the ``openshell`` CLI.

    Provides full Landlock/seccomp isolation when OpenShell is installed.
    """

    def __init__(self, config: DoliosConfig) -> None:
        import shutil

        super().__init__(config)
        openshell = shutil.which("openshell")
        if not openshell:
            raise RuntimeError("openshell binary not found — cannot use OpenShellBackend")
        self._openshell = openshell

    async def apply(self) -> None:
        """APPLY: Create sandbox, configure provider, set inference route."""
        if not self._plan:
            self._plan = self.plan()

        if self._plan.dry_run:
            logger.info("Dry run — no changes applied")
            return

        sandbox = self._plan.sandbox
        inference = self._plan.inference

        # Create sandbox
        _run_cmd(
            [
                self._openshell,
                "sandbox",
                "create",
                "--name",
                sandbox["name"],
                "--image",
                sandbox["image"],
            ]
        )
        logger.info("Sandbox created via OpenShell: %s", sandbox["name"])

        # Configure inference provider — API key via env, never CLI args
        credential_env = inference.get("credential_env", "")
        api_key = os.environ.get(credential_env, "") if credential_env else ""
        provider_env = {**os.environ, "DOLIOS_PROVIDER_KEY": api_key}

        subprocess.run(
            [
                self._openshell,
                "provider",
                "create",
                "--name",
                inference.get("provider_name", "dolios-inference"),
                "--type",
                inference.get("provider_type", "openai"),
                "--endpoint",
                inference.get("endpoint", ""),
                "--api-key-env",
                "DOLIOS_PROVIDER_KEY",
            ],
            capture_output=True,
            text=True,
            check=True,
            timeout=60,
            env=provider_env,
        )
        logger.info("Inference provider configured: %s", inference.get("provider_name"))

        # Set inference routing
        _run_cmd(
            [
                self._openshell,
                "inference",
                "set",
                "--sandbox",
                sandbox["name"],
                "--provider",
                inference.get("provider_name", ""),
                "--model",
                inference.get("model", ""),
            ]
        )
        logger.info("Inference route set")

        self.state.running = True
        self.state.run_id = self._plan.run_id
        self._save_running_state()
        logger.info("Sandbox '%s' running via OpenShell", self.state.sandbox_name)

    async def execute(
        self,
        command: str,
        timeout: float = 120.0,
        workdir: str | None = None,
    ) -> CommandResult:
        """Execute a command inside the OpenShell sandbox.

        SECURITY TRUST BOUNDARY: ``command`` is passed to ``bash -c`` inside
        the sandbox. The sandbox (Landlock/seccomp) constrains blast radius.
        """
        if not self.state.running:
            raise RuntimeError("Sandbox not running. Call start() first.")

        cwd = workdir or self.state.workspace_path
        logger.debug(
            "SANDBOX EXEC [%s] cwd=%s cmd=%s", self.state.sandbox_name, cwd, command
        )

        sandbox_cmd = [
            self._openshell,
            "exec",
            "--sandbox",
            self.state.sandbox_name,
            "--workdir",
            cwd,
            "--",
            "bash",
            "-c",
            command,
        ]

        try:
            proc = await asyncio.create_subprocess_exec(
                *sandbox_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
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

    async def rollback(self) -> None:
        """ROLLBACK: Stop and remove the OpenShell sandbox."""
        if not self.state.running:
            logger.info("No OpenShell sandbox to rollback")
            return

        logger.info("Rolling back OpenShell sandbox: %s", self.state.sandbox_name)
        _run_cmd([self._openshell, "sandbox", "stop", self.state.sandbox_name], check=False)
        _run_cmd([self._openshell, "sandbox", "remove", self.state.sandbox_name], check=False)

        self._save_stopped_state()
        self.state.running = False
        logger.info("OpenShell sandbox rolled back")
