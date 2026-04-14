"""AI-DLC Engine — integrates AI-DLC workflow methodology into the agent.

AI-DLC is used at two levels:
1. Building Dolios itself (CLAUDE.md steering)
2. Inside the running agent (context files for methodology-aware task execution)

The engine manages phase detection, gated transitions, context injection,
and workflow rules.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from dolios.config import DoliosConfig

logger = logging.getLogger(__name__)


class AIDLCPhase(Enum):
    """AI-DLC workflow phases."""

    INCEPTION = "inception"  # What & Why — requirements, design, risk
    CONSTRUCTION = "construction"  # How — implementation, testing, validation
    OPERATIONS = "operations"  # Deploy & Monitor — deployment, observability


PHASE_ORDER: dict[AIDLCPhase, int] = {
    AIDLCPhase.INCEPTION: 0,
    AIDLCPhase.CONSTRUCTION: 1,
    AIDLCPhase.OPERATIONS: 2,
}


FORWARD_GATES: set[tuple[AIDLCPhase, AIDLCPhase]] = {
    (AIDLCPhase.INCEPTION, AIDLCPhase.CONSTRUCTION),
    (AIDLCPhase.CONSTRUCTION, AIDLCPhase.OPERATIONS),
}


@dataclass(frozen=True)
class PhaseTransitionResult:
    """Result of evaluating or applying an AI-DLC phase transition."""

    previous_phase: AIDLCPhase
    requested_phase: AIDLCPhase
    active_phase: AIDLCPhase
    blocked: bool
    reason: str = ""

    @property
    def changed(self) -> bool:
        return self.previous_phase != self.active_phase


# Phase detection keywords in user messages
PHASE_SIGNALS: dict[AIDLCPhase, list[str]] = {
    AIDLCPhase.INCEPTION: [
        "what should",
        "how should",
        "design",
        "plan",
        "requirements",
        "architecture",
        "should we",
        "propose",
        "strategy",
        "approach",
        "evaluate",
        "assess",
        "analyze requirements",
    ],
    AIDLCPhase.CONSTRUCTION: [
        "implement",
        "build",
        "code",
        "write",
        "create",
        "fix",
        "refactor",
        "test",
        "add feature",
        "modify",
        "update",
        "debug",
        "integrate",
        "configure",
    ],
    AIDLCPhase.OPERATIONS: [
        "deploy",
        "monitor",
        "release",
        "production",
        "ci/cd",
        "pipeline",
        "observability",
        "metrics",
        "rollback",
        "scale",
        "health check",
        "status",
    ],
}


class AIDLCEngine:
    """Manages AI-DLC workflow integration for methodology-aware task execution."""

    def __init__(self, config: DoliosConfig):
        self.config = config
        self.current_phase: AIDLCPhase = AIDLCPhase.INCEPTION
        self.rules_dir = Path(".aidlc-rule-details")
        self.require_phase_approval = config.aidlc_require_phase_approval
        self._approved_transitions: set[tuple[AIDLCPhase, AIDLCPhase]] = set()
        self._pending_transition: tuple[AIDLCPhase, AIDLCPhase] | None = None

    @staticmethod
    def parse_phase(value: str | AIDLCPhase) -> AIDLCPhase | None:
        """Parse a phase value from enum or case-insensitive string."""
        if isinstance(value, AIDLCPhase):
            return value

        normalized = value.strip().lower()
        for phase in AIDLCPhase:
            if phase.value == normalized:
                return phase
        return None

    @staticmethod
    def _next_phase(phase: AIDLCPhase) -> AIDLCPhase | None:
        if phase == AIDLCPhase.INCEPTION:
            return AIDLCPhase.CONSTRUCTION
        if phase == AIDLCPhase.CONSTRUCTION:
            return AIDLCPhase.OPERATIONS
        return None

    def _detect_requested_phase(self, user_message: str) -> AIDLCPhase:
        """Detect requested phase from message without mutating state."""
        message_lower = user_message.lower()
        scores: dict[AIDLCPhase, int] = {phase: 0 for phase in AIDLCPhase}

        for phase, signals in PHASE_SIGNALS.items():
            for signal in signals:
                if signal in message_lower:
                    scores[phase] += 1

        best_phase = max(scores, key=lambda p: scores[p])
        return best_phase if scores[best_phase] > 0 else self.current_phase

    def evaluate_phase_transition(self, user_message: str) -> PhaseTransitionResult:
        """Evaluate requested phase for a message and apply if permitted."""
        requested = self._detect_requested_phase(user_message)
        return self.transition_to(requested)

    def transition_to(self, requested_phase: AIDLCPhase) -> PhaseTransitionResult:
        """Attempt a transition to the requested phase under gate rules."""
        previous = self.current_phase

        if requested_phase == previous:
            return PhaseTransitionResult(
                previous_phase=previous,
                requested_phase=requested_phase,
                active_phase=self.current_phase,
                blocked=False,
            )

        previous_rank = PHASE_ORDER[previous]
        requested_rank = PHASE_ORDER[requested_phase]

        if not self.require_phase_approval:
            self.current_phase = requested_phase
            self._pending_transition = None
            return PhaseTransitionResult(
                previous_phase=previous,
                requested_phase=requested_phase,
                active_phase=self.current_phase,
                blocked=False,
            )

        if requested_rank > previous_rank:
            if requested_rank - previous_rank > 1:
                next_phase = self._next_phase(previous)
                if next_phase is None:
                    return PhaseTransitionResult(
                        previous_phase=previous,
                        requested_phase=requested_phase,
                        active_phase=self.current_phase,
                        blocked=True,
                        reason=(
                            f"Cannot jump from {previous.value} to {requested_phase.value}; "
                            "advance one phase at a time."
                        ),
                    )

                self._pending_transition = (previous, next_phase)
                return PhaseTransitionResult(
                    previous_phase=previous,
                    requested_phase=requested_phase,
                    active_phase=self.current_phase,
                    blocked=True,
                    reason=(
                        f"Forward transition requires approval: "
                        f"{previous.value} -> {next_phase.value}"
                    ),
                )

            gate = (previous, requested_phase)
            if gate in FORWARD_GATES and gate not in self._approved_transitions:
                self._pending_transition = gate
                return PhaseTransitionResult(
                    previous_phase=previous,
                    requested_phase=requested_phase,
                    active_phase=self.current_phase,
                    blocked=True,
                    reason=(
                        f"Forward transition requires approval: "
                        f"{previous.value} -> {requested_phase.value}"
                    ),
                )

        # Backward transitions are allowed without approval to enable replanning.
        self.current_phase = requested_phase
        self._pending_transition = None
        return PhaseTransitionResult(
            previous_phase=previous,
            requested_phase=requested_phase,
            active_phase=self.current_phase,
            blocked=False,
        )

    def pending_transition(self) -> tuple[AIDLCPhase, AIDLCPhase] | None:
        """Return the currently pending gated transition, if any."""
        return self._pending_transition

    def approve_transition(self, target_phase: str | AIDLCPhase | None = None) -> AIDLCPhase | None:
        """Approve a pending or explicit forward transition and advance phase."""
        if not self.require_phase_approval:
            if target_phase is None:
                return self.current_phase
            parsed = self.parse_phase(target_phase)
            if parsed is None:
                return None
            self.current_phase = parsed
            self._pending_transition = None
            return self.current_phase

        if target_phase is None:
            pending = self._pending_transition
            if pending is None:
                return None

            from_phase, to_phase = pending
            if from_phase != self.current_phase:
                self._pending_transition = None
                return None

            self._approved_transitions.add((from_phase, to_phase))
            self.current_phase = to_phase
            self._pending_transition = None
            return self.current_phase

        parsed_target = self.parse_phase(target_phase)
        if parsed_target is None:
            return None

        if parsed_target == self.current_phase:
            self._pending_transition = None
            return self.current_phase

        current_rank = PHASE_ORDER[self.current_phase]
        target_rank = PHASE_ORDER[parsed_target]

        if target_rank < current_rank:
            self.current_phase = parsed_target
            self._pending_transition = None
            return self.current_phase

        if target_rank - current_rank > 1:
            next_phase = self._next_phase(self.current_phase)
            if next_phase is None:
                return None
            self._pending_transition = (self.current_phase, next_phase)
            return None

        gate = (self.current_phase, parsed_target)
        self._approved_transitions.add(gate)
        self.current_phase = parsed_target
        self._pending_transition = None
        return self.current_phase

    def status(self) -> dict[str, str | bool | None]:
        """Return a serializable snapshot of phase and gate state."""
        pending = self.pending_transition()
        pending_str = None
        if pending:
            pending_str = f"{pending[0].value} -> {pending[1].value}"

        return {
            "current_phase": self.current_phase.value,
            "require_phase_approval": self.require_phase_approval,
            "pending_transition": pending_str,
        }

    def detect_phase(self, user_message: str) -> AIDLCPhase:
        """Detect and apply the appropriate AI-DLC phase from user intent."""
        result = self.evaluate_phase_transition(user_message)
        return result.active_phase

    def get_context_files(self) -> list[Path]:
        """Return AI-DLC context files to inject into the agent."""
        files: list[Path] = []

        # Core workflow rules (from CLAUDE.md)
        claude_md = Path("CLAUDE.md")
        if claude_md.exists():
            files.append(claude_md)

        # Phase-specific rule details
        if self.rules_dir.exists():
            phase_dir = self.rules_dir / self.current_phase.value
            if phase_dir.exists():
                files.extend(sorted(phase_dir.glob("*.md")))

            # Common rules always loaded
            common_dir = self.rules_dir / "common"
            if common_dir.exists():
                files.extend(sorted(common_dir.glob("*.md")))

            # Extensions
            extensions_dir = self.rules_dir / "extensions"
            if extensions_dir.exists():
                for ext_dir in sorted(extensions_dir.iterdir()):
                    if ext_dir.is_dir():
                        files.extend(sorted(ext_dir.glob("*.md")))

        return files

    def get_phase_prompt(self) -> str:
        """Get a phase-appropriate steering prompt for the agent."""
        prompts = {
            AIDLCPhase.INCEPTION: (
                "You are in the INCEPTION phase. Focus on understanding requirements, "
                "validating assumptions, decomposing the problem into units of work, "
                "and identifying risks. Ask clarifying questions. Do not implement yet."
            ),
            AIDLCPhase.CONSTRUCTION: (
                "You are in the CONSTRUCTION phase. Focus on implementation: "
                "write code, tests, and documentation. Follow the design from Inception. "
                "Validate each unit of work before moving to the next."
            ),
            AIDLCPhase.OPERATIONS: (
                "You are in the OPERATIONS phase. Focus on deployment, monitoring, "
                "and production readiness. Verify that all systems are healthy and "
                "that rollback mechanisms are in place."
            ),
        }
        return prompts[self.current_phase]

    def get_security_rules(self) -> list[str]:
        """Load Dolios security extension rules."""
        sec_dir = self.rules_dir / "extensions" / "dolios-security"
        if not sec_dir.exists():
            return []

        rules = []
        for rule_file in sorted(sec_dir.glob("*.md")):
            rules.append(rule_file.read_text())
        return rules
