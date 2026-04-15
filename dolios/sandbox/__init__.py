"""Dolios sandbox package — typed SandboxBackend implementations.

Public API:
    SandboxBackend       — abstract base class
    BlueprintSandboxBackend — intermediate base with blueprint plan/status
    OpenShellBackend     — full Landlock/seccomp isolation via openshell CLI
    DockerBackend        — container isolation fallback
    LocalBackend         — no isolation, development-only
    create_backend       — factory: returns best available backend
    SandboxState         — runtime state dataclass
    CommandResult        — command execution result dataclass
    BlueprintPlan        — resolved deployment plan dataclass
"""

from dolios.sandbox.backend import (
    BlueprintPlan,
    BlueprintSandboxBackend,
    CommandResult,
    SandboxBackend,
    SandboxState,
    create_backend,
)
from dolios.sandbox.docker import DockerBackend
from dolios.sandbox.local import LocalBackend
from dolios.sandbox.openshell import OpenShellBackend

__all__ = [
    "SandboxBackend",
    "BlueprintSandboxBackend",
    "OpenShellBackend",
    "DockerBackend",
    "LocalBackend",
    "create_backend",
    "SandboxState",
    "CommandResult",
    "BlueprintPlan",
]
