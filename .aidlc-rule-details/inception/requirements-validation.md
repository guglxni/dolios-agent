# AI-DLC Inception Rule: Requirements Validation

## Rule: INCEPTION-001 — Requirement Clarity
Before implementing any feature:
1. Identify the relevant PRD section
2. List all acceptance criteria
3. Identify dependencies on other components
4. Flag any ambiguities for human clarification
5. Estimate risk level (low/medium/high)

## Rule: INCEPTION-002 — Decomposition
Break work into units that:
- Can be completed in one session
- Have clear input and output
- Can be tested independently
- Don't require changes to vendor code

## Rule: INCEPTION-003 — Risk Assessment
Flag high-risk items:
- NemoClaw API changes (alpha software)
- Security policy modifications
- Inference routing changes
- Self-evolution pipeline modifications
