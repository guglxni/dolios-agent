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

### vendor/hermes-agent (Hermes Agent v0.3.0)
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
