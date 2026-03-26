# Dolios Security Extension — AI-DLC Rule Details

## Rule: DOLIOS-SEC-001 — Sandbox-Aware Tool Execution
Every tool call must be verified against the active NemoClaw policy before execution.
Blocked calls must surface to the operator, not silently fail.

### Verification Checklist:
- [ ] Tool's network endpoints are in the allowed egress list
- [ ] File paths are within sandbox-permitted directories
- [ ] No privilege escalation in command execution
- [ ] Inference calls route through the OpenShell gateway

## Rule: DOLIOS-SEC-002 — Credential Management
- No hardcoded API keys anywhere in the codebase
- All secrets injected via environment variables
- Sandbox credential injection for runtime keys
- Secrets never logged, even at DEBUG level

## Rule: DOLIOS-SEC-003 — Inference Isolation
- All model API calls intercepted by sandbox gateway
- No direct outbound inference connections from agent
- Provider switching must go through inference_router.py
- Route changes logged for audit trail

## Rule: DOLIOS-SEC-004 — Evolution Safety
- Evolved artifacts deploy as new versions only
- No hot-swapping of active session state
- All evolution changes submitted as PRs
- Human review required before merge
- Full test suite must pass (zero tolerance)

## Rule: DOLIOS-SEC-005 — Filesystem Boundaries
- Writable: /sandbox/workspace, /sandbox/skills, /sandbox/memory, /tmp
- Readonly: /sandbox/dolios/brand, /sandbox/dolios/policies
- Agent must not attempt to write outside these paths
- Path traversal attempts must be detected and blocked
