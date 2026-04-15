"""Load NemoClaw policy presets and tier definitions from vendor YAML files.

All preset loading reads from vendor/nemoclaw/nemoclaw-blueprint/policies/
directly, treating those files as the authoritative schema source rather
than reimplementing them as Python dicts.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

VENDOR_POLICIES_DIR = Path("vendor/nemoclaw/nemoclaw-blueprint/policies")
VENDOR_PRESETS_DIR = VENDOR_POLICIES_DIR / "presets"
VENDOR_BASE_POLICY = VENDOR_POLICIES_DIR / "openclaw-sandbox.yaml"
VENDOR_TIERS = VENDOR_POLICIES_DIR / "tiers.yaml"


def load_preset(name: str) -> dict[str, Any] | None:
    """Load a named preset from the vendor presets directory.

    Returns the full preset dict (including 'preset' metadata block and
    'network_policies') or None if the file does not exist.

    Raises ValueError for names that do not match ``[a-zA-Z0-9_-]+``
    to prevent path traversal.
    """
    if not re.match(r"^[a-zA-Z0-9_-]+$", name):
        raise ValueError(
            f"Invalid preset name {name!r} — only alphanumeric, hyphens, underscores allowed"
        )

    preset_path = VENDOR_PRESETS_DIR / f"{name}.yaml"
    if not preset_path.exists():
        return None

    from dolios.io import load_yaml

    return load_yaml(preset_path)


def load_all_presets() -> dict[str, dict[str, Any]]:
    """Load all available vendor presets, keyed by preset name.

    Returns an empty dict if the vendor presets directory does not exist.
    """
    presets: dict[str, dict[str, Any]] = {}

    if not VENDOR_PRESETS_DIR.exists():
        return presets

    from dolios.io import load_yaml

    for yaml_file in sorted(VENDOR_PRESETS_DIR.glob("*.yaml")):
        data = load_yaml(yaml_file)
        if data and "preset" in data:
            preset_name = data["preset"].get("name", yaml_file.stem)
            presets[preset_name] = data

    return presets


def load_tier_definitions() -> list[dict[str, Any]]:
    """Load tier definitions from vendor tiers.yaml.

    Returns a list of tier dicts, each with 'name', 'label',
    'description', and 'presets'. Falls back to a minimal
    three-tier default when the file is not found.
    """
    from dolios.io import load_yaml

    data = load_yaml(VENDOR_TIERS)
    if data and "tiers" in data:
        return data["tiers"]

    return [
        {"name": "restricted", "label": "Restricted", "presets": []},
        {
            "name": "balanced",
            "label": "Balanced",
            "presets": [
                {"name": "npm", "access": "read-write"},
                {"name": "pypi", "access": "read-write"},
                {"name": "huggingface", "access": "read-write"},
                {"name": "brew", "access": "read-write"},
                {"name": "brave", "access": "read-write"},
            ],
        },
        {
            "name": "open",
            "label": "Open",
            "presets": [
                {"name": "npm", "access": "read-write"},
                {"name": "pypi", "access": "read-write"},
                {"name": "huggingface", "access": "read-write"},
                {"name": "brew", "access": "read-write"},
                {"name": "brave", "access": "read-write"},
                {"name": "slack", "access": "read-write"},
                {"name": "discord", "access": "read-write"},
                {"name": "telegram", "access": "read-write"},
                {"name": "jira", "access": "read-write"},
                {"name": "outlook", "access": "read-write"},
            ],
        },
    ]


def load_base_policy() -> dict[str, Any]:
    """Load NemoClaw base sandbox policy (openclaw-sandbox.yaml).

    This is the deny-by-default baseline that all tiers build upon.
    Falls back to a minimal default dict when the vendor file is absent.
    """
    from dolios.io import load_yaml

    data = load_yaml(VENDOR_BASE_POLICY)
    if data is not None:
        return data

    return {
        "version": 1,
        "filesystem_policy": {
            "include_workdir": False,
            "read_only": ["/usr", "/lib", "/proc", "/etc"],
            "read_write": ["/tmp", "/dev/null"],
        },
        "landlock": {"compatibility": "best_effort"},
        "process": {"run_as_user": "sandbox", "run_as_group": "sandbox"},
        "network_policies": {},
    }


def merge_preset_into_policy(policy: dict[str, Any], preset_data: dict[str, Any]) -> None:
    """Merge preset network_policies into the given policy dict (in-place)."""
    if "network_policies" not in policy:
        policy["network_policies"] = {}

    for policy_name, policy_block in preset_data.get("network_policies", {}).items():
        policy["network_policies"][policy_name] = policy_block
