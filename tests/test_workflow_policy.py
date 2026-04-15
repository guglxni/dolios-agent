"""Tests for dolios.security.workflow — DAG tool ordering."""

import pytest
import yaml

from dolios.config import DoliosConfig
from dolios.security.workflow import WorkflowPolicy


def _make_config(tmp_path, policies=None):
    """Helper: build a DoliosConfig pointing at a tmp workflow.yaml."""
    config = DoliosConfig()
    policy_file = tmp_path / "workflow.yaml"
    if policies is not None:
        policy_file.write_text(yaml.dump({"version": "1.0", "policies": policies}))
    config.workflow.policy_file = str(policy_file)
    return config


def test_no_constraints_allows_all(tmp_path):
    wp = WorkflowPolicy(_make_config(tmp_path, policies=[]))
    allowed, reason = wp.check("s1", "any_tool")
    assert allowed is True
    assert reason == ""


def test_predecessor_not_run_blocks(tmp_path):
    wp = WorkflowPolicy(_make_config(tmp_path, policies=[
        {"tool": "deploy", "requires": [{"tool": "test", "status": "success"}]},
    ]))
    allowed, reason = wp.check("s1", "deploy")
    assert allowed is False
    assert "test" in reason


def test_predecessor_succeeded_allows(tmp_path):
    wp = WorkflowPolicy(_make_config(tmp_path, policies=[
        {"tool": "deploy", "requires": [{"tool": "test", "status": "success"}]},
    ]))
    wp.record_outcome("s1", "test", success=True)
    allowed, _ = wp.check("s1", "deploy")
    assert allowed is True


def test_predecessor_failed_blocks_when_success_required(tmp_path):
    wp = WorkflowPolicy(_make_config(tmp_path, policies=[
        {"tool": "deploy", "requires": [{"tool": "test", "status": "success"}]},
    ]))
    wp.record_outcome("s1", "test", success=False)
    allowed, reason = wp.check("s1", "deploy")
    assert allowed is False
    assert "succeeded" in reason


def test_predecessor_ran_allows_when_any_status(tmp_path):
    wp = WorkflowPolicy(_make_config(tmp_path, policies=[
        {"tool": "report", "requires": [{"tool": "test", "status": "any"}]},
    ]))
    wp.record_outcome("s1", "test", success=False)
    allowed, _ = wp.check("s1", "report")
    assert allowed is True


def test_reset_session_clears_state(tmp_path):
    wp = WorkflowPolicy(_make_config(tmp_path, policies=[
        {"tool": "deploy", "requires": [{"tool": "test", "status": "success"}]},
    ]))
    wp.record_outcome("s1", "test", success=True)
    assert wp.check("s1", "deploy")[0] is True

    wp.reset_session("s1")
    assert wp.check("s1", "deploy")[0] is False


def test_missing_yaml_no_constraints(tmp_path):
    wp = WorkflowPolicy(_make_config(tmp_path, policies=None))
    allowed, reason = wp.check("s1", "anything")
    assert allowed is True
    assert reason == ""


def test_circular_dependency_raises(tmp_path):
    with pytest.raises(ValueError, match="Circular dependency"):
        WorkflowPolicy(_make_config(tmp_path, policies=[
            {"tool": "a", "requires": [{"tool": "b", "status": "success"}]},
            {"tool": "b", "requires": [{"tool": "a", "status": "success"}]},
        ]))
