# DOLIOS — AI-DLC Workflow Rules

> This file serves as the AI-DLC core workflow document for the Dolios project.
> All development follows the Inception → Construction → Operations methodology.

## Project Identity

**Dolios** — "The Crafty Agent" | Scheme. Execute. Deliver.
A self-improving, sandboxed, methodology-aware agentic AI system.

- **PRD**: `dolios-technical-prd.md` (source of truth)
- **License**: MIT (agent layer) + Apache 2.0 (sandbox layer)
- **Stack**: Python 3.12+ / uv / Click / DSPy / Docker

## Architecture (4-Layer Stack)

```
User Interfaces (CLI TUI, Telegram, Discord, Slack, WhatsApp)
    ↓
Dolios Orchestrator (dolios/) — NEW code, the glue layer
    ↓
Hermes Agent Runtime (vendor/hermes-agent) — forked, extended
    ↓
NemoClaw Sandbox (vendor/nemoclaw) — adapted blueprint
    ↓
Inference Providers + Self-Evolution Pipeline
```

## AI-DLC Phases

### INCEPTION (What & Why)
Before implementing any feature:
1. Read the relevant PRD section
2. Validate requirements against existing code in vendor/
3. Decompose into units of work
4. Identify risks (NemoClaw is alpha — pin commits)
5. Get human approval before proceeding

### CONSTRUCTION (How)
When building:
1. Follow the repository structure in PRD Section 11
2. Import from vendor/ repos — do NOT copy code
3. Write tests alongside implementation
4. Use type hints (Python 3.12+ syntax)
5. Keep modules under 400 lines
6. Run `uv run pytest` before considering work complete

### OPERATIONS (Deploy & Monitor)
When deploying or verifying:
1. Docker Compose is the primary local deployment target
2. All inference must route through sandbox gateway
3. Verify policy enforcement before any release
4. Self-evolution changes require PR review — never direct commit

## Code Conventions

- **Package manager**: uv (not pip, not poetry)
- **CLI framework**: Click (consistent with Dolios CLI design)
- **Formatting**: ruff format
- **Linting**: ruff check
- **Testing**: pytest with pytest-asyncio
- **Type checking**: pyright or mypy (strict mode)
- **Imports**: absolute imports from `dolios.` namespace
- **Docstrings**: Only where logic is non-obvious. No boilerplate docstrings.
- **Error handling**: Let exceptions propagate unless at a boundary (CLI, API, sandbox edge)

## Vendor Integration Rules

### vendor/hermes-agent (Hermes Agent v2026.6.5 / v0.16.0)
- **DO**: Import modules, extend classes, add new backends
- **DO NOT**: Modify vendor code directly — use wrapper/adapter pattern
- **Key entry**: `hermes_cli.main:main`, `agent/prompt_builder.py`, `environments/`

### vendor/nemoclaw (NemoClaw alpha)
- **DO**: Use blueprint.yaml as template, adapt policies, reference runner.py patterns
- **DO NOT**: Assume API stability — pin to current commit
- **Key entry**: `nemoclaw-blueprint/orchestrator/runner.py`, `nemoclaw-blueprint/policies/`

### vendor/hermes-agent-self-evolution
- **DO**: Import evolution modules, extend with Dolios-specific targets
- **DO NOT**: Modify core DSPy/GEPA integration
- **Key entry**: `evolution/core/`, `evolution/skills/`

## Security Rules (DOLIOS-SEC)

1. **DOLIOS-SEC-001**: Every tool call verified against active NemoClaw policy before execution
2. **DOLIOS-SEC-002**: No hardcoded API keys — use env vars or sandbox credential injection
3. **DOLIOS-SEC-003**: Inference calls MUST route through OpenShell gateway — never direct
4. **DOLIOS-SEC-004**: Evolved skills deploy as new versions only — no hot-swapping active sessions
5. **DOLIOS-SEC-005**: File I/O restricted to sandbox-permitted paths in production

## Key Files

| File | Purpose |
|------|---------|
| `dolios-technical-prd.md` | Full PRD — source of truth |
| `dolios/orchestrator.py` | Main orchestration loop |
| `dolios/policy_bridge.py` | Hermes tools → NemoClaw policy YAML |
| `dolios/inference_router.py` | Multi-provider inference routing |
| `dolios/aidlc_engine.py` | AI-DLC workflow integration |
| `dolios/brand.py` | Brand identity / personality layer |
| `dolios/config.py` | Configuration management |
| `brand/SOUL.md` | Dolios personality definition |
| `environments/nemoclaw_backend.py` | NemoClaw terminal backend for Hermes |
| `policies/dolios-default.yaml` | Base sandbox policy |

## Development Commands

```bash
uv sync                          # Install dependencies
uv run dolios                    # Start Dolios CLI
uv run dolios setup              # Setup wizard
uv run dolios sandbox status     # Check sandbox health
uv run dolios evolve --dry-run   # Preview evolution changes
uv run pytest                    # Run test suite
uv run ruff check dolios/        # Lint
uv run ruff format dolios/       # Format
```

## AI-DLC Extension: Dolios Security Overlay

See `.aidlc-rule-details/extensions/dolios-security/` for full security rule definitions
that are enforced during Construction phase.

<!-- gitnexus:start -->
# GitNexus — Code Intelligence

This project is indexed by GitNexus as **dolios-agent** (1045 symbols, 2570 relationships, 86 execution flows). Use the GitNexus MCP tools to understand code, assess impact, and navigate safely.

