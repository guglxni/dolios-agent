"""Vendor path management — single source of truth for sys.path manipulation.

All vendor repo paths are resolved relative to the PACKAGE root (Path(__file__)),
NOT relative to the current working directory. This prevents dependency confusion
attacks where a malicious CWD contains a vendor/ directory with trojanized modules.

Security: OWASP A08:2025 (Software or Data Integrity Failures)
"""

from __future__ import annotations

import sys
from pathlib import Path

# Resolve from package root, not CWD
_PACKAGE_ROOT = Path(__file__).resolve().parent.parent

VENDOR_HERMES = _PACKAGE_ROOT / "vendor" / "hermes-agent"
VENDOR_NEMOCLAW = _PACKAGE_ROOT / "vendor" / "nemoclaw" / "nemoclaw-blueprint"
VENDOR_EVOLUTION = _PACKAGE_ROOT / "vendor" / "hermes-agent-self-evolution"

_paths_added = False


def ensure_vendor_on_path() -> None:
    """Add vendor repos to sys.path if not already present.

    All paths are anchored to the Dolios package installation directory,
    preventing CWD-relative path manipulation attacks.
    """
    global _paths_added
    if _paths_added:
        return

    for vendor_path in [VENDOR_HERMES, VENDOR_NEMOCLAW, VENDOR_EVOLUTION]:
        resolved = str(vendor_path)
        if resolved not in sys.path:
            # SEC-A08-L1: Append instead of insert to avoid shadowing stdlib modules
            sys.path.append(resolved)

    _paths_added = True


def vendor_available(name: str) -> bool:
    """Check if a vendor repo directory exists."""
    paths = {
        "hermes-agent": VENDOR_HERMES,
        "nemoclaw": VENDOR_NEMOCLAW,
        "hermes-agent-self-evolution": VENDOR_EVOLUTION,
    }
    return paths.get(name, Path("/nonexistent")).is_dir()
