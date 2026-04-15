"""Append-only JSON-lines audit logger for Dolios security events.

Every tool call decision (allowed, blocked, unknown) and security-relevant
event is recorded as a single JSON object per line.  Raw argument values
and credentials are never stored — only a SHA-256 hash of the serialised
arguments is kept.

File writes are atomic (write-to-tmp, fsync, rename) with fcntl exclusive
locking so concurrent processes can safely append to the same log.
"""

from __future__ import annotations

import contextlib
import fcntl
import hashlib
import json
import logging
import os
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_VALID_EVENTS = frozenset(
    {
        "tool_allowed",
        "tool_blocked",
        "tool_unknown",
        "endpoint_blocked",
        "credential_injected",
        "dlp_blocked",
        "workflow_blocked",
    }
)


def _args_hash(args: dict[str, Any]) -> str:
    """Return SHA-256 hex digest of the canonical JSON representation."""
    payload = json.dumps(args, sort_keys=True, default=str)
    return hashlib.sha256(payload.encode()).hexdigest()


class AuditLogger:
    """Append-only JSON-lines audit logger.

    One module-level singleton (`audit_logger`) is created at import time.
    Additional instances may be created for testing.
    """

    def __init__(self, log_path: Path | None = None, max_size_mb: int = 100) -> None:
        env_path = os.environ.get("DOLIOS_AUDIT_LOG")
        if log_path is not None:
            self._log_path = log_path
        elif env_path:
            self._log_path = Path(env_path)
        else:
            self._log_path = Path.home() / ".dolios" / "audit.jsonl"
        self._max_size_bytes = max_size_mb * 1024 * 1024

    def get_log_path(self) -> Path:
        return self._log_path

    def record(
        self,
        session_id: str,
        event: str,
        tool_name: str,
        args: dict[str, Any],
        policy_decision: str,
        reason: str,
        extra: dict[str, Any] | None = None,
    ) -> None:
        """Append a single audit entry to the log file."""
        if event not in _VALID_EVENTS:
            logger.warning("Audit: unknown event type %r — recording anyway", event)

        entry: dict[str, Any] = {
            "ts": datetime.now(UTC).isoformat(),
            "session_id": session_id,
            "event": event,
            "tool_name": tool_name,
            "args_hash": _args_hash(args),
            "policy_decision": policy_decision,
            "reason": reason,
        }
        if extra:
            entry["extra"] = extra

        line = json.dumps(entry, default=str) + "\n"
        self._append(line)

    def _append(self, line: str) -> None:
        """Atomically append *line* to the audit log with flock protection."""
        self._log_path.parent.mkdir(parents=True, exist_ok=True)

        self._maybe_rotate()

        lock_path = self._log_path.with_suffix(".lock")
        with open(lock_path, "w") as lock_fd:
            fcntl.flock(lock_fd, fcntl.LOCK_EX)
            try:
                # Write to a temp file, fsync, then append-rename.
                # Since we need to *append* (not replace), we read existing
                # content if any, append the new line, then atomically replace.
                # For pure append workloads this is safe because flock serialises
                # all writers.
                fd, tmp_path = tempfile.mkstemp(
                    dir=str(self._log_path.parent),
                    prefix=f".{self._log_path.name}.",
                    suffix=".tmp",
                )
                try:
                    existing = b""
                    if self._log_path.exists():
                        existing = self._log_path.read_bytes()
                    with os.fdopen(fd, "wb") as f:
                        f.write(existing)
                        f.write(line.encode())
                        f.flush()
                        os.fsync(f.fileno())
                    os.replace(tmp_path, str(self._log_path))
                except BaseException:
                    with contextlib.suppress(OSError):
                        os.unlink(tmp_path)
                    raise
            finally:
                fcntl.flock(lock_fd, fcntl.LOCK_UN)

    def _maybe_rotate(self) -> None:
        """Rotate the log file if it exceeds max_size_bytes."""
        try:
            size = self._log_path.stat().st_size
        except FileNotFoundError:
            return
        if size >= self._max_size_bytes:
            rotated = self._log_path.with_suffix(".1.jsonl")
            os.replace(str(self._log_path), str(rotated))
            logger.info("Audit log rotated → %s", rotated)


# Module-level singleton
audit_logger = AuditLogger()
