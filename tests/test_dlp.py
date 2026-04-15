"""Tests for dolios.security.dlp — outbound DLP scanner."""

from dolios.config import DoliosConfig
from dolios.security.dlp import DLPScanner


def _scanner() -> DLPScanner:
    return DLPScanner(DoliosConfig())


def test_clean_args():
    clean, findings = _scanner().scan("tool", {"query": "hello world"})
    assert clean is True
    assert findings == []


def test_api_key_detected():
    clean, findings = _scanner().scan(
        "tool", {"data": "my api key is sk-abcdefghij1234567890"}
    )
    assert clean is False
    assert any(f.pattern_category == "CREDENTIAL" for f in findings)


def test_aadhaar_detected():
    clean, findings = _scanner().scan("tool", {"id": "1234 5678 9012"})
    assert clean is False
    assert any(f.pattern_category == "AADHAAR" for f in findings)


def test_pan_detected():
    clean, findings = _scanner().scan("tool", {"pan": "ABCDE1234F"})
    assert clean is False
    assert any(f.pattern_category == "PAN" for f in findings)


def test_private_key_detected():
    clean, findings = _scanner().scan(
        "tool", {"key": "-----BEGIN RSA PRIVATE KEY-----\ndata"}
    )
    assert clean is False
    assert any(f.pattern_category == "PRIVATE_KEY" for f in findings)


def test_email_blocked():
    clean, findings = _scanner().scan("tool", {"to": "user@example.com"})
    assert clean is False
    assert any(f.pattern_category == "PII_EMAIL" for f in findings)


def test_email_allowed_by_type():
    clean, findings = _scanner().scan(
        "email_tool",
        {"to": "user@example.com"},
        allowed_types=["PII_EMAIL"],
    )
    assert clean is True
    assert findings == []


def test_nested_dict_scanning():
    clean, findings = _scanner().scan("tool", {
        "level1": {"level2": {"email": "test@example.com"}},
    })
    assert clean is False
    assert findings[0].field_path == "level1.level2.email"


def test_redacted_excerpt_max_chars():
    _, findings = _scanner().scan("tool", {"id": "1234 5678 9012"})
    for f in findings:
        original_chars = f.redacted_excerpt.replace("***", "")
        assert len(original_chars) <= 8
