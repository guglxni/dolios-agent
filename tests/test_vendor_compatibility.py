"""Compatibility checks against synced upstream vendor repositories."""

import inspect
from pathlib import Path

import pytest

from dolios.config import DoliosConfig
from dolios.integrations.evolution_adapter import EvolutionRuntimeAdapter
from dolios.integrations.hermes_adapter import HermesRuntimeAdapter
from dolios.vendor_path import ensure_vendor_on_path


def test_upstream_manifest_exists_after_sync():
    manifest = Path("vendor/upstream-manifest.yaml")
    assert manifest.exists()


@pytest.mark.skipif(
    not Path("vendor/hermes-agent/run_agent.py").exists(),
    reason="hermes-agent repo not synced",
)
def test_hermes_surface_snapshot_keys():
    snapshot = HermesRuntimeAdapter().compatibility_snapshot()
    assert set(snapshot.keys()) == {
        "AIAgent",
        "handle_function_call",
        "build_context_files_prompt",
    }


@pytest.mark.skipif(
    not Path("vendor/hermes-agent/run_agent.py").exists(),
    reason="hermes-agent repo not synced",
)
def test_hermes_aiagent_constructor_contract():
    pytest.importorskip("fire", reason="fire package not installed in this env")
    ensure_vendor_on_path()
    from run_agent import AIAgent

    params = set(inspect.signature(AIAgent.__init__).parameters)
    assert {"base_url", "api_key", "model"}.issubset(params)


@pytest.mark.skipif(
    not Path("vendor/hermes-agent/run_agent.py").exists(),
    reason="hermes-agent repo not synced",
)
def test_hermes_aiagent_chat_method_present():
    pytest.importorskip("fire", reason="fire package not installed in this env")
    ensure_vendor_on_path()
    from run_agent import AIAgent

    assert callable(getattr(AIAgent, "chat", None))


@pytest.mark.skipif(
    not Path("vendor/hermes-agent/model_tools.py").exists(),
    reason="hermes-agent repo not synced",
)
def test_hermes_tool_dispatch_contract():
    ensure_vendor_on_path()
    from model_tools import handle_function_call

    params = set(inspect.signature(handle_function_call).parameters)
    assert {"function_name", "function_args"}.issubset(params)


@pytest.mark.skipif(
    not Path("vendor/hermes-agent/model_tools.py").exists(),
    reason="hermes-agent repo not synced",
)
def test_hermes_tool_dispatch_unknown_tool_behavior():
    ensure_vendor_on_path()
    from model_tools import handle_function_call

    result = handle_function_call("missing_tool_xyz", {})
    assert "Unknown tool" in result


@pytest.mark.skipif(
    not Path("vendor/hermes-agent-self-evolution/evolution").exists(),
    reason="hermes-agent-self-evolution repo not synced",
)
def test_evolution_surface_snapshot_keys():
    snapshot = EvolutionRuntimeAdapter(DoliosConfig()).compatibility_snapshot()
    assert set(snapshot.keys()) == {
        "evolve",
        "ConstraintValidator",
        "EvolutionConfig",
    }


@pytest.mark.skipif(
    not Path("vendor/hermes-agent-self-evolution/evolution").exists(),
    reason="hermes-agent-self-evolution repo not synced",
)
def test_evolution_contract_symbols_present_in_source():
    root = Path("vendor/hermes-agent-self-evolution/evolution")

    evolve_content = (root / "skills" / "evolve_skill.py").read_text()
    constraints_content = (root / "core" / "constraints.py").read_text()
    config_content = (root / "core" / "config.py").read_text()

    assert "def evolve(" in evolve_content
    assert "class ConstraintValidator" in constraints_content
    assert "class EvolutionConfig" in config_content


@pytest.mark.skipif(
    not Path("vendor/nemoclaw/nemoclaw/src/blueprint/runner.ts").exists(),
    reason="nemoclaw repo not synced",
)
def test_nemoclaw_blueprint_runner_exists():
    runner = Path("vendor/nemoclaw/nemoclaw/src/blueprint/runner.ts")
    content = runner.read_text()
    assert "actionPlan" in content
    assert "actionApply" in content
