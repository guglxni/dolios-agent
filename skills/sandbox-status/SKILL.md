# Skill: sandbox-status

Check NemoClaw sandbox health, policy state, and resource usage.

## When to Use
- User asks about sandbox status, health, or resources
- Before executing a task that requires specific sandbox capabilities
- When diagnosing connectivity or permission issues

## Steps
1. Query the NemoClaw sandbox state via OpenShell CLI
2. Check if all policy files are loaded and active
3. Report filesystem usage in writable directories
4. List active network policy rules
5. Show inference routing configuration
6. Report any pending endpoint approval requests

## Output Format
Provide a structured summary:
- Sandbox name and ID
- Running status (healthy/degraded/stopped)
- Policy status (loaded/stale/missing)
- Filesystem usage (writable dirs)
- Network policy summary (N allowed endpoints)
- Inference route (provider, model)
- Pending approvals (if any)
