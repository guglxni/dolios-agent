"""NemoClaw sandbox runtime adapter."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from dolios.sandbox.backend import create_backend

if TYPE_CHECKING:
    from dolios.config import DoliosConfig
    from dolios.sandbox.backend import SandboxBackend


class SandboxRuntimeAdapter:
    """Adapter that wraps the Dolios sandbox backend for the fusion runtime."""

    def __init__(self, config: DoliosConfig):
        self._backend: SandboxBackend = create_backend(config)

    async def start(self) -> None:
        await self._backend.start()

    async def stop(self) -> None:
        await self._backend.stop()

    async def execute(self, command: str, timeout: float = 120.0) -> Any:
        return await self._backend.execute(command=command, timeout=timeout)

    def status(self) -> dict[str, Any]:
        return self._backend.status()
