"""Tests for dolios.inference_router."""

from dolios.config import DoliosConfig
from dolios.inference_router import InferenceRouter


def test_router_configure_no_keys(monkeypatch):
    # Clear all API keys
    for key in ["NVIDIA_API_KEY", "OPENROUTER_API_KEY", "NOUS_API_KEY", "OPENAI_API_KEY"]:
        monkeypatch.delenv(key, raising=False)

    config = DoliosConfig()
    router = InferenceRouter(config)
    router.configure()

    # Only "local" should be available (no API key required)
    assert "local" in router._available_providers


def test_router_configure_with_key(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    # Clear others
    for key in ["NVIDIA_API_KEY", "NOUS_API_KEY", "OPENAI_API_KEY"]:
        monkeypatch.delenv(key, raising=False)

    config = DoliosConfig()
    router = InferenceRouter(config)
    router.configure()

    assert "openrouter" in router._available_providers


def test_route_user_preference(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    monkeypatch.setenv("NVIDIA_API_KEY", "test-key")

    config = DoliosConfig()
    router = InferenceRouter(config)
    router.configure()

    route = router.route(preferred_provider="nvidia")
    assert route.provider == "nvidia"
    assert route.reason == "user preference"


def test_route_task_type(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    monkeypatch.setenv("NVIDIA_API_KEY", "test-key")

    config = DoliosConfig()
    router = InferenceRouter(config)
    router.configure()

    route = router.route(task_type="code")
    assert route.provider in router._available_providers


def test_list_providers(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")

    config = DoliosConfig()
    router = InferenceRouter(config)

    providers = router.list_providers()
    assert len(providers) == 5  # nvidia, openrouter, nous, openai, local
    names = [p["name"] for p in providers]
    assert "openrouter" in names
