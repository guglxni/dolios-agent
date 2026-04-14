"""Shared I/O utilities for Dolios.

Centralizes YAML/JSON loading, atomic writes, directory creation,
and timestamp formatting to eliminate duplication across modules.
"""

from __future__ import annotations

import json
import os
import tempfile
from contextlib import suppress
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

import yaml

if TYPE_CHECKING:
    from pathlib import Path


def load_yaml(path: Path, default: Any = None) -> Any:
    """Load a YAML file, returning default if the file doesn't exist."""
    try:
        with open(path) as f:
            return yaml.safe_load(f) or default
    except FileNotFoundError:
        return default


def save_yaml(path: Path, data: Any, **kwargs: Any) -> None:
    """Atomically write a YAML file."""
    kwargs.setdefault("default_flow_style", False)
    kwargs.setdefault("sort_keys", False)
    _atomic_write(path, yaml.dump(data, **kwargs))


def load_json(path: Path, default: Any = None) -> Any:
    """Load a JSON file, returning default if the file doesn't exist."""
    try:
        with open(path) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default


def save_json(path: Path, data: Any, indent: int = 2) -> None:
    """Atomically write a JSON file."""
    _atomic_write(path, json.dumps(data, indent=indent, default=str))


def _atomic_write(path: Path, content: str) -> None:
    """Write content atomically: write to temp file, then rename.

    Prevents corruption if the process crashes during write.
    (OWASP A08:2025 — Software or Data Integrity Failures)
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(
        dir=str(path.parent),
        prefix=f".{path.name}.",
        suffix=".tmp",
    )
    try:
        with os.fdopen(fd, "w") as f:
            f.write(content)
        os.replace(tmp_path, str(path))
    except BaseException:
        # Clean up temp file on any error
        with suppress(OSError):
            os.unlink(tmp_path)
        raise


def ensure_dir(path: Path) -> Path:
    """Create directory and parents if needed. Returns the path."""
    path.mkdir(parents=True, exist_ok=True)
    return path


def utc_now_iso() -> str:
    """Return current UTC time as ISO 8601 string."""
    return datetime.now(UTC).isoformat()
