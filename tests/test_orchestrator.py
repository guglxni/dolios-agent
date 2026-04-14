"""Tests for dolios.orchestrator — core wiring."""

import sys
from pathlib import Path

from dolios.config import DoliosConfig
from dolios.orchestrator import DoliosOrchestrator
from dolios.vendor_path import VENDOR_HERMES, ensure_vendor_on_path


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


def test_policy_guard_unknown_tool_allowed(monkeypatch):
    config = DoliosConfig()
    orch = DoliosOrchestrator(config, Path.cwd())
    orch._init_components()

    monkeypatch.setattr(orch.policy_bridge, "get_policy_for_tool", lambda _tool: None)

    allowed, reason = orch._policy_guard_tool_call("local_read_file", {})
    assert allowed is True
    assert reason == ""


def test_policy_guard_known_tool_blocked(monkeypatch):
    config = DoliosConfig()
    orch = DoliosOrchestrator(config, Path.cwd())
    orch._init_components()

    monkeypatch.setattr(
        orch.policy_bridge,
        "get_policy_for_tool",
        lambda _tool: {"endpoints": [{"host": "blocked.example.com", "port": 443}]},
    )
    monkeypatch.setattr(orch.policy_bridge, "check_endpoint", lambda _h, _p: False)

    requested = []

    def fake_request(**kwargs):
        requested.append(kwargs)

    monkeypatch.setattr(orch.policy_bridge, "request_endpoint_approval", fake_request)

    allowed, reason = orch._policy_guard_tool_call("web_search", {"query": "x"})

    assert allowed is False
    assert "blocked.example.com:443" in reason
    assert len(requested) == 1


class _CaptureConsole:
    def __init__(self):
        self.messages = []

    def print(self, message):
        self.messages.append(str(message))


def test_handle_aidlc_command_status():
    config = DoliosConfig()
    orch = DoliosOrchestrator(config, Path.cwd())
    orch._init_components()

    console = _CaptureConsole()
    handled = orch._handle_aidlc_command("/aidlc status", console)

    assert handled is True
    assert any("AI-DLC phase" in msg for msg in console.messages)


def test_handle_aidlc_command_approve_pending_transition():
    config = DoliosConfig()
    config.aidlc_require_phase_approval = True
    orch = DoliosOrchestrator(config, Path.cwd())
    orch._init_components()

    # Trigger pending inception -> construction gate.
    orch.aidlc.evaluate_phase_transition("Implement the policy bridge module")

    console = _CaptureConsole()
    handled = orch._handle_aidlc_command("/aidlc approve", console)

    assert handled is True
    assert orch.aidlc.current_phase.value == "construction"
    assert any("phase approved" in msg.lower() for msg in console.messages)


def test_handle_aidlc_command_non_command_passes_through():
    config = DoliosConfig()
    orch = DoliosOrchestrator(config, Path.cwd())
    orch._init_components()

    console = _CaptureConsole()
    handled = orch._handle_aidlc_command("hello", console)

    assert handled is False
