"""Composed Dolios runtime built from Hermes, NemoClaw, and evolution adapters."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from dolios.integrations.evolution_adapter import EvolutionRuntimeAdapter
from dolios.integrations.hermes_adapter import HermesRuntimeAdapter
from dolios.integrations.sandbox_adapter import SandboxRuntimeAdapter

if TYPE_CHECKING:
    from collections.abc import Callable

    from dolios.config import DoliosConfig
    from dolios.inference_router import InferenceRoute


class DoliosFusionRuntime:
    """Dolios-owned composed runtime around the three upstream stacks."""

    def __init__(self, config: DoliosConfig):
        self.config = config
        self.hermes = HermesRuntimeAdapter()
        self.evolution = EvolutionRuntimeAdapter(config)
        self.sandbox = SandboxRuntimeAdapter(config) if config.sandbox.enabled else None

    async def start_sandbox(self) -> None:
        if self.sandbox:
            await self.sandbox.start()

    async def stop_sandbox(self) -> None:
        if self.sandbox:
            await self.sandbox.stop()

    def create_agent(
        self,
        route: InferenceRoute,
        max_iterations: int = 90,
        policy_guard: Callable[[str, dict[str, Any]], tuple[bool, str]] | None = None,
    ) -> Any:
        return self.hermes.create_agent(
            base_url=route.base_url,
            api_key=route.api_key,
            model=route.model,
            policy_guard=policy_guard,
            max_iterations=max_iterations,
            platform="cli",
            skip_context_files=False,
            skip_memory=False,
        )

    def start_trace(self, trace_id: str, session_id: str, task: str) -> None:
        self.evolution.start_trace(trace_id=trace_id, session_id=session_id, task=task)

    def end_trace(self, trace_id: str, outcome: str = "completed") -> None:
        self.evolution.end_trace(trace_id=trace_id, outcome=outcome)

    def compatibility_snapshot(self) -> dict[str, Any]:
        return {
            "hermes": self.hermes.compatibility_snapshot(),
            "evolution": self.evolution.compatibility_snapshot(),
            "sandbox": {"enabled": self.sandbox is not None},
        }
