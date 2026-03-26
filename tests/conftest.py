"""Shared test fixtures for the Dolios test suite."""

import pytest

from dolios.config import DoliosConfig
from dolios.policy_bridge import PolicyBridge


@pytest.fixture
def config():
    """Default DoliosConfig for tests."""
    return DoliosConfig()


@pytest.fixture
def bridge(tmp_path, config):
    """PolicyBridge with tmp_path-based policy directories."""
    b = PolicyBridge(config)
    b.policy_dir = tmp_path / "policies"
    b.generated_dir = b.policy_dir / "generated"
    return b
