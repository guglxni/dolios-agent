"""Tests for dolios.config."""

from dolios.config import DoliosConfig, InferenceConfig, SandboxConfig


def test_default_config():
    config = DoliosConfig()
    assert config.sandbox.enabled is True
    assert config.sandbox.sandbox_name == "dolios-default"
    assert config.inference.default_provider == "openrouter"
    assert config.evolution.enabled is True
    assert config.aidlc_enabled is True
    assert config.aidlc_require_phase_approval is False
    assert config.log_level == "INFO"


def test_sandbox_config_defaults():
    config = SandboxConfig()
    assert config.blueprint_version == "0.1.0"
    assert config.policy_file == "policies/dolios-default.yaml"


def test_inference_config_providers():
    config = InferenceConfig()
    assert "nvidia" in config.providers
    assert "openrouter" in config.providers
    assert "nous" in config.providers
    assert "openai" in config.providers
    assert "local" in config.providers


def test_config_env_override(monkeypatch):
    monkeypatch.setenv("DOLIOS_INFERENCE_PROVIDER", "nvidia")
    monkeypatch.setenv("DOLIOS_LOG_LEVEL", "DEBUG")
    monkeypatch.setenv("DOLIOS_AIDLC_REQUIRE_APPROVAL", "false")
    config = DoliosConfig.load()
    assert config.inference.default_provider == "nvidia"
    assert config.aidlc_require_phase_approval is False
    assert config.log_level == "DEBUG"


def test_config_sandbox_disabled(monkeypatch):
    monkeypatch.setenv("DOLIOS_SANDBOX_DISABLED", "1")
    config = DoliosConfig.load()
    assert config.sandbox.enabled is False


def test_config_aidlc_enabled_override(monkeypatch):
    monkeypatch.setenv("DOLIOS_AIDLC_ENABLED", "0")
    config = DoliosConfig.load()
    assert config.aidlc_enabled is False
