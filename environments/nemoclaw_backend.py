"""NemoClaw Terminal Backend for Hermes Agent.

Adds NemoClaw as a terminal execution environment alongside Hermes Agent's
existing backends (local, docker, ssh, daytona, singularity, modal).

Implements the NemoClaw blueprint plan/apply/status/rollback lifecycle
adapted from vendor/nemoclaw/nemoclaw-blueprint/orchestrator/runner.py.

All commands execute inside the NemoClaw OpenShell sandbox with:
- Network policy enforcement (egress allowlist)
- Filesystem isolation (Landlock: writable /sandbox/workspace, /tmp)
- Process restrictions (seccomp, no privilege escalation)
- Inference routing through gateway

Helper types (SandboxState, CommandResult, BlueprintPlan) and free functions
live in nemoclaw_helpers.py to keep this file under 400 lines (CQ-M2).
"""

from __future__ import annotations

import asyncio
import logging
import os
import subprocess
import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from dolios.io import load_json, load_yaml, save_json, utc_now_iso
from environments.nemoclaw_helpers import (
    DOLIOS_BLUEPRINT_DIR,
    STATE_DIR_BASE,
    BlueprintPlan,
    CommandResult,
    SandboxState,
    find_openshell,
    run_cmd,
    validate_endpoint_url,
)

if TYPE_CHECKING:
    from dolios.config import DoliosConfig

logger = logging.getLogger(__name__)


