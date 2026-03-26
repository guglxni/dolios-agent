"""AI-DLC Engine — integrates AI-DLC workflow methodology into the agent.

AI-DLC is used at two levels:
1. Building Dolios itself (CLAUDE.md steering)
2. Inside the running agent (context files for methodology-aware task execution)

The engine manages phase detection, context injection, and workflow rules.
"""

from __future__ import annotations

import logging
from enum import Enum
from pathlib import Path

from dolios.config import DoliosConfig

logger = logging.getLogger(__name__)


class AIDLCPhase(Enum):
    """AI-DLC workflow phases."""

    INCEPTION = "inception"      # What & Why — requirements, design, risk
    CONSTRUCTION = "construction"  # How — implementation, testing, validation
    OPERATIONS = "operations"    # Deploy & Monitor — deployment, observability


# Phase detection keywords in user messages
PHASE_SIGNALS: dict[AIDLCPhase, list[str]] = {
    AIDLCPhase.INCEPTION: [
        "what should", "how should", "design", "plan", "requirements",
        "architecture", "should we", "propose", "strategy", "approach",
        "evaluate", "assess", "analyze requirements",
    ],
    AIDLCPhase.CONSTRUCTION: [
        "implement", "build", "code", "write", "create", "fix",
        "refactor", "test", "add feature", "modify", "update",
        "debug", "integrate", "configure",
    ],
    AIDLCPhase.OPERATIONS: [
        "deploy", "monitor", "release", "production", "ci/cd",
        "pipeline", "observability", "metrics", "rollback", "scale",
        "health check", "status",
    ],
}


class AIDLCEngine:
    """Manages AI-DLC workflow integration for methodology-aware task execution."""

    def __init__(self, config: DoliosConfig):
        self.config = config
        self.current_phase: AIDLCPhase = AIDLCPhase.INCEPTION
        self.rules_dir = Path(".aidlc-rule-details")

    def detect_phase(self, user_message: str) -> AIDLCPhase:
        """Detect the appropriate AI-DLC phase from user intent."""
        message_lower = user_message.lower()
        scores: dict[AIDLCPhase, int] = {phase: 0 for phase in AIDLCPhase}

        for phase, signals in PHASE_SIGNALS.items():
            for signal in signals:
                if signal in message_lower:
                    scores[phase] += 1

        best_phase = max(scores, key=lambda p: scores[p])
        if scores[best_phase] > 0:
            self.current_phase = best_phase

        return self.current_phase

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
