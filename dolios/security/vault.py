"""Credential vault — holds secrets encrypted in memory.

Secrets are loaded from environment variables at init time, encrypted with
a process-local Fernet key, and cleared from ``os.environ``.  The Fernet
key is generated fresh each process start and never persisted to disk.
"""

from __future__ import annotations

import os

from cryptography.fernet import Fernet


class CredentialVault:
    """In-memory encrypted credential store."""

    def __init__(self) -> None:
        self._key = Fernet.generate_key()
        self._fernet = Fernet(self._key)
        self._store: dict[str, bytes] = {}  # label → encrypted value

    def load_from_env(self, key_name: str, label: str) -> None:
        """Read ``os.environ[key_name]``, encrypt, store under *label*, pop from env."""
        value = os.environ.get(key_name, "")
        self._store[label] = self._fernet.encrypt(value.encode())
        os.environ.pop(key_name, None)

    def inject(self, label: str) -> str:
        """Decrypt and return the plaintext secret for *label*."""
        if label not in self._store:
            raise KeyError(f"No credential loaded for label: {label!r}")
        return self._fernet.decrypt(self._store[label]).decode()

    def has(self, label: str) -> bool:
        """Return True if *label* has been loaded into the vault."""
        return label in self._store

    def __repr__(self) -> str:
        labels = ", ".join(sorted(self._store.keys()))
        return f"CredentialVault(labels=[{labels}])"

    def __str__(self) -> str:
        return self.__repr__()
