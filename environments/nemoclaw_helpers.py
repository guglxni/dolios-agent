"""Backward-compatibility re-exports for nemoclaw_helpers.

All types and utilities have moved to authoritative locations:

  SandboxState, CommandResult, BlueprintPlan  →  dolios.sandbox.backend
  run_cmd, find_openshell                     →  dolios.sandbox.openshell / docker
  validate_endpoint_url                       →  dolios.policy.matcher.validate_ssrf

This module re-exports them so existing call sites continue to work without
changes. New code should import from the canonical locations.
"""

from __future__ import annotations

import logging
import shutil
import subprocess

# Re-export data types from canonical location
from dolios.sandbox.backend import (
    DOLIOS_BLUEPRINT_DIR,
    STATE_DIR_BASE,
    BlueprintPlan,
    CommandResult,
    SandboxState,
)

logger = logging.getLogger(__name__)

__all__ = [
    "SandboxState",
    "CommandResult",
    "BlueprintPlan",
    "DOLIOS_BLUEPRINT_DIR",
    "STATE_DIR_BASE",
    "find_openshell",
    "run_cmd",
    "validate_endpoint_url",
]


def find_openshell() -> str | None:
    """Find the OpenShell binary on PATH."""
    return shutil.which("openshell")


def run_cmd(
    args: list[str],
    *,
    check: bool = True,
    capture: bool = True,
    timeout: int = 60,
) -> subprocess.CompletedProcess[str]:
    """Run a command safely — never uses shell=True."""
    logger.debug("run_cmd: %s", " ".join(args))
    return subprocess.run(
        args,
        capture_output=capture,
        text=True,
        check=check,
        timeout=timeout,
    )


def validate_endpoint_url(url: str) -> str:
    """Validate endpoint URL against SSRF rules.

    Delegates to the canonical ``dolios.policy.matcher.validate_ssrf``.
    Kept here for backward compatibility.
    """
    from dolios.policy.matcher import validate_ssrf

    return validate_ssrf(url)
