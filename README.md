<p align="center">
  <img src="dolios-brand/assets/logo-lockup.svg" alt="Dolios" width="400">
</p>

<h1 align="center">Dolios Δ</h1>

<p align="center">
  <strong>The Crafty Agent — Scheme. Execute. Deliver.</strong>
</p>

<p align="center">
  <a href="https://github.com/guglxni/dolios-agent/blob/main/LICENSE"><img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge" alt="License"></a>
  <a href="https://github.com/guglxni/dolios-agent"><img src="https://img.shields.io/badge/Built%20by-Aaryan%20Guglani-blueviolet?style=for-the-badge" alt="Built by"></a>
  <a href="https://github.com/guglxni/dolios-agent/actions"><img src="https://img.shields.io/badge/Tests-56%20passing-brightgreen?style=for-the-badge" alt="Tests"></a>
  <a href="https://owasp.org/Top10/2025/"><img src="https://img.shields.io/badge/OWASP-2025%20Audited-orange?style=for-the-badge" alt="OWASP"></a>
</p>

---

A self-improving, sandboxed AI agent that combines [Hermes Agent](https://github.com/NousResearch/hermes-agent)'s closed learning loop with [NemoClaw](https://github.com/NVIDIA/NemoClaw)'s production-grade sandbox isolation. Dolios wraps these systems in a unified orchestration layer with multi-provider inference routing, AI-DLC methodology awareness, and a DSPy/GEPA self-evolution pipeline — all deployable on a $5 VPS, a GPU cluster, or serverless infrastructure.

No vendor lock-in. Works with NVIDIA Nemotron, Nous Portal, OpenRouter (200+ models), OpenAI, Anthropic, Kimi, MiniMax, or local models via Ollama/vLLM.

## Features

| Feature | Description |
|---------|-------------|
| **Sandboxed execution** | Every tool call runs inside a NemoClaw/OpenShell sandbox with Landlock filesystem isolation, seccomp process restrictions, and deny-by-default network policies. |
| **Self-improving skills** | Closed learning loop: the agent creates procedural skills from experience, improves them via DSPy/GEPA optimization, and persists knowledge across sessions. |
| **Multi-provider inference** | Smart model routing across NVIDIA, Nous, OpenRouter, OpenAI, Anthropic, and local inference — all intercepted by the sandbox gateway. |
| **Lives where you do** | CLI with interactive TUI, plus multi-platform messaging gateway (Telegram, Discord, Slack, WhatsApp, Signal). |
| **Methodology-aware** | AI-DLC workflow engine: Inception → Construction → Operations phases for structured task execution with human-in-the-loop gates. |
| **Security-first** | OWASP Top 10:2025 + LLM Top 10:2025 audited. Fail-closed defaults, prompt injection scanning, API key redaction, atomic writes. 67/67 findings resolved. |
| **Research-ready** | Batch trajectory generation, Atropos RL environments, execution trace collection for training next-gen tool-calling models. |

## Quick Install

```bash
curl -fsSL https://dolios.dev/install.sh | bash
```

Or install manually:

```bash
git clone --recurse-submodules https://github.com/guglxni/dolios-agent.git
cd dolios-agent
uv sync
dolios setup    # guided configuration wizard
dolios          # start the agent
```

Requires **Python 3.12+**, **uv**, **git**, and **Docker** (for sandbox). Runs on Linux, macOS, and WSL2.

After install, verify with:

```bash
dolios doctor   # checks all prerequisites
```

## Getting Started

| Command | Description |
|---------|-------------|
| `dolios` | Start the interactive agent (default: starts chat) |
| `dolios setup` | Full setup wizard — configure providers, API keys, sandbox |
| `dolios model` | Show or switch inference provider/model |
| `dolios sandbox status` | Check sandbox health and policy state |
| `dolios sandbox policy` | View active network policies |
| `dolios sandbox approve` | Approve pending endpoint access requests |
| `dolios evolve run` | Run the self-evolution pipeline on a skill |
| `dolios evolve status` | Show evolution pipeline status |
| `dolios aidlc` | Show current AI-DLC workflow phase |
| `dolios doctor` | Diagnose installation issues |

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                     USER INTERFACES                           │
│  CLI (TUI)  │  Telegram  │  Discord  │  Slack  │  WhatsApp   │
└──────────┬───────────────────────────────────────────────────┘
           │
           ▼
┌──────────────────────────────────────────────────────────────┐
│                   DOLIOS ORCHESTRATOR                          │
│                                                               │
│  Policy Bridge  │  Inference Router  │  AI-DLC Engine         │
│  Brand Layer    │  Trace Collector   │  Prompt Injection Scan  │
└──────────┬───────────────────────────────────────────────────┘
           │
           ▼
┌──────────────────────────────────────────────────────────────┐
│                 HERMES AGENT RUNTIME                           │
│                                                               │
│  Agent Loop  │  Skills  │  Memory  │  Tools  │  Gateway       │
│  Subagents   │  Honcho  │  Cron    │  MCP    │  FTS5 Search   │
└──────────┬───────────────────────────────────────────────────┘
           │
           ▼
┌──────────────────────────────────────────────────────────────┐
│                 NEMOCLAW SANDBOX LAYER                         │
│                                                               │
│  Network Policy  │  Filesystem Isolation  │  Process Sandbox   │
│  (deny-default)  │  (Landlock strict)     │  (seccomp)         │
│  Inference Gateway  │  Blueprint Lifecycle  │  Policy YAML      │
└──────────┬───────────────────────────────────────────────────┘
           │
           ▼
┌──────────────────────────────────────────────────────────────┐
│                 INFERENCE PROVIDERS                            │
│  NVIDIA Nemotron │ Nous Portal │ OpenRouter │ OpenAI │ Local  │
└──────────────────────────────────────────────────────────────┘
```

## Project Structure

```
dolios-agent/
├── dolios/                  # Core orchestrator (Python)
│   ├── orchestrator.py      # Main coordination loop
│   ├── policy_bridge.py     # Hermes tools → NemoClaw policies
│   ├── inference_router.py  # Multi-provider model routing
│   ├── aidlc_engine.py      # AI-DLC workflow integration
│   ├── brand.py             # Brand identity / personality
│   ├── config.py            # Configuration management
│   ├── cli.py               # Click-based CLI
│   ├── io.py                # Shared I/O utilities (atomic writes)
│   └── vendor_path.py       # Vendor repo path management
├── environments/            # NemoClaw terminal backend
├── evolution/               # Self-evolution pipeline integration
│   ├── trace_collector.py   # Execution trace logging
│   ├── dolios_targets.py    # Evolution targets
│   └── constraint_gates.py  # Safety guardrails (7 gates)
├── skills/                  # Dolios-specific skills (6)
├── policies/                # NemoClaw policy templates
├── dolios-blueprint/        # Sandbox blueprint + policies
├── brand/                   # SOUL.md, voice guidelines
├── vendor/                  # Upstream repos (git submodules)
│   ├── hermes-agent/        # Nous Research — agent runtime
│   ├── nemoclaw/            # NVIDIA — sandbox layer
│   └── hermes-agent-self-evolution/  # DSPy/GEPA pipeline
├── tests/                   # pytest suite (56 tests)
├── scripts/                 # Installer
├── CLAUDE.md                # AI-DLC workflow rules
├── AGENTS.md                # Instructions for AI coding agents
├── SECURITY-AUDIT.md        # Full OWASP audit report
└── dolios-technical-prd.md  # Technical PRD
```

## Security

Dolios has been audited against both [OWASP Top 10:2025](https://owasp.org/Top10/2025/) and [OWASP Top 10 for LLM Applications 2025](https://genai.owasp.org/resource/owasp-top-10-for-llm-applications-2025/). All 67 findings across 3 audit passes have been resolved.

Key security properties:
- **Fail-closed defaults** — no policy = deny all, DNS failure = reject, missing Landlock = refuse to start
- **Prompt injection scanning** — context files scanned for injection patterns and invisible Unicode before agent injection
- **API key redaction** — keys never appear in logs, CLI args, repr, or process listings
- **Atomic writes** — all state/policy/trace files use write-to-temp + rename
- **Evolution safety** — AI cannot evolve its own sandbox policies or routing code; 7 constraint gates enforce size, growth, structure, and security
- **Supply chain** — Docker images pinned by SHA256 digest, lockfile committed, per-build auth tokens

See [`SECURITY-AUDIT.md`](SECURITY-AUDIT.md) for the complete audit report.

## Self-Evolution

Dolios integrates the [hermes-agent-self-evolution](https://github.com/NousResearch/hermes-agent-self-evolution) pipeline for continuous skill improvement:

```bash
dolios evolve run --target skill-sandbox-status --iterations 10
dolios evolve run --dry-run                    # preview available targets
```

The pipeline uses DSPy + GEPA (Genetic-Pareto Prompt Evolution) to optimize skills based on execution traces. No GPU required — runs via API calls at ~$2-10 per optimization cycle.

**Safety guardrails:**
- 7 constraint gates must ALL pass (tests, size, growth, structure, non-empty, semantic preservation, security patterns)
- Security-critical files (policies, routing code) excluded from auto-evolution
- All changes via PR with human review — never direct commit

## Hermes Agent Migration

If you're coming from [Hermes Agent](https://github.com/NousResearch/hermes-agent), Dolios extends it with sandboxing and self-evolution while preserving full compatibility:

| What | Status |
|------|--------|
| SOUL.md / personality | Migrated to `brand/SOUL.md` with Dolios identity |
| Skills | All Hermes skills available, plus 6 Dolios-specific skills |
| Memory & sessions | Preserved via Hermes SessionDB |
| Tools (40+) | All available, with NemoClaw policy enforcement |
| Multi-platform gateway | Telegram, Discord, Slack, WhatsApp, Signal — unchanged |
| Cron scheduler | Unchanged |
| Honcho user modeling | Unchanged |

## Development

```bash
git clone --recurse-submodules https://github.com/guglxni/dolios-agent.git
cd dolios-agent
uv sync --extra dev
uv run pytest               # run tests (56 passing)
uv run ruff check dolios/   # lint
uv run ruff format dolios/  # format
```

Development follows the AI-DLC methodology. See [`CLAUDE.md`](CLAUDE.md) for workflow rules and [`CONTRIBUTING.md`](CONTRIBUTING.md) for the full guide.

## Community

- [GitHub Issues](https://github.com/guglxni/dolios-agent/issues) — Bug reports and feature requests
- [Technical PRD](dolios-technical-prd.md) — Full architecture specification
- [Security Audit](SECURITY-AUDIT.md) — OWASP audit report

## License

[MIT](LICENSE) (agent layer) + [Apache 2.0](LICENSE) (sandbox layer)

Built on [Hermes Agent](https://github.com/NousResearch/hermes-agent) by Nous Research and [NemoClaw](https://github.com/NVIDIA/NemoClaw) by NVIDIA.
