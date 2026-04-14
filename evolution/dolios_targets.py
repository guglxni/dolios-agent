"""Compatibility shim for legacy imports.

The canonical evolution vendor seam now lives in:
`dolios.integrations.evolution_vendor`
"""

from dolios.integrations.evolution_vendor import (
    DOLIOS_TARGETS,
    EvolutionTarget,
    TargetType,
    evolve_skill,
    get_all_targets,
    get_dolios_skill_targets,
    validate_evolved_artifact,
)

__all__ = [
    "DOLIOS_TARGETS",
    "EvolutionTarget",
    "TargetType",
    "evolve_skill",
    "get_all_targets",
    "get_dolios_skill_targets",
    "validate_evolved_artifact",
]
