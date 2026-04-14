"""Tests for HermesRuntimeAdapter policy guard wrapping."""

import logging
import sys
import types

from dolios.integrations.hermes_adapter import HermesRuntimeAdapter


def _install_fake_vendor_modules(monkeypatch):
    class FakeAIAgent:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

    def original_handle(function_name, function_args, *args, **kwargs):
        return f"ok:{function_name}:{function_args}"

    run_agent_mod = types.ModuleType("run_agent")
    run_agent_mod.AIAgent = FakeAIAgent
    run_agent_mod.handle_function_call = original_handle

    model_tools_mod = types.ModuleType("model_tools")
    model_tools_mod.handle_function_call = original_handle

    monkeypatch.setitem(sys.modules, "run_agent", run_agent_mod)
    monkeypatch.setitem(sys.modules, "model_tools", model_tools_mod)
    monkeypatch.setattr(
        "dolios.integrations.hermes_adapter.ensure_vendor_on_path",
        lambda: None,
    )

    return run_agent_mod, model_tools_mod


def test_policy_guard_blocks_tool_call(monkeypatch):
    run_agent_mod, _ = _install_fake_vendor_modules(monkeypatch)
    adapter = HermesRuntimeAdapter()

    adapter.create_agent(
        base_url="https://example.com",
        api_key="key",
        model="model",
        policy_guard=lambda _tool, _args: (False, "blocked by test"),
    )

    result = run_agent_mod.handle_function_call("web_search", {"query": "x"})
    assert "Blocked by Dolios policy guard" in result


def test_policy_guard_allows_and_delegates(monkeypatch):
    _, model_tools_mod = _install_fake_vendor_modules(monkeypatch)
    adapter = HermesRuntimeAdapter()

    adapter.create_agent(
        base_url="https://example.com",
        api_key="key",
        model="model",
        policy_guard=lambda _tool, _args: (True, ""),
    )

    result = model_tools_mod.handle_function_call("github", "{}")
    assert result.startswith("ok:github")


def test_coerce_args_json():
    args = HermesRuntimeAdapter._coerce_args('{"a":1}')
    assert args == {"a": 1}


def test_optional_warning_detection():
    assert HermesRuntimeAdapter._is_optional_tool_import_warning(
        "Could not import tool module tools.web_tools: No module named 'firecrawl'"
    )
    assert HermesRuntimeAdapter._is_optional_tool_import_warning(
        "Could not import tool module tools.image_generation_tool: No module named 'fal_client'"
    )
    assert not HermesRuntimeAdapter._is_optional_tool_import_warning(
        "Could not import tool module tools.other: No module named 'x'"
    )


def test_optional_import_filter_suppresses_known_warning(caplog):
    adapter = HermesRuntimeAdapter()
    logger = logging.getLogger("model_tools")

    with (
        adapter._suppress_optional_tool_import_warnings(),
        caplog.at_level(logging.WARNING, logger="model_tools"),
    ):
        logger.warning("Could not import tool module tools.web_tools: No module named 'firecrawl'")
        logger.warning("Could not import tool module tools.other: missing")

    messages = [record.getMessage() for record in caplog.records]
    assert any("tools.other" in msg for msg in messages)
    assert not any("tools.web_tools" in msg for msg in messages)
