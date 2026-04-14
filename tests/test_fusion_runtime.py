"""Tests for Dolios fused runtime composition."""

from dolios.config import DoliosConfig
from dolios.inference_router import InferenceRoute
from dolios.integrations.fusion_runtime import DoliosFusionRuntime


def test_fusion_runtime_sandbox_toggle():
    config = DoliosConfig()
    config.sandbox.enabled = False
    runtime = DoliosFusionRuntime(config)
    assert runtime.sandbox is None

    config_enabled = DoliosConfig()
    config_enabled.sandbox.enabled = True
    runtime_enabled = DoliosFusionRuntime(config_enabled)
    assert runtime_enabled.sandbox is not None


def test_fusion_runtime_create_agent_delegates(monkeypatch):
    config = DoliosConfig()
    config.sandbox.enabled = False
    runtime = DoliosFusionRuntime(config)

    sentinel = object()

    def fake_create_agent(**_kwargs):
        return sentinel

    monkeypatch.setattr(runtime.hermes, "create_agent", fake_create_agent)

    route = InferenceRoute(
        provider="openrouter",
        model="nous/hermes-3-llama-3.1-405b",
        base_url="https://openrouter.ai/api/v1",
        api_key="test",
        score=1.0,
        reason="test",
    )

    assert runtime.create_agent(route) is sentinel


def test_fusion_runtime_snapshot_shape(monkeypatch):
    config = DoliosConfig()
    config.sandbox.enabled = False
    runtime = DoliosFusionRuntime(config)

    monkeypatch.setattr(runtime.hermes, "compatibility_snapshot", lambda: {"AIAgent": True})
    monkeypatch.setattr(runtime.evolution, "compatibility_snapshot", lambda: {"evolve": True})

    snapshot = runtime.compatibility_snapshot()
    assert snapshot["hermes"]["AIAgent"] is True
    assert snapshot["evolution"]["evolve"] is True
    assert snapshot["sandbox"]["enabled"] is False
