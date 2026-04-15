"""Tests for dolios.security.audit — append-only audit trail."""

import hashlib
import json
import threading
from pathlib import Path

from dolios.security.audit import AuditLogger, _args_hash


def test_single_record_valid_json(tmp_path: Path) -> None:
    log_path = tmp_path / "audit.jsonl"
    al = AuditLogger(log_path=log_path)

    al.record(
        session_id="test-session",
        event="tool_allowed",
        tool_name="web_search",
        args={"query": "hello"},
        policy_decision="allowed",
        reason="endpoint matched policy",
    )

    lines = log_path.read_text().strip().splitlines()
    assert len(lines) == 1
    entry = json.loads(lines[0])
    assert entry["session_id"] == "test-session"
    assert entry["event"] == "tool_allowed"
    assert entry["tool_name"] == "web_search"
    assert "ts" in entry
    assert "args_hash" in entry
    assert entry["policy_decision"] == "allowed"


def test_args_hash_is_hmac_sha256_deterministic() -> None:
    """_args_hash uses HMAC-SHA-256 (not plain SHA-256) and is deterministic within a process."""
    args = {"z": 1, "a": 2}
    h = _args_hash(args)

    # Must be a valid 64-char SHA-256 hex digest
    assert len(h) == 64
    assert all(c in "0123456789abcdef" for c in h)

    # Must NOT equal plain SHA-256 — verifies HMAC key is in use
    plain = hashlib.sha256(json.dumps(args, sort_keys=True).encode()).hexdigest()
    assert h != plain, "_args_hash must use HMAC, not plain SHA-256"

    # Must be deterministic within the same process (same key)
    assert _args_hash(args) == h


def test_args_hash_never_contains_raw_value(tmp_path: Path) -> None:
    log_path = tmp_path / "audit.jsonl"
    al = AuditLogger(log_path=log_path)

    al.record(
        session_id="s",
        event="tool_allowed",
        tool_name="t",
        args={"api_key": "sk-super-secret-key-12345"},
        policy_decision="allowed",
        reason="ok",
    )

    content = log_path.read_text()
    assert "sk-super-secret-key-12345" not in content


def test_concurrent_writes_no_corruption(tmp_path: Path) -> None:
    log_path = tmp_path / "audit.jsonl"
    al = AuditLogger(log_path=log_path)
    n_threads = 10
    n_records = 5

    def writer(thread_id: int) -> None:
        for i in range(n_records):
            al.record(
                session_id=f"session-{thread_id}",
                event="tool_allowed",
                tool_name=f"tool-{i}",
                args={"i": i},
                policy_decision="allowed",
                reason="test",
            )

    threads = [threading.Thread(target=writer, args=(t,)) for t in range(n_threads)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    lines = log_path.read_text().strip().splitlines()
    assert len(lines) == n_threads * n_records
    for line in lines:
        json.loads(line)  # every line must be valid JSON


def test_rotation_triggers(tmp_path: Path) -> None:
    log_path = tmp_path / "audit.jsonl"
    al = AuditLogger(log_path=log_path, max_size_mb=0)

    # First record — file doesn't exist yet, no rotation
    al.record(
        session_id="s", event="tool_allowed", tool_name="t",
        args={}, policy_decision="allowed", reason="first",
    )
    assert log_path.exists()

    # Second record — file > 0 bytes, triggers rotation
    al.record(
        session_id="s", event="tool_blocked", tool_name="t2",
        args={}, policy_decision="blocked", reason="second",
    )

    rotated = log_path.with_suffix(".1.jsonl")
    assert rotated.exists()


def test_log_path_from_env(tmp_path: Path, monkeypatch: "pytest.MonkeyPatch") -> None:
    custom_path = tmp_path / "custom" / "audit.jsonl"
    monkeypatch.setenv("DOLIOS_AUDIT_LOG", str(custom_path))

    al = AuditLogger()
    assert al.get_log_path() == custom_path
