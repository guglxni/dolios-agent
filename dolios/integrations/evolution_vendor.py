"""Dolios-owned seam for self-evolution vendor integration.

This module centralizes imports and calls into vendor/hermes-agent-self-evolution.
All runtime code should access evolution functionality through Dolios adapters.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class TargetType(StrEnum):
    """Types of evolution targets."""

    SKILL = "skill"
    TOOL_DESC = "tool_desc"
    PROMPT = "prompt"
    POLICY = "policy"
    ROUTING = "routing"


@dataclass
class EvolutionTarget:
    """A target for the self-evolution pipeline."""

    name: str
    description: str
    file_path: Path
    target_type: str
    tier: int
    max_size_kb: int = 15


# SECURITY NOTE: Only non-security-critical files may be auto-evolved.
# Policies, routing code, and sandbox config are excluded and require review.
DOLIOS_TARGETS: list[EvolutionTarget] = [
    EvolutionTarget(
        name="dolios-soul",
        description="Evolve Dolios brand personality for better user experience",
        file_path=Path("brand/SOUL.md"),
        target_type=TargetType.PROMPT,
        tier=3,
        max_size_kb=10,
    ),
    EvolutionTarget(
        name="dolios-aidlc-steering",
        description="Optimize AI-DLC context for better methodology adherence",
        file_path=Path("CLAUDE.md"),
        target_type=TargetType.PROMPT,
        tier=3,
        max_size_kb=20,
    ),
]


def _ensure_evolution_vendor(_project_dir: Path | None = None) -> bool:
    """Add vendor repos to sys.path using the shared vendor_path module."""
    try:
        from dolios.vendor_path import ensure_vendor_on_path

        ensure_vendor_on_path()
    except ImportError:
        # Fallback for standalone contexts
        pass

    try:
        import evolution.skills.skill_module  # noqa: F401

        return True
    except ImportError:
        logger.debug("hermes-agent-self-evolution not importable")
        return False


def get_dolios_skill_targets(skills_dir: Path | None = None) -> list[EvolutionTarget]:
    """Discover Dolios-specific skill targets."""
    skills_dir = skills_dir or Path("skills")
    targets: list[EvolutionTarget] = []

    if not skills_dir.exists():
        return targets

    for skill_dir in sorted(skills_dir.iterdir()):
        if not skill_dir.is_dir():
            continue

        skill_md = skill_dir / "SKILL.md"
        if skill_md.exists():
            targets.append(
                EvolutionTarget(
                    name=f"skill-{skill_dir.name}",
                    description=f"Evolve {skill_dir.name} skill for better task completion",
                    file_path=skill_md,
                    target_type=TargetType.SKILL,
                    tier=1,
                )
            )

    return targets


def get_all_targets() -> list[EvolutionTarget]:
    """Get all evolution targets (Dolios-specific + discovered skills)."""
    return DOLIOS_TARGETS + get_dolios_skill_targets()


def evolve_skill(
    skill_name: str,
    iterations: int = 10,
    eval_source: str = "synthetic",
    dataset_path: str | None = None,
    optimizer_model: str = "openai/gpt-4.1",
    eval_model: str = "openai/gpt-4.1-mini",
    dry_run: bool = False,
    project_dir: Path | None = None,
) -> dict[str, Any]:
    """Run the self-evolution pipeline on a Dolios skill."""
    base = project_dir or Path.cwd()

    if not _ensure_evolution_vendor(base):
        return {
            "error": "hermes-agent-self-evolution not available",
            "hint": "Run: git submodule update --init vendor/hermes-agent-self-evolution",
        }

    import os

    os.environ.setdefault(
        "HERMES_AGENT_REPO",
        str((base / "vendor" / "hermes-agent").resolve()),
    )

    from evolution.skills.evolve_skill import evolve

    skill_path = base / "skills" / skill_name / "SKILL.md"
    if not skill_path.exists():
        hermes_skills = base / "vendor" / "hermes-agent" / "skills"
        from evolution.skills.skill_module import find_skill

        skill_path_found = find_skill(skill_name, hermes_skills)
        if not skill_path_found:
            return {"error": f"Skill '{skill_name}' not found"}

    evolve(
        skill_name=skill_name,
        iterations=iterations,
        eval_source=eval_source,
        dataset_path=dataset_path,
        optimizer_model=optimizer_model,
        eval_model=eval_model,
        hermes_repo=str((base / "vendor" / "hermes-agent").resolve()),
        dry_run=dry_run,
    )

    # CQ-L2: Use project IO helper instead of raw open/json.load
    from dolios.io import load_json

    output_dir = Path("output") / skill_name
    if output_dir.exists():
        runs = sorted(output_dir.iterdir(), reverse=True)
        if runs:
            metrics_file = runs[0] / "metrics.json"
            metrics = load_json(metrics_file)
            if metrics is not None:
                return metrics

    return {"status": "completed", "skill": skill_name}


def validate_evolved_artifact(
    file_path: Path,
    original_content: str,
    evolved_content: str,
    project_dir: Path | None = None,
) -> list[dict[str, Any]]:
    """Validate an evolved artifact using the vendor constraint system.

    Prefers vendor constraints when available, falls back to local gates. (CQ-M3)
    """
    base = project_dir or Path.cwd()

    if not _ensure_evolution_vendor(base):
        # Vendor not available — fall back to local Dolios constraint gates
        from evolution.constraint_gates import run_all_gates

        results = run_all_gates(file_path, original_content, evolved_content)
        return [{"gate": r.gate_name, "passed": r.passed, "message": r.message} for r in results]

    # Vendor available — use the full constraint system
    from evolution.core.config import EvolutionConfig
    from evolution.core.constraints import ConstraintValidator

    config = EvolutionConfig()
    validator = ConstraintValidator(config)

    if "SKILL.md" in str(file_path):
        artifact_type = "skill"
    elif file_path.suffix == ".yaml":
        artifact_type = "policy"
    else:
        artifact_type = "prompt"

    results = validator.validate_all(
        evolved_content,
        artifact_type,
        baseline_text=original_content,
    )

    return [
        {
            "constraint": r.constraint_name,
            "passed": r.passed,
            "message": r.message,
            "details": r.details,
        }
        for r in results
    ]


__all__ = [
    "DOLIOS_TARGETS",
    "EvolutionTarget",
    "TargetType",
    "evolve_skill",
    "get_all_targets",
    "get_dolios_skill_targets",
    "validate_evolved_artifact",
]
