"""Tests for dolios.policy_bridge — NemoClaw-format policy generation."""

from pathlib import Path

import yaml

from dolios.config import DoliosConfig
from dolios.policy_bridge import PolicyBridge


def test_generate_policy_nemoclaw_format(bridge):
    path = bridge.generate_policy(enabled_tools=["github", "web_search"])
    assert path.exists()

    with open(path) as f:
        policy = yaml.safe_load(f)

    # Should have network_policies (NemoClaw format), not network.allow (legacy)
    assert "network_policies" in policy
    policy_names = list(policy["network_policies"].keys())
    assert "github_tools" in policy_names
    assert "web_search" in policy_names


def test_policy_has_endpoint_format(bridge):
    bridge.generate_policy(enabled_tools=["github"])

    with open(bridge.generated_dir / "dolios-active.yaml") as f:
        policy = yaml.safe_load(f)

    github_policy = policy["network_policies"]["github_tools"]
    endpoints = github_policy["endpoints"]
    assert len(endpoints) >= 1

    # Each endpoint should have NemoClaw fields
    ep = endpoints[0]
    assert "host" in ep
    assert "port" in ep
    assert "protocol" in ep
    assert "enforcement" in ep
    assert "rules" in ep


def test_check_endpoint_allowed(bridge):
    bridge.generate_policy(enabled_tools=["github"])

    assert bridge.check_endpoint("api.github.com", 443) is True
    assert bridge.check_endpoint("evil.example.com", 443) is False


def test_check_endpoint_wildcard(bridge):
    bridge.generate_policy(enabled_tools=["web_search"])

    # www.googleapis.com should be directly matched
    assert bridge.check_endpoint("www.googleapis.com", 443) is True


def test_check_endpoint_no_policy_denies():
    config = DoliosConfig()
    bridge = PolicyBridge(config)
    bridge.generated_dir = Path("/nonexistent")

    # No policy = DENY ALL (fail-closed security)
    assert bridge.check_endpoint("anything.com", 443) is False


def test_request_endpoint_approval(tmp_path):
    config = DoliosConfig()
    config.home = tmp_path
    bridge = PolicyBridge(config)

    bridge.request_endpoint_approval(
        host="new-api.example.com",
        port=443,
        tool_name="test_tool",
        reason="Need access for testing",
    )

    pending_file = tmp_path / "pending_approvals.yaml"
    assert pending_file.exists()

    with open(pending_file) as f:
        pending = yaml.safe_load(f)

    assert len(pending) == 1
    assert pending[0]["host"] == "new-api.example.com"
    assert pending[0]["status"] == "pending"


def test_generate_policy_with_messaging(bridge):
    path = bridge.generate_policy(
        enabled_tools=["github"],
        enabled_messaging=["telegram", "discord"],
    )

    with open(path) as f:
        policy = yaml.safe_load(f)

    policy_names = list(policy["network_policies"].keys())
    assert "telegram_bot" in policy_names
    assert "discord" in policy_names


def test_inference_providers_in_policy(bridge):
    bridge.generate_policy(enabled_tools=[])

    with open(bridge.generated_dir / "dolios-active.yaml") as f:
        policy = yaml.safe_load(f)

    # Should have inference provider policies
    policy_names = list(policy["network_policies"].keys())
    inference_policies = [n for n in policy_names if n.startswith("inference_")]
    assert len(inference_policies) > 0
