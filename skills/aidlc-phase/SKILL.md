# Skill: aidlc-phase

Report current AI-DLC phase and suggest next steps.

## When to Use
- User asks about the current workflow phase
- Starting a new complex task (to determine which phase to enter)
- User wants guidance on the AI-DLC methodology

## Steps
1. Detect the current AI-DLC phase from conversation context
2. Explain what the current phase focuses on
3. List completed and pending activities in this phase
4. Suggest what to do next
5. If at a phase gate: prompt for human approval before transitioning

## Phases
- INCEPTION: Requirements, design, risk assessment. Ask questions, don't implement.
- CONSTRUCTION: Implementation, testing, validation. Write code, run tests.
- OPERATIONS: Deployment, monitoring, production readiness. Verify and ship.

## Output Format
- Current phase: INCEPTION/CONSTRUCTION/OPERATIONS
- Focus: what this phase is about
- Next steps: 2-3 concrete actions
