"""Tests for environments.nemoclaw_backend — blueprint lifecycle."""

import json
from unittest.mock import patch

import pytest

from dolios.config import DoliosConfig
from environments.nemoclaw_backend import NemoClawBackend
from environments.nemoclaw_helpers import SandboxState, validate_endpoint_url


def test_sandbox_state_defaults():
    state = SandboxState()
    assert state.running is False
    assert state.workspace_path == "/sandbox/workspace"


def testvalidate_endpoint_url_valid():
    url = validate_endpoint_url("https://api.openai.com/v1")
    assert url == "https://api.openai.com/v1"


def testvalidate_endpoint_url_invalid_scheme():
    with pytest.raises(ValueError, match="Only HTTP"):
        validate_endpoint_url("ftp://evil.com")


def testvalidate_endpoint_url_no_hostname():
    with pytest.raises(ValueError, match="No hostname"):
        validate_endpoint_url("https://")


def test_plan_creates_state(tmp_path, monkeypatch):
    # Point state dir to tmp
    monkeypatch.setattr(
        "environments.nemoclaw_backend.STATE_DIR_BASE",
        tmp_path / "runs",
    )

    config = DoliosConfig()
    backend = NemoClawBackend(config)

    # Use localhost endpoint to avoid DNS resolution issues in tests
    blueprint = {
        "version": "0.1.0",
        "components": {
            "sandbox": {"image": "test:latest", "name": "test", "forward_ports": [8080]},
            "inference": {
                "profiles": {
                    "default": {
                        "provider_type": "openai",
                        "provider_name": "test",
                        "endpoint": "http://localhost:11434/v1",
                        "model": "test-model",
                        "credential_env": "",
                    }
                }
            },
            "policy": {"additions": {}},
        },
    }

    with patch.object(backend, "_load_blueprint", return_value=blueprint):
        plan = backend.plan(dry_run=True)

    assert plan.run_id.startswith("dolios-")
    assert plan.dry_run is True

    # Check state was persisted
    run_dirs = list((tmp_path / "runs").iterdir())
    assert len(run_dirs) == 1
    plan_file = run_dirs[0] / "plan.json"
    assert plan_file.exists()

    with open(plan_file) as f:
        saved = json.load(f)
    assert saved["run_id"] == plan.run_id


def test_validate_endpoint_dns_failure_rejects():
    """SSRF fix: DNS resolution failure must reject (fail-closed)."""
    with pytest.raises(ValueError, match="DNS resolution failed"):
        validate_endpoint_url("https://nonexistent-host-abc123.invalid/v1")


def test_status_no_sandbox():
    config = DoliosConfig()
    backend = NemoClawBackend(config)

    status = backend.status()
    assert status["running"] is False


@pytest.mark.asyncio
async def test_execute_not_running():
    config = DoliosConfig()
    backend = NemoClawBackend(config)

    with pytest.raises(RuntimeError, match="not running"):
        await backend.execute("echo hello")
