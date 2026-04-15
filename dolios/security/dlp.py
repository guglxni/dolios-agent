"""Outbound DLP (Data Loss Prevention) scanner for tool call arguments.

Scans serialised tool arguments for sensitive data patterns before
dispatch.  Pure-Python regex patterns — no external NLP dependencies.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, cast

if TYPE_CHECKING:
    from dolios.config import DoliosConfig


@dataclass
class DLPFinding:
    """A single sensitive-data match found during scanning."""

    pattern_category: str
    field_path: str
    redacted_excerpt: str


def _redact(value: str) -> str:
    """Show first 4 + ``***`` + last 4 chars (max 8 chars of original)."""
    if len(value) <= 8:
        return value[:4] + "***"
    return value[:4] + "***" + value[-4:]


# (category, compiled regex)
_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    (
        "PRIVATE_KEY",
        re.compile(r"-----BEGIN\s[A-Z\s]*PRIVATE\sKEY-----"),
    ),
    (
        "CREDENTIAL",
        re.compile(
            r"(?:key|token|secret|api|auth)[\s=:\"']{0,10}(?:\w+\s){0,3}([A-Za-z0-9_\-]{20,})",
            re.IGNORECASE,
        ),
    ),
    (
        "ENV_LEAK",
        re.compile(r"(?:KEY|TOKEN|SECRET|PASSWORD|CREDENTIAL)[=]\S+"),
    ),
    (
        "AADHAAR",
        re.compile(r"\b\d{4}\s\d{4}\s\d{4}\b"),
    ),
    (
        "PAN",
        re.compile(r"\b[A-Z]{5}[0-9]{4}[A-Z]\b"),
    ),
    (
        "PII_EMAIL",
        re.compile(r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b"),
    ),
    (
        "PII_PHONE",
        re.compile(r"(?:\+91[\s\-]?)?[6-9]\d{9}\b|\+\d{1,3}\d{6,14}\b"),
    ),
]


class DLPScanner:
    """Scans tool call arguments for sensitive data before dispatch."""

    def __init__(self, config: DoliosConfig) -> None:
        self._enabled = config.dlp.enabled

    def is_enabled(self) -> bool:
        return self._enabled

    def scan(
        self,
        tool_name: str,
        args: dict[str, Any],
        allowed_types: list[str] | None = None,
    ) -> tuple[bool, list[DLPFinding]]:
        """Return ``(True, [])`` if clean, ``(False, findings)`` otherwise."""
        if not self._enabled:
            return True, []

        allowed = set(allowed_types or [])
        findings: list[DLPFinding] = []
        self._scan_value(args, "", findings, allowed)

        if findings:
            return False, findings
        return True, []

    def _scan_value(
        self,
        value: Any,
        path: str,
        findings: list[DLPFinding],
        allowed: set[str],
    ) -> None:
        if isinstance(value, str):
            self._scan_string(value, path, findings, allowed)
        elif isinstance(value, dict):
            for k, v in cast("dict[str, Any]", value).items():
                child: str = f"{path}.{k}" if path else k
                self._scan_value(v, child, findings, allowed)
        elif isinstance(value, list):
            for i, item in enumerate(cast("list[Any]", value)):
                self._scan_value(item, f"{path}[{i}]", findings, allowed)

    def _scan_string(
        self,
        text: str,
        path: str,
        findings: list[DLPFinding],
        allowed: set[str],
    ) -> None:
        for category, pattern in _PATTERNS:
            if category in allowed:
                continue
            match = pattern.search(text)
            if match:
                findings.append(
                    DLPFinding(
                        pattern_category=category,
                        field_path=path,
                        redacted_excerpt=_redact(match.group(0)),
                    )
                )
