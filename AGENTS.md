# AGENTS.md — Dolios Agent Instructions

## For AI Coding Agents Working on This Repository

You are working on **Dolios**, a self-improving sandboxed agentic AI system that combines:
- **Hermes Agent** (vendor/hermes-agent) — self-improving agent runtime
- **NemoClaw** (vendor/nemoclaw) — sandboxed execution via OpenShell
- **Self-Evolution** (vendor/hermes-agent-self-evolution) — DSPy/GEPA optimization

### Ground Rules

1. **Read the PRD first**: `dolios-technical-prd.md` is the source of truth
2. **Read CLAUDE.md**: Contains AI-DLC workflow rules and code conventions
3. **Never modify vendor/ code**: Use adapters, wrappers, and extension points
4. **Test everything**: `uv run pytest` must pass before any PR
5. **Security first**: All tool execution must be policy-aware (see DOLIOS-SEC rules in CLAUDE.md)

### Architecture Quick Reference

```
dolios/           → Core orchestrator (Python, our code)
vendor/           → Upstream repos (git submodules, don't modify)
environments/     → Hermes Agent backend for NemoClaw
skills/           → Dolios-specific skill definitions
policies/         → NemoClaw policy templates
evolution/        → Self-evolution integration
brand/            → Brand identity (SOUL.md, voice, context)
tests/            → pytest test suite
```

### When Adding Features

1. Check if hermes-agent already has it (likely does — 40+ tools, 25 skill categories)
2. If yes, write an adapter in `dolios/` that imports and wraps it
3. If no, implement in `dolios/` following the same patterns as hermes-agent
4. Add sandbox awareness (policy check, inference routing) to any new tool
5. Write tests in `tests/`
