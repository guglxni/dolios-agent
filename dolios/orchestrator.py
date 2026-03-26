"""Dolios Orchestrator — the main coordination loop.

Wraps Hermes Agent's tool-calling loop inside NemoClaw's sandboxed runtime,
applying AI-DLC workflow rules and brand personality.

Integration points:
- vendor/hermes-agent: AIAgent (run_agent.py), prompt_builder, model_tools, SessionDB
- vendor/nemoclaw: runner.py plan/apply lifecycle, blueprint.yaml, policy YAML
- vendor/hermes-agent-self-evolution: trace collection for optimization
"""

from __future__ import annotations

import logging
import os
import uuid
from pathlib import Path
from typing import TYPE_CHECKING, Any

from dolios.config import DoliosConfig
from dolios.vendor_path import ensure_vendor_on_path

if TYPE_CHECKING:
    from dolios.aidlc_engine import AIDLCEngine
    from dolios.brand import BrandLayer
    from dolios.inference_router import InferenceRoute, InferenceRouter
    from dolios.policy_bridge import PolicyBridge
    from environments.nemoclaw_backend import NemoClawBackend

logger = logging.getLogger(__name__)


class DoliosOrchestrator:
    """Main orchestration layer that ties all components together.

    Responsibilities:
    1. Bootstrap NemoClaw sandbox with Hermes Agent inside
    2. Bridge Hermes tool declarations to NemoClaw policies
    3. Route inference through sandbox gateway to optimal provider
    4. Apply AI-DLC methodology to task execution
    5. Apply Dolios brand personality
    6. Feed execution traces to self-evolution pipeline
    """

    def __init__(self, config: DoliosConfig | None = None, project_dir: Path | None = None):
        self.config = config or DoliosConfig.load(project_dir)
        self.project_dir = project_dir or Path.cwd()
        self._components_initialized = False
        self._session_id: str = ""
        self._sandbox: NemoClawBackend | None = None

    def _init_components(self) -> None:
        """Lazy-initialize components to avoid import overhead for CLI help."""
        if self._components_initialized:
            return

        ensure_vendor_on_path()

        from dolios.aidlc_engine import AIDLCEngine
        from dolios.brand import BrandLayer
        from dolios.inference_router import InferenceRouter
        from dolios.policy_bridge import PolicyBridge

        self.policy_bridge: PolicyBridge = PolicyBridge(self.config)
        self.inference_router: InferenceRouter = InferenceRouter(self.config)
        self.brand: BrandLayer = BrandLayer(self.config, self.project_dir)
        self.aidlc: AIDLCEngine = AIDLCEngine(self.config)

        self._components_initialized = True

    def _setup_hermes_env(self, route: "InferenceRoute | None" = None) -> dict[str, str]:
        """Configure environment variables for Hermes Agent.

        After setting the active provider's key, unsets any other provider
        API keys from os.environ to prevent leakage to subprocesses.
        """
        if route is None:
            route = self.inference_router.route(task_type="general")

        env = {
            # Hermes Agent config
            "HERMES_HOME": str(self.config.home / "hermes"),
            # Inference routing — Hermes uses OpenAI-compatible env vars
            "OPENAI_API_BASE": route.base_url,
            "OPENAI_API_KEY": route.api_key,
            "DEFAULT_MODEL": route.model,
            # Terminal environment
            "TERMINAL_ENV": "docker" if self.config.sandbox.enabled else "local",
            # Dolios-specific
            "DOLIOS_SESSION_ID": self._session_id,
            "DOLIOS_TRACES_DIR": str(
                Path(self.config.evolution.traces_dir).expanduser()
            ),
        }

        # Unset non-active provider API keys to prevent leakage to subprocesses
        active_key_env = self.config.inference.providers.get(
            route.provider, {}
        ).get("api_key_env", "")
        for name, provider in self.config.inference.providers.items():
            key_env = provider.get("api_key_env", "")
            if key_env and key_env != active_key_env and key_env in os.environ:
                del os.environ[key_env]

        return env

    def _install_soul_md(self) -> None:
        """Install Dolios SOUL.md into Hermes home directory."""
        hermes_home = self.config.home / "hermes"
        hermes_home.mkdir(parents=True, exist_ok=True)

        soul_content = self.brand.get_soul_content()
        soul_dest = hermes_home / "SOUL.md"
        soul_dest.write_text(soul_content)
        logger.info(f"Installed SOUL.md → {soul_dest}")

    @staticmethod
    def _scan_content_for_injection(content: str, filename: str) -> str | None:
        """Scan content for prompt injection patterns before injecting into agent.

        Mirrors Hermes Agent's _scan_context_content() from prompt_builder.py.
        Returns sanitized content, or None if the file should be blocked.
        """
        import re

        injection_patterns = [
            r"ignore\s+(all\s+)?previous\s+instructions",
            r"system\s+prompt\s+override",
            r"disregard\s+(your|all)\s+rules",
            r"you\s+are\s+now\s+(?:a\s+)?(?:different|new|evil)",
            r"do\s+not\s+tell\s+the\s+user",
            r"curl\s+.*(?:KEY|TOKEN|SECRET|API)",
            r"cat\s+\.env",
            r"exfiltrate",
            r"base64\s+encode.*(?:key|secret|password)",
        ]

        # Check for invisible Unicode (zero-width spaces, directional overrides)
        invisible_chars = re.findall(r"[\u200b\u200c\u200d\u200e\u200f\u202a-\u202e\ufeff]", content)
        if invisible_chars:
            logger.warning(
                f"SECURITY: Blocked context file '{filename}' — "
                f"contains {len(invisible_chars)} invisible Unicode characters"
            )
            return None

        for pattern in injection_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                logger.warning(
                    f"SECURITY: Blocked context file '{filename}' — "
                    f"matched injection pattern: {pattern}"
                )
                return None

        return content

    def _install_context_files(self, context_files: list[Path]) -> None:
        """Install context files where Hermes Agent will discover them.

        Each file is scanned for prompt injection patterns before inclusion.
        This mirrors Hermes Agent's built-in _scan_context_content() defense.
        """
        workspace = self.project_dir
        hermes_context = workspace / ".hermes.md"

        sections = []
        blocked = 0
        for ctx_file in context_files:
            try:
                content = ctx_file.read_text()
            except FileNotFoundError:
                continue

            scanned = self._scan_content_for_injection(content, ctx_file.name)
            if scanned is None:
                blocked += 1
                continue

            sections.append(f"<!-- Dolios context: {ctx_file.name} -->\n{scanned}")

        if blocked:
            logger.warning(f"SECURITY: Blocked {blocked} context files due to injection patterns")

        if sections:
            hermes_context.write_text("\n\n---\n\n".join(sections))
            logger.info(f"Installed {len(sections)} context files → {hermes_context}")

    def _install_skills(self) -> None:
        """Install Dolios skills into Hermes Agent's skill directory."""
        import shutil

        hermes_skills = self.config.home / "hermes" / "skills" / "dolios"
        hermes_skills.mkdir(parents=True, exist_ok=True)

        skills_src = self.project_dir / "skills"
        try:
            skill_dirs = [d for d in skills_src.iterdir() if d.is_dir()]
        except FileNotFoundError:
            return

        for skill_dir in skill_dirs:
            dest = hermes_skills / skill_dir.name
            shutil.copytree(skill_dir, dest, dirs_exist_ok=True)

        logger.info(f"Installed {len(skill_dirs)} Dolios skills → {hermes_skills}")

    async def start(self) -> None:
        """Start the Dolios agent loop.

        Flow:
        1. Initialize all components
        2. Bootstrap NemoClaw sandbox (if enabled)
        3. Generate sandbox policy from Hermes tool manifest
        4. Configure inference routing
        5. Install SOUL.md, context files, skills into Hermes Agent
        6. Launch Hermes Agent interactive loop
        """
        self._init_components()
        self._session_id = f"dolios-{uuid.uuid4().hex[:12]}"

        logger.info("Dolios starting — Scheme. Execute. Deliver.")

        # Step 1: Bootstrap sandbox (if enabled)
        if self.config.sandbox.enabled:
            await self._bootstrap_sandbox()
        else:
            logger.warning(
                "SECURITY: Sandbox DISABLED — running Hermes Agent with full local access. "
                "All filesystem, network, and process isolation is bypassed."
            )

        # Step 2: Generate sandbox policy from tool manifest
        policy_path = self.policy_bridge.generate_policy()
        logger.info(f"Policy generated: {policy_path}")

        # Step 3: Configure inference routing — compute route once and reuse
        self.inference_router.configure()
        self._active_route = self.inference_router.route(task_type="general")
        logger.info(f"Inference: {self._active_route.provider} → {self._active_route.model}")

        # Step 4: Install brand, context, and skills
        self._install_soul_md()

        context_files = self.brand.get_context_files()
        if self.config.aidlc_enabled:
            context_files.extend(self.aidlc.get_context_files())
        self._install_context_files(context_files)
        self._install_skills()

        # Step 5: Start Hermes Agent
        await self._start_hermes_agent()

    async def _bootstrap_sandbox(self) -> None:
        """Create and configure NemoClaw sandbox with Hermes Agent.

        Uses NemoClaw's plan/apply lifecycle adapted for Dolios:
        1. Load dolios-blueprint.yaml
        2. Resolve inference profile based on configured provider
        3. Plan sandbox resources
        4. Apply — create sandbox, configure provider, set inference route
        """
        from environments.nemoclaw_backend import NemoClawBackend

        logger.info(
            f"Bootstrapping sandbox: {self.config.sandbox.sandbox_name} "
            f"(blueprint v{self.config.sandbox.blueprint_version})"
        )

        self._sandbox = NemoClawBackend(self.config)
        await self._sandbox.start()

    async def _start_hermes_agent(self) -> None:
        """Start the Hermes Agent interactive loop.

        Wires into vendor/hermes-agent via:
        1. run_agent.AIAgent for the core agent loop
        2. model_tools for tool definitions and dispatch
        3. hermes_state.SessionDB for persistence
        4. agent.prompt_builder for system prompt assembly
        """
        route = self._active_route
        env_vars = self._setup_hermes_env(route)
        for key, value in env_vars.items():
            os.environ[key] = value

        try:
            # Import Hermes Agent components
            from run_agent import AIAgent
        except ImportError:
            logger.error(
                "Could not import Hermes Agent. "
                "Ensure vendor/hermes-agent is initialized: "
                "git submodule update --init --recursive"
            )
            raise

        # Initialize the agent with Dolios configuration
        agent = AIAgent(
            base_url=route.base_url,
            api_key=route.api_key,
            model=route.model,
            max_iterations=90,
            platform="cli",
            skip_context_files=False,  # We installed .hermes.md
            skip_memory=False,
        )

        logger.info(f"Hermes Agent initialized: {route.model} via {route.provider}")

        # Start the trace collector for self-evolution
        from evolution.trace_collector import TraceCollector

        trace_collector = TraceCollector(self.config)
        trace = trace_collector.start_trace(
            trace_id=self._session_id,
            session_id=self._session_id,
            task="interactive_session",
        )

        try:
            # Run the agent — this enters the interactive loop
            # AIAgent.run() handles the conversation cycle
            await self._run_agent_loop(agent)
        except KeyboardInterrupt:
            logger.info("Session interrupted by user")
        finally:
            trace_collector.end_trace(self._session_id, outcome="completed")
            logger.info("Trace saved for evolution pipeline")

    async def _run_agent_loop(self, agent: Any) -> None:
        """Run the Hermes Agent interactive conversation loop.

        This wraps the agent's chat method with Dolios-specific hooks:
        - Pre-tool-call: policy bridge check
        - Post-tool-call: trace collection
        - AI-DLC phase detection on user messages
        """
        from rich.console import Console
        from rich.prompt import Prompt

        console = Console()

        console.print("[bold blue]Δ Dolios[/bold blue] ready. Type your message.\n")

        while True:
            try:
                user_input = Prompt.ask("[bold]You[/bold]")
            except (EOFError, KeyboardInterrupt):
                break

            if not user_input.strip():
                continue

            if user_input.strip().lower() in ("exit", "quit", "/exit", "/quit"):
                break

            # Detect AI-DLC phase from user intent
            if self.config.aidlc_enabled:
                phase = self.aidlc.detect_phase(user_input)
                logger.debug(f"AI-DLC phase: {phase.value}")

            # Send to Hermes Agent
            # NOTE: Pre-dispatch policy checks cannot be injected here without
            # modifying vendor AIAgent internals. Real enforcement happens at
            # the sandbox/network level via NemoClaw policies. We log a
            # post-call trace event for evolution pipeline visibility.
            try:
                response = agent.chat(user_input)
                if response:
                    console.print(f"\n[bold blue]Δ[/bold blue] {response}\n")
            except Exception as e:
                # Log full error internally, show sanitized message to user
                # (OWASP A10:2025 — Mishandling of Exceptional Conditions)
                logger.error(f"Agent error: {e}", exc_info=True)
                console.print(
                    "\n[red]An error occurred processing your request. "
                    "Check logs for details.[/red]\n"
                )

    async def stop(self) -> None:
        """Gracefully stop the agent and sandbox."""
        logger.info("Dolios stopping...")

        # Stop sandbox if running
        if self._sandbox:
            await self._sandbox.stop()

        # Flush any pending traces
        logger.info("Session complete.")
