"""Credential vault — holds secrets encrypted in memory.

Secrets are loaded from environment variables at init time, encrypted with
a process-local Fernet key, and cleared from ``os.environ``.  The Fernet
key is generated fresh each process start and never persisted to disk.

Security notes (SEC-L2):
- The Fernet key and encrypted blobs both reside in Python's heap simultaneously.
  A heap dump or memory forensics tool could theoretically extract both.
  For production deployments requiring hardware-backed secrets, use an HSM
  or OS keychain (macOS Keychain, Linux Secret Service via secretstorage).
- The process-local Fernet key is never written to disk or logged.
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
        """Read ``os.environ[key_name]``, encrypt, store under *label*, pop from env.

        Raises ``KeyError`` if the environment variable is not set or empty.
        Use ``load_from_env_optional`` if you want to silently skip missing vars.

        SEC-L3: Raises rather than storing an empty string so that ``has()``
        accurately reflects whether a usable credential is available.
        """
        value = os.environ.get(key_name)
        if not value:
            raise KeyError(
                f"Environment variable {key_name!r} is not set or empty. "
                "Cannot load credential into vault."
            )
        self._store[label] = self._fernet.encrypt(value.encode())
        os.environ.pop(key_name, None)

    def load_from_env_optional(self, key_name: str, label: str) -> bool:
        """Like ``load_from_env`` but returns False (and skips) if var is missing.

        Use this when the credential is optional and absence is not an error.
        Returns True if loaded, False if the env var was not set or empty.
        """
        value = os.environ.get(key_name)
        if not value:
            return False
        self._store[label] = self._fernet.encrypt(value.encode())
        os.environ.pop(key_name, None)
        return True

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
