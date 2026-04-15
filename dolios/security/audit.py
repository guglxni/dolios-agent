"""Append-only JSON-lines audit logger for Dolios security events.

Every tool call decision (allowed, blocked, unknown) and security-relevant
event is recorded as a single JSON object per line.  Raw argument values
and credentials are never stored — only an HMAC-SHA-256 hash of the
serialised arguments is kept.

File writes are atomic (write-to-tmp, fsync, rename) with fcntl exclusive
locking so concurrent processes can safely append to the same log.

Security notes:
- Rotation happens INSIDE the flock block to prevent TOCTOU races.
- Up to 5 rotation backups are kept (.1.jsonl through .5.jsonl).
- Unknown event types raise ValueError rather than being recorded.
- Log files are created with mode 0600 (owner read/write only).
- Args hash uses HMAC-SHA-256 for tamper evidence within a process session.
"""

from __future__ import annotations

import contextlib
import fcntl
import hashlib
import hmac
import json
import logging
import os
import secrets
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Process-local HMAC key — randomly generated at import time, never persisted.
# Provides tamper-evidence for args hashes within a single process session.
# Cross-process integrity requires a persisted key (out of scope for this layer).
_HMAC_KEY: bytes = secrets.token_bytes(32)

_VALID_EVENTS = frozenset(
    {
        "tool_allowed",
        "tool_blocked",
        "tool_unknown",
        "endpoint_blocked",
        "credential_injected",
        "dlp_blocked",
        "workflow_blocked",
        "injection_blocked",
        "response_dlp_finding",
    }
)

_MAX_ROTATION_BACKUPS = 5


def _args_hash(args: dict[str, Any]) -> str:
    """Return HMAC-SHA-256 hex digest of the canonical JSON representation.

    Uses a process-local key for tamper-evidence within the session.
    SEC-L1: HMAC prevents construction of valid hashes for arbitrary inputs.
    """
    payload = json.dumps(args, sort_keys=True, default=str).encode()
    return hmac.new(_HMAC_KEY, payload, hashlib.sha256).hexdigest()


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
            raise ValueError(
                f"Unknown audit event type {event!r}. "
                f"Valid events: {sorted(_VALID_EVENTS)}"
            )

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
        """Atomically append *line* to the audit log with flock protection.

        Rotation is performed INSIDE the flock to prevent TOCTOU races
        (SEC-H2): two concurrent processes could both see an oversized log
        and both rotate, with the second overwriting the first's backup.
        """
        self._log_path.parent.mkdir(parents=True, exist_ok=True)

        lock_path = self._log_path.with_suffix(".lock")
        with open(lock_path, "w") as lock_fd:
            fcntl.flock(lock_fd, fcntl.LOCK_EX)
            try:
                # Rotation inside lock — prevents TOCTOU race (SEC-H2)
                self._maybe_rotate()

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
                    # Ensure restrictive permissions on newly created log file (SEC-L5)
                    with contextlib.suppress(OSError):
                        os.chmod(str(self._log_path), 0o600)
                except BaseException:
                    with contextlib.suppress(OSError):
                        os.unlink(tmp_path)
                    raise
            finally:
                fcntl.flock(lock_fd, fcntl.LOCK_UN)

    def _maybe_rotate(self) -> None:
        """Rotate the log file if it exceeds max_size_bytes.

        Keeps up to _MAX_ROTATION_BACKUPS numbered backups (.1.jsonl through
        .5.jsonl). On each rotation, existing backups shift up by one:
          .4.jsonl → .5.jsonl, .3.jsonl → .4.jsonl, … .1.jsonl → .2.jsonl
        then the active log becomes .1.jsonl.

        MUST be called inside the flock block (SEC-H2).
        """
        try:
            size = self._log_path.stat().st_size
        except FileNotFoundError:
            return
        if size < self._max_size_bytes:
            return

        # Shift existing backups up (oldest overwritten if at max)
        for i in range(_MAX_ROTATION_BACKUPS - 1, 0, -1):
            src = self._log_path.with_suffix(f".{i}.jsonl")
            dst = self._log_path.with_suffix(f".{i + 1}.jsonl")
            if src.exists():
                with contextlib.suppress(OSError):
                    os.replace(str(src), str(dst))

        rotated = self._log_path.with_suffix(".1.jsonl")
        os.replace(str(self._log_path), str(rotated))
        logger.info("Audit log rotated → %s", rotated)


# Module-level singleton
audit_logger = AuditLogger()
