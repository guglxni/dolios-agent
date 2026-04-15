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
- dolios/security/audit.py — AuditLogger
- dolios/security/vault.py — CredentialVault
- dolios/security/dlp.py — DLPScanner
- dolios/security/workflow.py — WorkflowPolicy
