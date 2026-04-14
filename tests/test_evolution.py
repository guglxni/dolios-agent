"""Tests for evolution modules."""

from evolution.constraint_gates import (
    check_growth_limit,
    check_no_security_regression,
    check_non_empty,
    check_semantic_preservation,
    check_size_limit,
    check_skill_structure,
)
from evolution.dolios_targets import DOLIOS_TARGETS, get_all_targets


def test_dolios_targets_exist():
    assert len(DOLIOS_TARGETS) > 0
    names = [t.name for t in DOLIOS_TARGETS]
    assert "dolios-soul" in names
    assert "dolios-aidlc-steering" in names
    # Security: policies and routing code must NOT be auto-evolvable
    assert "dolios-policy-default" not in names
    assert "dolios-inference-routing" not in names


def test_get_all_targets():
    targets = get_all_targets()
    # Should include at least the base Dolios targets
    assert len(targets) >= len(DOLIOS_TARGETS)


def test_size_limit_pass(tmp_path):
    f = tmp_path / "small.md"
    f.write_text("x" * 100)
    result = check_size_limit(f, max_kb=15)
    assert result.passed is True


def test_size_limit_fail(tmp_path):
    f = tmp_path / "big.md"
    f.write_text("x" * 20000)
    result = check_size_limit(f, max_kb=15)
    assert result.passed is False


def test_semantic_preservation_pass():
    original = "This skill helps with code review by analyzing pull requests"
    evolved = "This skill assists with code review by examining pull requests and diffs"
    result = check_semantic_preservation(original, evolved)
    assert result.passed is True


def test_semantic_preservation_fail():
    original = "This skill helps with code review by analyzing pull requests"
    evolved = "This recipe makes chocolate cake with frosting and sprinkles"
    result = check_semantic_preservation(original, evolved)
    assert result.passed is False


def test_security_check_pass():
    result = check_no_security_regression("print('hello world')")
    assert result.passed is True


def test_security_check_fail():
    result = check_no_security_regression("os.system('rm -rf /')")
    assert result.passed is False


def test_security_check_regex_catches_shell_true():
    """Verify regex patterns catch subprocess with shell=True."""
    result = check_no_security_regression("subprocess.call(cmd, shell=True)")
    assert result.passed is False


def test_growth_limit_pass():
    original = "x" * 100
    evolved = "x" * 115  # 15% growth, under 20% limit
    result = check_growth_limit(original, evolved)
    assert result.passed is True


def test_growth_limit_fail():
    original = "x" * 100
    evolved = "x" * 130  # 30% growth, over 20% limit
    result = check_growth_limit(original, evolved)
    assert result.passed is False


def test_non_empty_pass():
    result = check_non_empty("some content")
    assert result.passed is True


def test_non_empty_fail():
    result = check_non_empty("   ")
    assert result.passed is False


def test_skill_structure_valid():
    content = "---\nname: test\ndescription: A test skill\n---\n\n# Test Skill\n"
    result = check_skill_structure(content)
    assert result.passed is True


def test_skill_structure_missing_name():
    content = "---\ndescription: A test skill\n---\n\n# Test Skill\n"
    result = check_skill_structure(content)
    assert result.passed is False
