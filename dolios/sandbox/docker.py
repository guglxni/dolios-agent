"""Docker sandbox backend — container isolation fallback.

Used when OpenShell is not available. Provides container-level isolation via:
- Read-only root filesystem (--read-only)
- Dropped Linux capabilities (--cap-drop ALL)
- No privilege escalation (--security-opt no-new-privileges:true)
- Tmpfs for /tmp (--tmpfs /tmp:size=512M)

API keys are passed via a temp env-file (mode 0600), never via -e CLI args
which are visible in ``ps aux`` and ``docker inspect``.
"""

from __future__ import annotations

import asyncio
import logging
import os
import subprocess
import tempfile
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
) -> subprocess.CompletedProcess[str]:
    """Run a command safely — never uses shell=True."""
    logger.debug("Docker: %s", " ".join(args))
    return subprocess.run(
        args,
        capture_output=True,
        text=True,
        check=check,
        timeout=timeout,
    )


class DockerBackend(BlueprintSandboxBackend):
    """Sandbox backend that delegates to Docker.

    Used as fallback when OpenShell is not installed.
    """

    def __init__(self, config: DoliosConfig) -> None:
        super().__init__(config)

    async def apply(self) -> None:
        """APPLY: Start a hardened Docker container."""
        if not self._plan:
            self._plan = self.plan()

        if self._plan.dry_run:
            logger.info("Dry run — no changes applied")
            return

        sandbox = self._plan.sandbox
        inference = self._plan.inference
        credential_env = inference.get("credential_env", "")

        port_args: list[str] = []
        for port in sandbox.get("forward_ports", []):
            port_args.extend(["-p", f"127.0.0.1:{port}:{port}"])

        env_lines = [
            f"DOLIOS_INFERENCE_PROVIDER={self.config.inference.default_provider}",
            f"DOLIOS_INFERENCE_MODEL={inference.get('model', '')}",
        ]
        if credential_env and os.environ.get(credential_env):
            env_lines.append(f"{credential_env}={os.environ[credential_env]}")

        env_file_path: str | None = None
        try:
            fd, env_file_path = tempfile.mkstemp(prefix="dolios-env-", suffix=".env")
            os.chmod(env_file_path, 0o600)
            with os.fdopen(fd, "w") as f:
                f.write("\n".join(env_lines) + "\n")

            _run_cmd(
                [
                    "docker",
                    "run",
                    "-d",
                    "--name",
                    sandbox["name"],
                    *port_args,
                    "--env-file",
                    env_file_path,
                    "--read-only",
                    "--security-opt",
                    "no-new-privileges:true",
                    "--cap-drop",
                    "ALL",
                    "--tmpfs",
                    "/tmp:size=512M",
                    "-v",
                    f"{self.config.home / 'traces'}:/sandbox/memory/traces",
                    sandbox["image"],
                ],
                timeout=120,
            )
            logger.info("Docker container '%s' started", sandbox["name"])

        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            if getattr(self.config, "allow_unsandboxed", False):
                logger.warning(
                    "SECURITY: Docker fallback failed (%s). Running unsandboxed — "
                    "explicitly permitted via allow_unsandboxed config.",
                    e,
                )
            else:
                raise RuntimeError(
                    f"Sandbox creation failed and unsandboxed mode is not permitted. "
                    f"Docker error: {e}. "
                    "Set allow_unsandboxed=True in config to run without isolation."
                ) from e
        finally:
            if env_file_path and os.path.exists(env_file_path):
                os.unlink(env_file_path)

        self.state.running = True
        self.state.run_id = self._plan.run_id
        self._save_running_state()
        logger.info("Sandbox '%s' running via Docker", self.state.sandbox_name)

    async def execute(
        self,
        command: str,
        timeout: float = 120.0,
        workdir: str | None = None,
    ) -> CommandResult:
        """Execute a command inside the Docker container.

        SECURITY TRUST BOUNDARY: ``command`` is passed to ``bash -c`` inside
        the container. Container isolation constrains blast radius.
        """
        if not self.state.running:
            raise RuntimeError("Sandbox not running. Call start() first.")

        cwd = workdir or self.state.workspace_path
        logger.debug(
            "SANDBOX EXEC [%s] cwd=%s cmd=%s", self.state.sandbox_name, cwd, command
        )

        sandbox_cmd = [
            "docker",
            "exec",
            "-w",
            cwd,
            self.state.sandbox_name,
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
        """ROLLBACK: Stop and remove the Docker container."""
        if not self.state.running:
            logger.info("No Docker container to rollback")
            return

        logger.info("Rolling back Docker container: %s", self.state.sandbox_name)
        _run_cmd(["docker", "stop", self.state.sandbox_name], check=False)
        _run_cmd(["docker", "rm", self.state.sandbox_name], check=False)

        self._save_stopped_state()
        self.state.running = False
        logger.info("Docker container rolled back")
