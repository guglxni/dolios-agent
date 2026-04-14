"""NemoClaw sandbox runtime adapter."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from environments.nemoclaw_backend import NemoClawBackend

if TYPE_CHECKING:
    from dolios.config import DoliosConfig


class SandboxRuntimeAdapter:
    """Adapter around the Dolios NemoClaw backend implementation."""

    def __init__(self, config: DoliosConfig):
        self._backend = NemoClawBackend(config)

    async def start(self) -> None:
        await self._backend.start()

    async def stop(self) -> None:
        await self._backend.stop()

    async def execute(self, command: str, timeout: float = 120.0) -> Any:
        return await self._backend.execute(command=command, timeout=timeout)

    def status(self) -> dict[str, Any]:
        return self._backend.status()
