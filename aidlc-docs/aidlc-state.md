# AI-DLC State — Native Dolios Integration

## Workflow Context
- Workflow: AWS AI-DLC
- Source ruleset: awslabs/aidlc-workflows
- Current phase: OPERATIONS
- Date: 2026-04-15

## Extension Configuration
- dolios-security: Enabled
- security-baseline (aidlc extension): Planned
- property-based-testing (aidlc extension): Planned
- runtime AI-DLC phase approval gate: Optional (opt-in)

## Upstream Baselines (Latest at Planning Time)
- hermes-agent: 3e0bccc54c7ccc2ee27c16ab439de56aa66bc246
- nemoclaw: 855924fd0e4212b9218156a0261df5b6be6e13fb
- hermes-agent-self-evolution: 4693c8f0eed21e39f065c6f38d98d2a403a04095
- aidlc-workflows: 182b6e9edcbfca5357987ed22dccc8582ee52288
- aidlc-rules/VERSION: 0.1.7

## Planned Deliverables
- Native runtime fusion architecture plan with AI-DLC units
- Upstream sync and manifest tooling
- AI-DLC rule sync mechanism from awslabs/aidlc-workflows
- Progressive replacement of runtime vendor imports with Dolios-owned modules

## Construction Progress
- C1: Implement upstream sync manager and manifest generation (completed)
- C2: Add CLI controls for upstream status/sync workflows (completed)
- C3: Add AI-DLC rule sync from aidlc-workflows (completed)
- C4: Introduce fused Dolios integration seams for Hermes/NemoClaw/evolution (completed)
- C5: Add compatibility tests for latest upstream surfaces (completed, strict contracts added)
- C6: Enforce AI-DLC forward-phase approval gates in runtime loop (completed)
- C7: Remove remaining non-adapter direct upstream imports (completed)
- C8: Add behavioral compatibility contracts for key upstream interfaces (completed)

## Operations Progress
- O1: Release-readiness verification command added and validated (`dolios verify release` passes)
- O2: Integration mode and release docs updated (README + CONTRIBUTING)
- O3: Release checklist and CI workflow added for upstream sync, lint, tests, and release verification
- O3 update: optional Hermes dependency diagnostics documented with explicit install path (`uv sync --extra optional-tools`)
