"""Self-evolution runtime adapter."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from dolios.integrations.evolution_vendor import (
    evolve_skill,
    get_all_targets,
    validate_evolved_artifact,
)
from dolios.vendor_path import VENDOR_EVOLUTION
from evolution.trace_collector import TraceCollector

if TYPE_CHECKING:
    from pathlib import Path

    from dolios.config import DoliosConfig


class EvolutionRuntimeAdapter:
    """Adapter for trace lifecycle and self-evolution entrypoints."""

    def __init__(self, config: DoliosConfig):
        self._collector = TraceCollector(config)

    def start_trace(self, trace_id: str, session_id: str, task: str) -> None:
        self._collector.start_trace(trace_id=trace_id, session_id=session_id, task=task)

    def end_trace(self, trace_id: str, outcome: str = "completed") -> Path | None:
        return self._collector.end_trace(trace_id=trace_id, outcome=outcome)

    def list_targets(self) -> list[Any]:
        return get_all_targets()

    def evolve_skill(
        self,
        *,
        skill_name: str,
        iterations: int,
        eval_model: str,
        dry_run: bool,
        project_dir: Path,
    ) -> dict[str, Any]:
        return evolve_skill(
            skill_name=skill_name,
            iterations=iterations,
            eval_model=eval_model,
            dry_run=dry_run,
            project_dir=project_dir,
        )

    def validate_evolved_artifact(
        self,
        *,
        file_path: Path,
        original_content: str,
        evolved_content: str,
        project_dir: Path,
    ) -> list[dict[str, Any]]:
        return validate_evolved_artifact(
            file_path=file_path,
            original_content=original_content,
            evolved_content=evolved_content,
            project_dir=project_dir,
        )

    def compatibility_snapshot(self) -> dict[str, bool]:
        """Report whether expected vendor evolution files are available."""
        root = VENDOR_EVOLUTION / "evolution"
        return {
            "evolve": (root / "skills" / "evolve_skill.py").exists(),
            "ConstraintValidator": (root / "core" / "constraints.py").exists(),
            "EvolutionConfig": (root / "core" / "config.py").exists(),
        }