> If any GitNexus tool warns the index is stale, run `npx gitnexus analyze` in terminal first.

## Always Do

- **MUST run impact analysis before editing any symbol.** Before modifying a function, class, or method, run `gitnexus_impact({target: "symbolName", direction: "upstream"})` and report the blast radius (direct callers, affected processes, risk level) to the user.
- **MUST run `gitnexus_detect_changes()` before committing** to verify your changes only affect expected symbols and execution flows.
- **MUST warn the user** if impact analysis returns HIGH or CRITICAL risk before proceeding with edits.
- When exploring unfamiliar code, use `gitnexus_query({query: "concept"})` to find execution flows instead of grepping. It returns process-grouped results ranked by relevance.
- When you need full context on a specific symbol — callers, callees, which execution flows it participates in — use `gitnexus_context({name: "symbolName"})`.

## When Debugging

1. `gitnexus_query({query: "<error or symptom>"})` — find execution flows related to the issue
2. `gitnexus_context({name: "<suspect function>"})` — see all callers, callees, and process participation
3. `READ gitnexus://repo/dolios-agent/process/{processName}` — trace the full execution flow step by step
4. For regressions: `gitnexus_detect_changes({scope: "compare", base_ref: "main"})` — see what your branch changed

## When Refactoring

- **Renaming**: MUST use `gitnexus_rename({symbol_name: "old", new_name: "new", dry_run: true})` first. Review the preview — graph edits are safe, text_search edits need manual review. Then run with `dry_run: false`.
- **Extracting/Splitting**: MUST run `gitnexus_context({name: "target"})` to see all incoming/outgoing refs, then `gitnexus_impact({target: "target", direction: "upstream"})` to find all external callers before moving code.
- After any refactor: run `gitnexus_detect_changes({scope: "all"})` to verify only expected files changed.

## Never Do

- NEVER edit a function, class, or method without first running `gitnexus_impact` on it.
- NEVER ignore HIGH or CRITICAL risk warnings from impact analysis.
- NEVER rename symbols with find-and-replace — use `gitnexus_rename` which understands the call graph.
- NEVER commit changes without running `gitnexus_detect_changes()` to check affected scope.

## Tools Quick Reference

| Tool | When to use | Command |
|------|-------------|---------|
| `query` | Find code by concept | `gitnexus_query({query: "auth validation"})` |
| `context` | 360-degree view of one symbol | `gitnexus_context({name: "validateUser"})` |
| `impact` | Blast radius before editing | `gitnexus_impact({target: "X", direction: "upstream"})` |
| `detect_changes` | Pre-commit scope check | `gitnexus_detect_changes({scope: "staged"})` |
| `rename` | Safe multi-file rename | `gitnexus_rename({symbol_name: "old", new_name: "new", dry_run: true})` |
| `cypher` | Custom graph queries | `gitnexus_cypher({query: "MATCH ..."})` |

## Impact Risk Levels

| Depth | Meaning | Action |
|-------|---------|--------|
| d=1 | WILL BREAK — direct callers/importers | MUST update these |
| d=2 | LIKELY AFFECTED — indirect deps | Should test |
| d=3 | MAY NEED TESTING — transitive | Test if critical path |

## Resources

| Resource | Use for |
|----------|---------|
| `gitnexus://repo/dolios-agent/context` | Codebase overview, check index freshness |
| `gitnexus://repo/dolios-agent/clusters` | All functional areas |
| `gitnexus://repo/dolios-agent/processes` | All execution flows |
| `gitnexus://repo/dolios-agent/process/{name}` | Step-by-step execution trace |

## Self-Check Before Finishing

Before completing any code modification task, verify:
1. `gitnexus_impact` was run for all modified symbols
2. No HIGH/CRITICAL risk warnings were ignored
3. `gitnexus_detect_changes()` confirms changes match expected scope
4. All d=1 (WILL BREAK) dependents were updated

## Keeping the Index Fresh

After committing code changes, the GitNexus index becomes stale. Re-run analyze to update it:

```bash
npx gitnexus analyze
```

If the index previously included embeddings, preserve them by adding `--embeddings`:

```bash
npx gitnexus analyze --embeddings
```

To check whether embeddings exist, inspect `.gitnexus/meta.json` — the `stats.embeddings` field shows the count (0 means no embeddings). **Running analyze without `--embeddings` will delete any previously generated embeddings.**

> Claude Code users: A PostToolUse hook handles this automatically after `git commit` and `git merge`.

## CLI

| Task | Read this skill file |
|------|---------------------|
| Understand architecture / "How does X work?" | `.claude/skills/gitnexus/gitnexus-exploring/SKILL.md` |
| Blast radius / "What breaks if I change X?" | `.claude/skills/gitnexus/gitnexus-impact-analysis/SKILL.md` |
| Trace bugs / "Why is X failing?" | `.claude/skills/gitnexus/gitnexus-debugging/SKILL.md` |
| Rename / extract / split / refactor | `.claude/skills/gitnexus/gitnexus-refactoring/SKILL.md` |
| Tools, resources, schema reference | `.claude/skills/gitnexus/gitnexus-guide/SKILL.md` |
| Index, status, clean, wiki CLI commands | `.claude/skills/gitnexus/gitnexus-cli/SKILL.md` |

<!-- gitnexus:end -->
