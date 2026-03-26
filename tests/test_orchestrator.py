"""Tests for dolios.orchestrator — core wiring."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

from dolios.config import DoliosConfig
from dolios.orchestrator import DoliosOrchestrator
from dolios.vendor_path import ensure_vendor_on_path, VENDOR_HERMES


def test_orchestrator_init():
    config = DoliosConfig()
    config.sandbox.enabled = False
    orch = DoliosOrchestrator(config, Path.cwd())

    assert orch.config == config
    assert orch._components_initialized is False


def test_ensure_vendor_on_path():
    ensure_vendor_on_path()

    # Check that vendor paths are in sys.path (anchored to package root, not CWD)
    hermes_path = str(VENDOR_HERMES)
    assert hermes_path in sys.path


def test_init_components():
    config = DoliosConfig()
    orch = DoliosOrchestrator(config, Path.cwd())
    orch._init_components()

    assert orch._components_initialized is True
    assert hasattr(orch, "policy_bridge")
    assert hasattr(orch, "inference_router")
    assert hasattr(orch, "brand")
    assert hasattr(orch, "aidlc")


def test_setup_hermes_env():
    config = DoliosConfig()
    config.sandbox.enabled = False
    orch = DoliosOrchestrator(config, Path.cwd())
    orch._init_components()
    orch._session_id = "test-session"
    orch.inference_router.configure()

    env = orch._setup_hermes_env()

    assert "HERMES_HOME" in env
    assert "OPENAI_API_BASE" in env
    assert "DEFAULT_MODEL" in env
    assert env["DOLIOS_SESSION_ID"] == "test-session"
    assert env["TERMINAL_ENV"] == "local"  # sandbox disabled


def test_install_soul_md(tmp_path):
    config = DoliosConfig()
    config.home = tmp_path
    orch = DoliosOrchestrator(config, Path.cwd())
    orch._init_components()

    orch._install_soul_md()

    soul_file = tmp_path / "hermes" / "SOUL.md"
    assert soul_file.exists()
    content = soul_file.read_text()
    assert "Dolios" in content


def test_install_skills(tmp_path):
    config = DoliosConfig()
    config.home = tmp_path
    orch = DoliosOrchestrator(config, Path.cwd())

    orch._install_skills()

    skills_dir = tmp_path / "hermes" / "skills" / "dolios"
    assert skills_dir.exists()
    # Should have our 6 Dolios skills
    skill_dirs = [d for d in skills_dir.iterdir() if d.is_dir()]
    assert len(skill_dirs) >= 6
