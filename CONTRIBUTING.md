# Contributing to Dolios

Thank you for your interest in contributing to Dolios. This guide covers everything you need to get started.

## Contribution Priorities

In order of priority:

1. **Security fixes** — Sandbox bypasses, credential leaks, injection vulnerabilities
2. **Bug fixes** — Anything that breaks existing functionality
3. **Performance** — Startup time, inference routing, policy checking
4. **New skills** — Dolios-specific skills for sandbox/evolution/policy management
5. **New tool integrations** — Extend the policy bridge for new Hermes tools
6. **Documentation** — Architecture docs, deployment guides, skill authoring guides
7. **Tests** — Increase coverage, add integration tests

## Development Setup

### Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) (package manager)
- Git
- Docker (for sandbox testing)

### Setup

```bash
git clone --recurse-submodules https://github.com/guglxni/dolios-agent.git
cd dolios-agent
uv sync --extra dev
# Optional: enable Firecrawl/FAL-backed Hermes tool integrations
uv sync --extra optional-tools
```

### Running

```bash
uv run dolios doctor       # verify setup
uv run dolios --no-sandbox # run without Docker (dev only)
uv run pytest -v           # run tests
uv run ruff check dolios/  # lint
uv run ruff format dolios/ # format
uv run dolios verify release # release-readiness checks
```

## Project Structure

```
dolios/              Core orchestrator — the code you'll most likely be editing
  orchestrator.py    Main coordination loop (wires Hermes + NemoClaw + evolution)
  policy_bridge.py   Hermes tools → NemoClaw network policy YAML
  inference_router.py Multi-provider model routing
  aidlc_engine.py    AI-DLC workflow phase detection
  brand.py           Brand identity / SOUL.md management
  config.py          Configuration loading and merging
  cli.py             Click CLI (all dolios commands)
  io.py              Shared I/O utilities (atomic writes, YAML/JSON helpers)
  vendor_path.py     Vendor repo sys.path management (security-anchored)

environments/        Hermes Agent terminal backend for NemoClaw
evolution/           Self-evolution pipeline integration
skills/              Dolios-specific skills (SKILL.md format)
policies/            NemoClaw policy templates and presets
tests/               pytest suite
vendor/              Upstream repos (git submodules — do not modify)
```

## AI-DLC Workflow

All development follows the AI-DLC methodology defined in [`CLAUDE.md`](CLAUDE.md):

1. **INCEPTION** — Understand requirements, validate against the PRD, decompose into units of work
2. **CONSTRUCTION** — Implement, test, validate. Import from vendor/ — never copy code.
3. **OPERATIONS** — Deploy, verify policy enforcement, check sandbox health

## Key Rules

- **Never modify vendor/ code.** Use adapters, wrappers, and extension points in `dolios/`.
- **Write tests alongside implementation.** All PRs must maintain or increase test count.
- **Import from `dolios.io`** for all YAML/JSON I/O (atomic writes, consistent error handling).
- **Import from `dolios.vendor_path`** for all vendor repo access (prevents dependency confusion).
- **Security-critical files** (policies, routing code) require manual review — they cannot be auto-evolved.
- **Optional Hermes tool SDKs** are intentionally non-blocking; install `uv sync --extra optional-tools` for web/image integrations.

## Adding a New Skill

Create a directory under `skills/` with a `SKILL.md`:

```markdown
# Skill: my-skill-name

Description of what the skill does.

## When to Use
- Conditions that trigger this skill

## Steps
1. Step one
2. Step two

## Output Format
- Expected output structure
```

## Adding a New Tool Policy

Add an entry to `TOOL_POLICIES` in `dolios/policy_bridge.py`:

```python
"my_tool": {
    "name": "my_tool",
    "endpoints": [
        {"host": "api.example.com", "port": 443, "protocol": "rest",
         "enforcement": "enforce", "tls": "terminate",
         "rules": [{"allow": {"method": "POST", "path": "/v1/**"}}]},
    ],
},
```

## Security Considerations

- All tool calls execute inside the NemoClaw sandbox
- Network egress is deny-by-default — tools must have explicit policy entries
- API keys are never passed as CLI args — use env vars or temp files
- Evolved artifacts pass 7 constraint gates before deployment
- Context files are scanned for prompt injection patterns

See [`SECURITY-AUDIT.md`](SECURITY-AUDIT.md) for the full audit report.

## PR Process

1. Fork and create a feature branch: `git checkout -b feat/my-feature`
2. Make changes following the rules above
3. Run tests: `uv run pytest -v`
4. Run lint: `uv run ruff check dolios/`
5. Run release checks: `uv run dolios verify release`
6. Submit PR with a clear description of what changed and why

## License

By contributing, you agree that your contributions will be licensed under the [MIT License](LICENSE).