class NemoClawBackend:
    """NemoClaw terminal backend — executes commands inside an OpenShell sandbox.

    Implements the plan/apply/status/rollback lifecycle from NemoClaw's
    runner.py, adapted for Dolios (Hermes Agent instead of OpenClaw).
    """

    def __init__(self, config: DoliosConfig):
        self.config = config
        self.state = SandboxState(sandbox_name=config.sandbox.sandbox_name)
        self._openshell = find_openshell()
        self._blueprint: dict[str, Any] = {}
        self._plan: BlueprintPlan | None = None

    def _load_blueprint(self) -> dict[str, Any]:
        """Load the Dolios blueprint.yaml."""
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

    def plan(self, dry_run: bool = False) -> BlueprintPlan:
        """PLAN: Validate blueprint, resolve profile, check prerequisites."""
        logger.info("Planning Dolios sandbox deployment...")
        self._blueprint = self._load_blueprint()
        profile = self._resolve_profile(self._blueprint)
        endpoint = profile.get("endpoint", "")
        if endpoint and "localhost" not in endpoint and "host.docker.internal" not in endpoint:
            validate_endpoint_url(endpoint)

        if not self._openshell:
            logger.warning(
                "OpenShell not found — sandbox will run in Docker fallback mode. "
                "Install OpenShell for full Landlock/seccomp isolation."
            )

        sandbox_config = self._blueprint.get("components", {}).get("sandbox", {})
        policy_additions = (
            self._blueprint.get("components", {}).get("policy", {}).get("additions", {})
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

        logger.info(f"Plan created: {run_id} (profile: {self._plan.profile})")
        return self._plan

    async def apply(self) -> None:
        """APPLY: Create sandbox, configure provider, set inference route."""
        if not self._plan:
            self._plan = self.plan()

        logger.info(f"Applying plan: {self._plan.run_id}")

        if self._plan.dry_run:
            logger.info("Dry run — no changes applied")
            return

        if self._openshell:
            await self._apply_openshell()
        else:
            await self._apply_docker_fallback()

        self.state.running = True
        self.state.run_id = self._plan.run_id

        state_dir = STATE_DIR_BASE / self._plan.run_id
        save_json(
            state_dir / "state.json",
            {
                "running": True,
                "applied_at": utc_now_iso(),
            },
        )

        logger.info(f"Sandbox '{self.state.sandbox_name}' running")

    async def _apply_openshell(self) -> None:
        """Apply via OpenShell CLI (full Landlock/seccomp isolation)."""
        assert self._openshell and self._plan

        run_cmd(
            [
                self._openshell,
                "sandbox",
                "create",
                "--name",
                self._plan.sandbox["name"],
                "--image",
                self._plan.sandbox["image"],
            ]
        )
        logger.info("Sandbox created via OpenShell")

        inference = self._plan.inference
        credential_env = inference.get("credential_env", "")
        api_key = os.environ.get(credential_env, "") if credential_env else ""

        provider_env = os.environ.copy()
        provider_env["DOLIOS_PROVIDER_KEY"] = api_key
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
        logger.info(f"Inference provider configured: {inference.get('provider_name')}")

        run_cmd(
            [
                self._openshell,
                "inference",
                "set",
                "--sandbox",
                self._plan.sandbox["name"],
                "--provider",
                inference.get("provider_name", ""),
                "--model",
                inference.get("model", ""),
            ]
        )
        logger.info("Inference route set")

    async def _apply_docker_fallback(self) -> None:
        """Apply via Docker (when OpenShell is not available).

        API keys are passed via --env-file with a temp file (0600 permissions),
        NOT via -e CLI args which are visible in ``ps aux`` and ``docker inspect``.
        """
        import tempfile

        assert self._plan

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

        env_file = None
        try:
            fd, env_file_path = tempfile.mkstemp(prefix="dolios-env-", suffix=".env")
            env_file = env_file_path
            os.chmod(env_file_path, 0o600)
            with os.fdopen(fd, "w") as f:
                f.write("\n".join(env_lines) + "\n")

            run_cmd(
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
            logger.info(f"Docker container '{sandbox['name']}' started")
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            if getattr(self.config, "allow_unsandboxed", False):
                logger.warning(f"Docker fallback failed: {e}")
                logger.warning(
                    "SECURITY: Running in local mode — no sandbox isolation active. "
                    "This was explicitly permitted via allow_unsandboxed config."
                )
            else:
                raise RuntimeError(
                    f"Sandbox creation failed and unsandboxed mode is not permitted. "
                    f"Docker error: {e}. "
                    f"Set allow_unsandboxed=True in config to run without isolation."
                ) from e
        finally:
            if env_file and os.path.exists(env_file):
                os.unlink(env_file)

    async def start(self) -> None:
        """Bootstrap the NemoClaw sandbox (plan + apply)."""
        self.plan()
        await self.apply()

    async def execute(
        self,
        command: str,
        timeout: float = 120.0,
        workdir: str | None = None,
    ) -> CommandResult:
        """Execute a command inside the sandbox.

        SECURITY TRUST BOUNDARY (SEC-A05-M1): The ``command`` string is passed
        to ``bash -c`` and may contain arbitrary shell metacharacters.  This is
        by design — the agent must be able to run arbitrary commands.  The
        sandbox (OpenShell Landlock/seccomp or Docker --read-only/cap-drop)
        constrains blast radius.  All calls are logged for audit.
        """
        if not self.state.running:
            raise RuntimeError("Sandbox not running. Call start() first.")

        cwd = workdir or self.state.workspace_path
        logger.debug("SANDBOX EXEC [%s] cwd=%s cmd=%s", self.state.sandbox_name, cwd, command)

        if self._openshell:
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
        else:
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

    def status(self) -> dict[str, Any]:
        """STATUS: Report sandbox state."""
        if not self.state.run_id:
            return {"running": False, "message": "No sandbox bootstrapped"}

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

    async def rollback(self) -> None:
        """ROLLBACK: Stop and remove sandbox."""
        if not self.state.running:
            logger.info("No sandbox to rollback")
            return

        logger.info(f"Rolling back sandbox: {self.state.sandbox_name}")

        if self._openshell:
            run_cmd(
                [self._openshell, "sandbox", "stop", self.state.sandbox_name],
                check=False,
            )
            run_cmd(
                [self._openshell, "sandbox", "remove", self.state.sandbox_name],
                check=False,
            )
        else:
            run_cmd(["docker", "stop", self.state.sandbox_name], check=False)
            run_cmd(["docker", "rm", self.state.sandbox_name], check=False)

        if self.state.run_id:
            state_dir = STATE_DIR_BASE / self.state.run_id
            save_json(
                state_dir / "state.json",
                {
                    "running": False,
                    "rolled_back_at": utc_now_iso(),
                },
            )

        self.state.running = False
        logger.info("Sandbox rolled back")

    async def stop(self) -> None:
        """Gracefully stop the sandbox."""
        await self.rollback()
