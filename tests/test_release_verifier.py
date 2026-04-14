"""Tests for release verification checks."""

from dolios.config import DoliosConfig
from dolios.io import save_yaml
from dolios.release_verifier import ReleaseCheckResult, ReleaseVerifier


def test_check_upstream_manifest_missing(tmp_path):
    verifier = ReleaseVerifier(DoliosConfig(), tmp_path)
    result = verifier._check_upstream_manifest()
    assert result.passed is False


def test_check_upstream_manifest_passes_with_required_repos(tmp_path):
    manifest = {
        "repos": [
            {"name": "hermes-agent"},
            {"name": "nemoclaw"},
            {"name": "hermes-agent-self-evolution"},
        ]
    }
    save_yaml(tmp_path / "vendor" / "upstream-manifest.yaml", manifest)

    verifier = ReleaseVerifier(DoliosConfig(), tmp_path)
    result = verifier._check_upstream_manifest()
    assert result.passed is True


def test_check_aidlc_sync_metadata_missing(tmp_path):
    verifier = ReleaseVerifier(DoliosConfig(), tmp_path)
    result = verifier._check_aidlc_sync_metadata()
    assert result.passed is False


def test_check_aidlc_sync_metadata_passes(tmp_path):
    save_yaml(
        tmp_path / ".aidlc-rule-details" / "upstream-sync.yaml",
        {
            "source_sha": "a" * 40,
            "files_synced": 12,
        },
    )

    verifier = ReleaseVerifier(DoliosConfig(), tmp_path)
    result = verifier._check_aidlc_sync_metadata()
    assert result.passed is True


def test_run_checks_collects_all_results(monkeypatch, tmp_path):
    verifier = ReleaseVerifier(DoliosConfig(), tmp_path)

    monkeypatch.setattr(
        verifier,
        "_check_upstream_manifest",
        lambda: ReleaseCheckResult("upstream-manifest", True, "ok"),
    )
    monkeypatch.setattr(
        verifier,
        "_check_aidlc_sync_metadata",
        lambda: ReleaseCheckResult("aidlc-sync", True, "ok"),
    )
    monkeypatch.setattr(
        verifier,
        "_check_optional_hermes_tool_dependencies",
        lambda: ReleaseCheckResult("optional-tool-deps", True, "ok"),
    )
    monkeypatch.setattr(
        verifier,
        "_check_fusion_compatibility",
        lambda: ReleaseCheckResult("fusion-compat", False, "missing"),
    )
    monkeypatch.setattr(
        verifier,
        "_check_policy_generation",
        lambda: ReleaseCheckResult("policy-generation", True, "ok"),
    )

    results = verifier.run_checks()
    assert len(results) == 5
    assert ReleaseVerifier.is_ready(results) is False


def test_optional_hermes_tool_dependencies_missing_is_non_blocking(monkeypatch, tmp_path):
    verifier = ReleaseVerifier(DoliosConfig(), tmp_path)

    monkeypatch.setattr(
        "dolios.integrations.hermes_adapter.HermesRuntimeAdapter.optional_dependency_status",
        lambda: {"fal_client": False, "firecrawl": True},
    )

    result = verifier._check_optional_hermes_tool_dependencies()
    assert result.passed is True
    assert "fal_client" in result.details


def test_is_ready_all_pass():
    results = [
        ReleaseCheckResult("a", True, "ok"),
        ReleaseCheckResult("b", True, "ok"),
    ]
    assert ReleaseVerifier.is_ready(results) is True
