# Skill: policy-request

Request operator approval for a new network endpoint.

## When to Use
- A tool call requires network access to an endpoint not in the current policy
- The sandbox blocks an outbound connection

## Steps
1. Identify the blocked endpoint (host, port)
2. Determine which tool needs the endpoint and why
3. Check if a policy preset exists that would cover it
4. If no preset: create a pending approval request with justification
5. Notify the operator via the CLI approval flow
6. If approved: add to the active policy and proceed
7. If denied: report the denial and suggest alternatives

## Output Format
- Endpoint: host:port
- Requesting tool: tool_name
- Reason: why this access is needed
- Status: pending/approved/denied
