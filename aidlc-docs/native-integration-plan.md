# Native Dolios Integration Plan (AI-DLC)

## Objective
Build Dolios as a tightly integrated runtime assembled from Hermes Agent, NemoClaw, and Hermes Self-Evolution capabilities, while converging toward Dolios-owned core modules.

## Current State (Brownfield)
- Dolios has orchestration and adapter layers in place.
- Runtime depends on externally present upstream repos under vendor/.
- AI-DLC rule details are partially populated and not fully aligned to latest awslabs/aidlc-workflows.

## Target State
- Dolios runtime has stable internal integration modules for:
  - Agent loop execution and tool dispatch
  - Sandbox lifecycle and policy enforcement
  - Evolution loop and constraint gates
- Upstream repos are synchronized from explicit SHAs and tracked in manifest artifacts.
- AI-DLC rules are synced from latest upstream, with Dolios security extension overlaid.

## Inception Units
1. U1: Baseline upstream versions and capture pinned SHAs.
2. U2: Define migration architecture from wrapper-heavy to native-fused modules.
3. U3: Define phased cutover strategy with rollback points and test gates.

## Construction Units
1. C1: Implement upstream sync manager and manifest generation.
2. C2: Add CLI controls for upstream status/sync workflows.
3. C3: Add AI-DLC rule sync from aidlc-workflows into .aidlc-rule-details.
4. C4: Introduce integration seams that replace direct runtime vendor imports.
5. C5: Add compatibility tests for latest upstream surfaces.
6. C6: Enforce AI-DLC phase gates in interactive runtime flow.
7. C7: Remove remaining non-adapter direct upstream imports.
8. C8: Add behavioral compatibility contracts for critical upstream interfaces.

## Operations Units
1. O1: Validate all tests, lint, and smoke flows.
2. O2: Document synced versions and active integration mode.
3. O3: Add release checklist for upstream bump and compatibility verification.

## Risks
- Upstream API drift can break direct imports.
- Tight coupling to moving heads introduces instability without pinned manifests.
- Full native fusion requires staged extraction and replacement, not a single-step rewrite.

## Acceptance Gates
- All tests pass after each unit.
- Upstream manifest is generated and committed.
- AI-DLC sync metadata is generated.
- No direct regressions in sandbox, inference routing, or evolution constraints.

## Initial Implementation Status
- C1 completed: upstream sync manager implemented with manifest generation.
- C2 completed: CLI upstream status/sync/compat commands implemented.
- C3 completed: AI-DLC rule sync from aidlc-workflows implemented.
- C4 completed: DoliosFusionRuntime + Hermes/NemoClaw/evolution adapters wired through orchestrator.
- C5 completed: upstream compatibility tests expanded from symbol presence to constructor/dispatcher contracts.
- C6 completed: runtime now blocks forward phase jumps until explicit approval, with /aidlc status/approve controls.
- C6 note: runtime phase gate remains available but is opt-in by default to keep AI-DLC primarily as the development workflow.
- C7 completed: CLI/orchestrator now route through integration seams; legacy evolution module is a shim.
- C8 completed: added behavioral upstream contract tests (Hermes chat + unknown-tool dispatch behavior).
- O1 completed: lint/tests/smoke checks integrated and `dolios verify release` passes.
- O2 completed: docs updated with integration mode, release-verification command, and optional dependency install guidance.
- O3 completed: release checklist and CI workflow added for upstream sync, lint, tests, and release verification.
