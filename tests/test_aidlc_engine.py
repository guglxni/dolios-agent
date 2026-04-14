"""Tests for dolios.aidlc_engine."""

from dolios.aidlc_engine import AIDLCEngine, AIDLCPhase
from dolios.config import DoliosConfig


def test_detect_inception_phase():
    config = DoliosConfig()
    config.aidlc_require_phase_approval = False
    engine = AIDLCEngine(config)

    phase = engine.detect_phase("How should we design the API?")
    assert phase == AIDLCPhase.INCEPTION


def test_detect_construction_phase():
    config = DoliosConfig()
    config.aidlc_require_phase_approval = False
    engine = AIDLCEngine(config)

    phase = engine.detect_phase("Implement the policy bridge module")
    assert phase == AIDLCPhase.CONSTRUCTION


def test_detect_operations_phase():
    config = DoliosConfig()
    config.aidlc_require_phase_approval = False
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


def test_forward_transition_requires_approval_by_default():
    config = DoliosConfig()
    config.aidlc_require_phase_approval = True
    engine = AIDLCEngine(config)

    result = engine.evaluate_phase_transition("Implement the policy bridge module")

    assert result.blocked is True
    assert engine.current_phase == AIDLCPhase.INCEPTION
    assert engine.pending_transition() == (AIDLCPhase.INCEPTION, AIDLCPhase.CONSTRUCTION)


def test_approve_pending_transition_advances_phase():
    config = DoliosConfig()
    config.aidlc_require_phase_approval = True
    engine = AIDLCEngine(config)

    engine.evaluate_phase_transition("Implement the policy bridge module")
    approved = engine.approve_transition()

    assert approved == AIDLCPhase.CONSTRUCTION
    assert engine.current_phase == AIDLCPhase.CONSTRUCTION
    assert engine.pending_transition() is None


def test_direct_jump_to_operations_requires_stepwise_approval():
    config = DoliosConfig()
    config.aidlc_require_phase_approval = True
    engine = AIDLCEngine(config)

    result = engine.evaluate_phase_transition("Deploy to production and monitor metrics")

    assert result.blocked is True
    assert engine.current_phase == AIDLCPhase.INCEPTION
    assert engine.pending_transition() == (AIDLCPhase.INCEPTION, AIDLCPhase.CONSTRUCTION)
