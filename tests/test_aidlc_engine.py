"""Tests for dolios.aidlc_engine."""

from dolios.aidlc_engine import AIDLCEngine, AIDLCPhase
from dolios.config import DoliosConfig


def test_detect_inception_phase():
    config = DoliosConfig()
    engine = AIDLCEngine(config)

    phase = engine.detect_phase("How should we design the API?")
    assert phase == AIDLCPhase.INCEPTION


def test_detect_construction_phase():
    config = DoliosConfig()
    engine = AIDLCEngine(config)

    phase = engine.detect_phase("Implement the policy bridge module")
    assert phase == AIDLCPhase.CONSTRUCTION


def test_detect_operations_phase():
    config = DoliosConfig()
    engine = AIDLCEngine(config)

    phase = engine.detect_phase("Deploy to production and monitor metrics")
    assert phase == AIDLCPhase.OPERATIONS


def test_get_phase_prompt():
    config = DoliosConfig()
    engine = AIDLCEngine(config)

    engine.current_phase = AIDLCPhase.INCEPTION
    prompt = engine.get_phase_prompt()
    assert "INCEPTION" in prompt
    assert "requirements" in prompt.lower()

    engine.current_phase = AIDLCPhase.CONSTRUCTION
    prompt = engine.get_phase_prompt()
    assert "CONSTRUCTION" in prompt
    assert "implement" in prompt.lower()


def test_default_phase_is_inception():
    config = DoliosConfig()
    engine = AIDLCEngine(config)
    assert engine.current_phase == AIDLCPhase.INCEPTION
