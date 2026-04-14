"""Constraint Gates — guardrails for the self-evolution pipeline.

Every evolved artifact must pass ALL gates before deployment:
1. Test suite passes 100%
2. Size limits respected
3. Growth limit (max 20% over baseline) — ported from vendor
4. Non-empty check — ported from vendor
5. Structural validation (YAML frontmatter for skills) — ported from vendor
6. Semantic preservation check
7. No security regressions

Aligned with vendor/hermes-agent-self-evolution/evolution/core/constraints.py.
"""

from __future__ import annotations

import logging
import subprocess
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

logger = logging.getLogger(__name__)

# CQ-M4: Module-level constant to avoid rebuilding on every call
_STOPWORDS: frozenset[str] = frozenset(
    {
        "the",
        "and",
        "for",
        "that",
        "this",
        "with",
        "from",
        "are",
        "was",
        "not",
    }
)


@dataclass
class GateResult:
    """Result of a constraint gate check."""

    gate_name: str
    passed: bool
    message: str


def check_tests(project_dir: Path | None = None) -> GateResult:
    """Gate: Full test suite must pass."""
    cwd = str(project_dir) if project_dir else None
    try:
        result = subprocess.run(
            ["uv", "run", "pytest", "-q", "--tb=short"],
            capture_output=True,
            text=True,
            cwd=cwd,
            timeout=300,
        )
        passed = result.returncode == 0
        return GateResult(
            gate_name="test_suite",
            passed=passed,
            message=result.stdout[-200:] if passed else result.stderr[-200:],
        )
    except (FileNotFoundError, subprocess.TimeoutExpired) as e:
        return GateResult(gate_name="test_suite", passed=False, message=str(e))


def check_size_limit(file_path: Path, max_kb: int = 15) -> GateResult:
    """Gate: Evolved file must not exceed size limit."""
    if not file_path.exists():
        return GateResult(
            gate_name="size_limit",
            passed=False,
            message=f"File not found: {file_path}",
        )

    size_kb = file_path.stat().st_size / 1024
    passed = size_kb <= max_kb
    return GateResult(
        gate_name="size_limit",
        passed=passed,
        message=f"{size_kb:.1f}KB / {max_kb}KB limit",
    )


def check_growth_limit(original: str, evolved: str, max_growth: float = 0.2) -> GateResult:
    """Gate: Evolved content must not grow more than max_growth (20%) over baseline.

    Ported from vendor/hermes-agent-self-evolution/evolution/core/constraints.py.
    Prevents verbose drift in evolved artifacts.
    """
    if not original:
        return GateResult(
            gate_name="growth_limit",
            passed=True,
            message="No baseline to compare growth against",
        )

    original_len = len(original)
    evolved_len = len(evolved)
    growth = (evolved_len - original_len) / original_len if original_len > 0 else 0

    passed = growth <= max_growth
    return GateResult(
        gate_name="growth_limit",
        passed=passed,
        message=f"Growth: {growth:.1%} (max: {max_growth:.0%})",
    )


def check_non_empty(content: str) -> GateResult:
    """Gate: Evolved content must not be empty or whitespace-only.

    Ported from vendor/hermes-agent-self-evolution/evolution/core/constraints.py.
    """
    passed = bool(content and content.strip())
    return GateResult(
        gate_name="non_empty",
        passed=passed,
        message="Content is non-empty" if passed else "Content is empty or whitespace-only",
    )


