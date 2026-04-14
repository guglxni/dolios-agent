"""Tests for dolios.upstream_manager."""

import pytest

from dolios.upstream_manager import UpstreamManager, parse_ls_remote_head


def test_parse_ls_remote_head_valid():
    out = "abc1234567890abcdef1234567890abcdef1234\tHEAD\n"
    sha = parse_ls_remote_head(out)
    assert sha == "abc1234567890abcdef1234567890abcdef1234"


def test_parse_ls_remote_head_invalid():
    with pytest.raises(ValueError):
        parse_ls_remote_head("abc123 refs/heads/main\n")


def test_status_missing_repos(tmp_path):
    manager = UpstreamManager(tmp_path)
    status = manager.status()

    names = {item["name"] for item in status}
    assert names == {"hermes-agent", "nemoclaw", "hermes-agent-self-evolution"}
    assert all(item["exists"] is False for item in status)
    assert all(item["local_sha"] is None for item in status)


def test_sync_writes_manifest(tmp_path, monkeypatch):
    manager = UpstreamManager(tmp_path)

    def fake_sync_repo(self: UpstreamManager, spec):
        repo_path = self.project_dir / spec.path
        repo_path.parent.mkdir(parents=True, exist_ok=True)
        repo_path.mkdir(parents=True, exist_ok=True)
        return {
            "name": spec.name,
            "url": spec.url,
            "path": str(spec.path),
            "previous_sha": None,
            "remote_head": "a" * 40,
            "synced_sha": "a" * 40,
            "changed": True,
        }

    monkeypatch.setattr(UpstreamManager, "sync_repo", fake_sync_repo)

    manifest_path, manifest = manager.sync()
    assert manifest_path == tmp_path / "vendor" / "upstream-manifest.yaml"
    assert manifest_path.exists()
    assert len(manifest["repos"]) == 3


def test_sync_aidlc_rule_details(tmp_path):
    manager = UpstreamManager(tmp_path)

    source_root = tmp_path / "vendor" / "aidlc-workflows" / "aidlc-rules" / "aws-aidlc-rule-details"
    source_file = source_root / "common" / "process-overview.md"
    source_file.parent.mkdir(parents=True, exist_ok=True)
    source_file.write_text("# Process Overview\n")

    version_file = tmp_path / "vendor" / "aidlc-workflows" / "aidlc-rules" / "VERSION"
    version_file.parent.mkdir(parents=True, exist_ok=True)
    version_file.write_text("0.1.7\n")

    metadata = manager.sync_aidlc_rule_details()

    target_file = tmp_path / ".aidlc-rule-details" / "common" / "process-overview.md"
    assert target_file.exists()
    assert target_file.read_text() == "# Process Overview\n"
    assert metadata["version"] == "0.1.7"
    assert metadata["files_synced"] == 1


def test_sync_aidlc_rule_details_requires_repo(tmp_path):
    manager = UpstreamManager(tmp_path)

    with pytest.raises(FileNotFoundError):
        manager.sync_aidlc_rule_details()
