"""Tests for per-tool capability manifests in skills/."""

from pathlib import Path

import yaml

from dolios.config import DoliosConfig
from dolios.policy_bridge import PolicyBridge


def test_load_skill_capabilities_parses_all_manifests():
    config = DoliosConfig()
    bridge = PolicyBridge(config)
    caps = bridge.load_skill_capabilities(Path("skills"))
    expected = {
        "sandbox-status",
        "policy-request",
        "model-switch",
        "aidlc-phase",
        "evolution-report",
        "trace-analyze",
    }
    assert expected <= set(caps.keys())


def test_tool_without_manifest_returns_none():
    config = DoliosConfig()
    bridge = PolicyBridge(config)
    bridge.load_skill_capabilities(Path("skills"))
    assert bridge.get_capabilities_for_tool("nonexistent_tool") is None


def test_generate_policy_includes_capability_domains(tmp_path):
    config = DoliosConfig()
    bridge = PolicyBridge(config)
    bridge.policy_dir = tmp_path / "policies"
    bridge.generated_dir = bridge.policy_dir / "generated"

    # Create a skills dir with a tool that has network domains
    skills_dir = tmp_path / "skills" / "net-tool"
    skills_dir.mkdir(parents=True)
    (skills_dir / "capabilities.yaml").write_text(yaml.dump({
        "version": "1.0",
        "tool": "net-tool",
        "network": {"allow_domains": ["api.example.com"]},
        "filesystem": {"read": [], "write": []},
        "description": "test",
    }))

    path = bridge.generate_policy(enabled_tools=[], skills_dir=skills_dir.parent)

    with open(path) as f:
        policy = yaml.safe_load(f)

    np = policy.get("network_policies", {})
    found = any(
        any(ep.get("host") == "api.example.com" for ep in block.get("endpoints", []))
        for block in np.values()
    )
    assert found, "capability domain not found in generated policy"


def test_malformed_capabilities_skipped(tmp_path):
    config = DoliosConfig()
    bridge = PolicyBridge(config)

    skills_dir = tmp_path / "skills" / "broken"
    skills_dir.mkdir(parents=True)
    (skills_dir / "capabilities.yaml").write_text("{{{invalid yaml")

    caps = bridge.load_skill_capabilities(skills_dir.parent)
    assert "broken" not in caps
