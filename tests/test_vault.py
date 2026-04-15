"""Tests for dolios.security.vault — credential vault."""

import os

import pytest

from dolios.security.vault import CredentialVault


def test_load_from_env_removes_key(monkeypatch):
    monkeypatch.setenv("MY_SECRET", "super-secret-value")
    vault = CredentialVault()
    vault.load_from_env("MY_SECRET", label="MY_SECRET")
    assert os.environ.get("MY_SECRET") is None


def test_inject_roundtrip(monkeypatch):
    monkeypatch.setenv("MY_KEY", "plaintext-value-here")
    vault = CredentialVault()
    vault.load_from_env("MY_KEY", label="MY_KEY")
    assert vault.inject("MY_KEY") == "plaintext-value-here"


def test_inject_unknown_raises():
    vault = CredentialVault()
    with pytest.raises(KeyError):
        vault.inject("nonexistent")


def test_repr_hides_values(monkeypatch):
    monkeypatch.setenv("SECRET", "s3cr3t")
    vault = CredentialVault()
    vault.load_from_env("SECRET", label="SECRET")
    r = repr(vault)
    assert "s3cr3t" not in r
    assert "SECRET" in r  # label IS shown


def test_two_vaults_different_keys(monkeypatch):
    monkeypatch.setenv("K", "value")
    v1 = CredentialVault()
    v1.load_from_env("K", label="K")

    monkeypatch.setenv("K", "value")
    v2 = CredentialVault()
    v2.load_from_env("K", label="K")

    # Encrypted bytes differ because Fernet keys differ
    assert v1._store["K"] != v2._store["K"]
    # But both decrypt to the same value
    assert v1.inject("K") == v2.inject("K") == "value"


def test_has(monkeypatch):
    monkeypatch.setenv("X", "val")
    vault = CredentialVault()
    assert vault.has("X") is False
    vault.load_from_env("X", label="X")
    assert vault.has("X") is True
    assert vault.has("Y") is False