def check_skill_structure(content: str) -> GateResult:
    """Gate: Skill files must have valid YAML frontmatter with name and description.

    Ported from vendor/hermes-agent-self-evolution/evolution/core/constraints.py.
    Only applies to SKILL.md files.
    """
    if not content.startswith("---"):
        # Not a skill file or no frontmatter — skip this gate
        return GateResult(
            gate_name="skill_structure",
            passed=True,
            message="Not a skill file (no frontmatter) — skipped",
        )

    parts = content.split("---", 2)
    if len(parts) < 3:
        return GateResult(
            gate_name="skill_structure",
            passed=False,
            message="Invalid frontmatter: missing closing ---",
        )

    frontmatter = parts[1].strip()
    has_name = any(line.strip().startswith("name:") for line in frontmatter.splitlines())
    has_desc = any(line.strip().startswith("description:") for line in frontmatter.splitlines())

    if not has_name or not has_desc:
        missing = []
        if not has_name:
            missing.append("name")
        if not has_desc:
            missing.append("description")
        return GateResult(
            gate_name="skill_structure",
            passed=False,
            message=f"Frontmatter missing required fields: {missing}",
        )

    return GateResult(
        gate_name="skill_structure",
        passed=True,
        message="Valid skill structure",
    )


def check_semantic_preservation(original: str, evolved: str, threshold: float = 0.7) -> GateResult:
    """Gate: Evolved content must preserve semantic meaning.

    Uses simple heuristic: shared key terms ratio.
    In production, this would use embedding similarity via the inference router.
    """

    def extract_terms(text: str) -> set[str]:
        words = text.lower().split()
        return {w.strip(".,;:!?()[]{}\"'") for w in words if len(w) > 2 and w not in _STOPWORDS}

    original_terms = extract_terms(original)
    evolved_terms = extract_terms(evolved)

    if not original_terms:
        return GateResult(
            gate_name="semantic_preservation",
            passed=True,
            message="No baseline terms to compare",
        )

    overlap = len(original_terms & evolved_terms)
    ratio = overlap / len(original_terms)
    passed = ratio >= threshold

    return GateResult(
        gate_name="semantic_preservation",
        passed=passed,
        message=f"Term overlap: {ratio:.2f} (threshold: {threshold})",
    )


def check_no_security_regression(content: str) -> GateResult:
    """Gate: Evolved content must not introduce security issues.

    Uses both literal substring matching AND regex patterns for robustness.
    """
    import re

    # Literal substring patterns (exact match)
    literal_patterns = [
        "rm -rf /",
        "sudo ",
        "chmod 777",
        "eval(",
        "exec(",
        "__import__(",
        "os.system(",
        "os.popen(",
        "getattr(os",
        "getattr(__builtins__",
        "shell=True",
    ]

    # Regex patterns for more complex detection
    regex_patterns = [
        r"subprocess\.\w+\(.*shell\s*=\s*True",
        r"__import__\s*\(",
        r"getattr\s*\(\s*(?:os|sys|builtins|__builtins__)",
        r"open\s*\(\s*['\"]\/etc\/(?:passwd|shadow)",
        r"base64\.b64decode\s*\(",  # Common obfuscation vector
    ]

    found = []
    for pattern in literal_patterns:
        if pattern in content:
            found.append(f"literal:{pattern}")

    for pattern in regex_patterns:
        if re.search(pattern, content):
            found.append(f"regex:{pattern}")

    # Deduplicate (a literal match might overlap with a regex match)
    found = list(dict.fromkeys(found))

    passed = len(found) == 0
    return GateResult(
        gate_name="security_check",
        passed=passed,
        message=f"Found dangerous patterns: {found}" if found else "No issues",
    )


def run_all_gates(
    file_path: Path,
    original_content: str,
    evolved_content: str,
    max_size_kb: int = 15,
    max_growth: float = 0.2,
    project_dir: Path | None = None,
) -> list[GateResult]:
    """Run all constraint gates and return results.

    Gates are ordered by speed (fast gates first) so we fail fast.
    All gates must pass for the evolved artifact to be accepted.
    """
    return [
        # Fast checks first
        check_non_empty(evolved_content),
        check_size_limit(file_path, max_size_kb),
        check_growth_limit(original_content, evolved_content, max_growth),
        check_skill_structure(evolved_content),
        check_no_security_regression(evolved_content),
        check_semantic_preservation(original_content, evolved_content),
        # Slow check last (runs full test suite)
        check_tests(project_dir),
    ]
