"""Compatibility checks against synced upstream vendor repositories."""

import ast
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
        "steer",
        "switch_model",
        "load_soul_identity",
    }


def _hermes_aiagent_init_params(source: str) -> set[str]:
    """Parse AIAgent.__init__ parameter names from vendor source (no runtime import)."""
    tree = ast.parse(source)
    for node in tree.body:
        if not isinstance(node, ast.ClassDef) or node.name != "AIAgent":
            continue
        for child in node.body:
            if isinstance(child, ast.FunctionDef) and child.name == "__init__":
                return {arg.arg for arg in child.args.args if arg.arg != "self"}
    raise AssertionError("AIAgent.__init__ not found in run_agent.py")


def _hermes_aiagent_method_names(source: str) -> set[str]:
    """Return method names declared on AIAgent in vendor source."""
    tree = ast.parse(source)
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == "AIAgent":
            return {
                child.name
                for child in node.body
                if isinstance(child, ast.FunctionDef)
            }
    raise AssertionError("AIAgent class not found in run_agent.py")


@pytest.mark.skipif(
    not Path("vendor/hermes-agent/run_agent.py").exists(),
    reason="hermes-agent repo not synced",
)
def test_hermes_aiagent_constructor_contract():
    source = Path("vendor/hermes-agent/run_agent.py").read_text()
    params = _hermes_aiagent_init_params(source)
    assert {"base_url", "api_key", "model", "provider", "load_soul_identity"}.issubset(params)


@pytest.mark.skipif(
    not Path("vendor/hermes-agent/run_agent.py").exists(),
    reason="hermes-agent repo not synced",
)
def test_hermes_aiagent_chat_method_present():
    source = Path("vendor/hermes-agent/run_agent.py").read_text()
    methods = _hermes_aiagent_method_names(source)
    assert {"chat", "steer", "switch_model"}.issubset(methods)


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
    assert "validate_ssrf" in content or "SSRF" in content


def test_upstream_manifest_has_version_tags():
    import yaml

    manifest = yaml.safe_load(Path("vendor/upstream-manifest.yaml").read_text())
    repos = {item["name"]: item for item in manifest["repos"]}
    for name in ("hermes-agent", "nemoclaw", "hermes-agent-self-evolution"):
        assert name in repos
        assert repos[name]["synced_sha"]
