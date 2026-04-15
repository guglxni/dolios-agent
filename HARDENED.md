# Dolios — Hardened Edition

This branch is a permanent parallel track of Dolios Agent incorporating
IronClaw-inspired security architecture. It diverges intentionally from main
and is not intended to be merged back.

## What's different from main

| Feature | main | hardened |
|---------|------|----------|
| Credential handling | env vars read at route time | CredentialVault with boundary injection |
| Audit logging | logger.info only | Append-only JSON-lines audit trail |
| Outbound scanning | none | DLP scanner on tool call arguments |
| Tool permissions | session-wide policy | Per-tool capability manifests |
| Tool ordering | LLM-driven (prompt level) | DAG-enforced (code level) |

## Syncing with main

Periodically merge main INTO this branch to pull base improvements:
  git merge main
Never merge hardened into main.

## New modules (dolios/security/)

- **dolios/security/audit.py** — `AuditLogger`: append-only JSON-lines audit trail
  with atomic writes, fcntl locking, SHA-256 argument hashing, and log rotation.
- **dolios/security/vault.py** — `CredentialVault`: Fernet-encrypted in-memory
  secret store. Keys loaded from env vars at startup and cleared from os.environ.
- **dolios/security/workflow.py** — `WorkflowPolicy`: DAG-based tool ordering
  enforcement loaded from policies/workflow.yaml. Per-session state tracking.
- **dolios/security/dlp.py** — `DLPScanner`: regex-based outbound argument
  scanner detecting credentials, PII (email, phone, Aadhaar, PAN), private keys,
  and env variable leaks before tool dispatch.

## New config sections (dolios/config.py)

- `AuditConfig` — enabled, log_path, max_size_mb
- `WorkflowConfig` — enabled, policy_file
- `DLPConfig` — enabled

## Per-tool capability manifests (skills/*/capabilities.yaml)

Each skill declares its network, filesystem, and DLP allowances in a
capabilities.yaml manifest. PolicyBridge merges these into the generated
NemoClaw policy at startup.
