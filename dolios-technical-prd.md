# DOLIOS — Technical PRD & Architecture Spec
## Agentic AI System: Hermes Agent × NemoClaw × AI-DLC

**Version:** 1.0.0  
**Author:** Aaryan (AI/ML Engineer, Solana India Fellow)  
**Date:** March 23, 2026  
**Status:** Draft — Pre-Implementation  
**License Target:** MIT (agent layer) + Apache 2.0 (sandbox layer)

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Problem Statement](#2-problem-statement)
3. [Architecture Overview](#3-architecture-overview)
4. [Component Deep-Dive](#4-component-deep-dive)
5. [Integration Map: Hermes Agent](#5-integration-map-hermes-agent)
6. [Integration Map: NemoClaw / OpenShell](#6-integration-map-nemoclaw--openshell)
7. [Integration Map: AI-DLC Workflows](#7-integration-map-ai-dlc-workflows)
8. [Integration Map: Self-Evolution](#8-integration-map-self-evolution)
9. [Dolios-Specific Extensions](#9-dolios-specific-extensions)
10. [Development Lifecycle (AI-DLC Adapted)](#10-development-lifecycle-ai-dlc-adapted)
11. [Repository Structure](#11-repository-structure)
12. [Implementation Roadmap](#12-implementation-roadmap)
13. [API & Interface Contracts](#13-api--interface-contracts)
14. [Security Model](#14-security-model)
15. [Deployment Targets](#15-deployment-targets)
16. [Open Questions & Risks](#16-open-questions--risks)

---

## 1. Executive Summary

**Dolios** is an open-source agentic AI system that combines three production-grade components into a unified stack:

- **Hermes Agent** (Nous Research) — The self-improving agent runtime with a closed learning loop, skill system, multi-platform gateway, and RL training pipeline.
- **NemoClaw** (NVIDIA) — The sandboxed execution environment using OpenShell for policy-enforced network, filesystem, process, and inference isolation.
- **AI-DLC** (AWS Labs) — The adaptive development workflow methodology providing structured Inception → Construction → Operations phases for building the system itself.

Dolios adds a **unifying orchestration layer** that:
1. Wraps Hermes Agent's tool-calling loop inside NemoClaw's sandboxed runtime
2. Applies AI-DLC workflow rules to its own development and to tasks it executes for users
3. Integrates the Hermes Self-Evolution pipeline for continuous skill/prompt optimization
4. Exposes a branded, configurable interface under the Dolios identity

The result: a **self-improving, sandboxed, methodology-aware agent** that can be deployed on a $5 VPS, a GPU cluster, or serverless infrastructure.

---

## 2. Problem Statement

### Current Pain Points in the Agent Ecosystem

**Hermes Agent alone** provides an excellent agent runtime with learning capabilities, but runs with full system access — no sandboxing, no egress control, no policy enforcement. A misbehaving tool call can `rm -rf /` or exfiltrate data.

**NemoClaw alone** provides world-class sandboxing for OpenClaw agents, but is tightly coupled to the OpenClaw agent format and NVIDIA's Nemotron inference pipeline. It doesn't natively support Hermes Agent's skill system, learning loop, or multi-provider inference routing.

**AI-DLC alone** is a methodology, not a runtime. It provides excellent workflow rules for development but has no agent execution layer.

**The gap:** No existing system combines a self-improving agent with production-grade sandboxing and structured development methodology. Dolios fills this gap.

---

## 3. Architecture Overview

```
┌──────────────────────────────────────────────────────────────────┐
│                        USER INTERFACES                           │
│  CLI (TUI)  │  Telegram  │  Discord  │  Slack  │  WhatsApp      │
└──────────┬───────────────────────────────────────────────────────┘
           │
           ▼
┌──────────────────────────────────────────────────────────────────┐
│                    DOLIOS ORCHESTRATOR                            │
│                                                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌──────────────────────────┐ │
│  │ AI-DLC      │  │ Dolios      │  │ Brand / Identity Layer   │ │
│  │ Workflow     │  │ Config &    │  │ (System prompts,         │ │
│  │ Engine       │  │ Policy Mgr  │  │  voice, personality)     │ │
│  └──────┬──────┘  └──────┬──────┘  └──────────────────────────┘ │
│         │                │                                       │
│         ▼                ▼                                       │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              HERMES AGENT RUNTIME                         │   │
│  │                                                           │   │
│  │  Agent Loop  │  Skills  │  Memory  │  Tools  │  Gateway   │   │
│  │  Subagents   │  Honcho  │  Cron    │  MCP    │  FTS5      │   │
│  └──────────────────────────┬────────────────────────────────┘   │
│                              │                                    │
└──────────────────────────────┼────────────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────────┐
│                    NEMOCLAW SANDBOX LAYER                         │
│                                                                  │
│  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌─────────────┐  │
│  │ Network   │  │ Filesystem│  │ Process   │  │ Inference   │  │
│  │ Policy    │  │ Isolation │  │ Sandbox   │  │ Routing     │  │
│  │ (egress)  │  │ (Landlock)│  │ (seccomp) │  │ (gateway)   │  │
│  └───────────┘  └───────────┘  └───────────┘  └─────────────┘  │
│                                                                  │
│  OpenShell Runtime  │  Blueprint Lifecycle  │  Policy YAML       │
└──────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────────┐
│                    INFERENCE PROVIDERS                            │
│                                                                  │
│  NVIDIA Nemotron  │  Nous Portal  │  OpenRouter (200+ models)   │
│  Kimi / Moonshot  │  MiniMax      │  OpenAI  │  Local (Ollama)  │
└──────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────────┐
│                    SELF-EVOLUTION PIPELINE                        │
│                                                                  │
│  DSPy + GEPA Optimizer  │  Execution Trace Analysis              │
│  Skill Evolution        │  Prompt Mutation & Selection            │
│  Constraint Gates       │  PR-based Human Review                  │
│  Atropos RL Envs        │  Trajectory Compression                 │
└──────────────────────────────────────────────────────────────────┘
```

---

## 4. Component Deep-Dive

### 4.1 Dolios Orchestrator (NEW — to build)

The glue layer that doesn't exist yet. Responsibilities:

| Function | Description |
|---|---|
| **Sandbox Bootstrapper** | Calls NemoClaw's blueprint lifecycle to create an OpenShell sandbox, then installs Hermes Agent inside it instead of OpenClaw. |
| **Policy Bridge** | Translates Hermes Agent's tool declarations into NemoClaw network policy YAML. When Hermes wants to call a new API, the bridge either permits (if policy allows) or surfaces the request for operator approval. |
| **Inference Router** | Extends NemoClaw's inference gateway to support Hermes Agent's multi-provider model switching (`hermes model`). NemoClaw's default routes through NVIDIA Endpoint; Dolios adds OpenRouter, Nous Portal, Kimi, etc. |
| **AI-DLC Steering** | Embeds AI-DLC workflow rules as Hermes Agent context files, enabling methodology-aware task execution. |
| **Brand Layer** | Applies Dolios identity (system prompts, personality, voice guidelines) on top of Hermes Agent's configurable personality system. |
| **Evolution Hook** | Connects the Self-Evolution pipeline to the running agent, feeding execution traces back for skill/prompt optimization. |

### 4.2 Hermes Agent Runtime (UPSTREAM — fork/extend)

Key capabilities Dolios inherits directly from Hermes Agent v0.3.0:

**Agent Loop & Skills:**
- Closed learning loop: agent creates skills from experience, improves them during use
- Persistent memory with periodic nudges for self-curation
- FTS5 session search with LLM summarization for cross-session recall
- Honcho dialectic user modeling for deepening user understanding
- Compatible with agentskills.io open standard

**Multi-Platform Gateway:**
- Telegram, Discord, Slack, WhatsApp, Signal, Email
- Voice memo transcription
- Cross-platform conversation continuity
- Built-in cron scheduler for unattended automation

**Execution Backends:**
- Local, Docker, SSH, Daytona, Singularity, Modal
- Serverless persistence (Daytona, Modal) — environment hibernates when idle
- Subagent delegation for parallel workstreams

**Research Pipeline:**
- Batch trajectory generation
- Atropos RL environments (via tinker-atropos submodule)
- Trajectory compression for training next-gen tool-calling models

**Migration Path:**
- Built-in `hermes claw migrate` for OpenClaw users
- Imports SOUL.md, memories, skills, API keys, messaging configs

### 4.3 NemoClaw Sandbox (UPSTREAM — adapt)

Key capabilities Dolios inherits from NemoClaw (alpha, March 2026):

**OpenShell Runtime:**
- Landlock + seccomp + netns isolation
- Filesystem restricted to `/sandbox` and `/tmp`
- Privilege escalation and dangerous syscall blocking
- Locked at sandbox creation, not modifiable at runtime

**Network Policy:**
- Declarative YAML egress control
- Hot-reloadable at runtime
- Operator approval flow for unlisted hosts (surfaced in TUI)
- Preset policies for PyPI, Docker Hub, Slack, Jira

**Inference Routing:**
- All model API calls intercepted by OpenShell gateway
- Rerouted to controlled backends
- Default: NVIDIA Nemotron-3-super-120b-a12b
- Local (Ollama, vLLM) experimental

**Blueprint Lifecycle:**
- Resolve artifact → Verify digest → Plan resources → Apply via OpenShell CLI
- Versioned Python artifact for reproducible sandbox creation

### 4.4 AI-DLC Workflow (UPSTREAM — integrate as steering rules)

Three-phase adaptive methodology from AWS Labs:

**INCEPTION (What & Why):**
- Requirements analysis and validation
- User story creation
- Application design and unit-of-work decomposition
- Risk assessment and complexity evaluation

**CONSTRUCTION (How):**
- Detailed component design
- Code generation and implementation
- Build configuration and testing
- Quality assurance and validation

**OPERATIONS (Deploy & Monitor):**
- Deployment automation
- Monitoring and observability
- Production readiness validation

**Key AI-DLC Properties:**
- Agent-agnostic (works with any coding agent via steering files)
- Adaptive — only executes stages that add value
- Question-driven — structured multiple-choice in files, not chat
- Human-in-the-loop — agent proposes, human approves
- Extensible — security, compliance, custom rule overlays

**Integration into Dolios:**
- AI-DLC `core-workflow.md` becomes a Hermes Agent context file
- `.aidlc-rule-details/` directory ships with Dolios for construction phases
- Self-Evolution pipeline uses AI-DLC phases to structure optimization runs

### 4.5 Self-Evolution Pipeline (UPSTREAM — integrate)

From `hermes-agent-self-evolution`:

**Engine: DSPy + GEPA (Genetic-Pareto Prompt Evolution):**
- Reads execution traces to understand WHY things fail
- Proposes targeted improvements (not random mutations)
- ICLR 2026 Oral, MIT licensed
- No GPU training required — API calls only (~$2-10 per run)

**Optimization Targets (Phased):**

| Phase | Target | Engine | Status |
|---|---|---|---|
| Phase 1 | Skill files (SKILL.md) | DSPy + GEPA | Implemented |
| Phase 2 | Tool descriptions | DSPy + GEPA | Planned |
| Phase 3 | System prompt sections | DSPy + GEPA | Planned |
| Phase 4 | Tool implementation code | Darwinian Evolver | Planned |
| Phase 5 | Continuous improvement loop | Automated pipeline | Planned |

**Guardrails:**
- Full test suite must pass 100%
- Size limits: Skills ≤15KB, tool descriptions ≤500 chars
- Semantic preservation — must not drift from original purpose
- All changes via PR with human review, never direct commit

---

## 5. Integration Map: Hermes Agent

### What Dolios Forks/Extends

```
hermes-agent/
├── agent/              → Core agent loop — EXTEND with sandbox awareness
├── skills/             → Skill system — EXTEND with Dolios-specific skills
├── tools/              → Tool declarations — EXTEND with policy bridge hooks
├── gateway/            → Multi-platform gateway — USE AS-IS
├── environments/       → Terminal backends — ADD NemoClaw backend
├── hermes_cli/         → CLI — WRAP with `dolios` CLI
├── honcho_integration/ → User modeling — USE AS-IS
├── cron/               → Scheduled tasks — USE AS-IS
├── acp_adapter/        → Agent Communication Protocol — USE AS-IS
├── acp_registry/       → ACP registry — USE AS-IS
├── datagen-config-examples/ → Training data configs — EXTEND
├── optional-skills/    → Optional skill packs — USE AS-IS
├── batch_runner.py     → Trajectory batch gen — USE AS-IS
├── rl_cli.py           → RL training CLI — USE AS-IS
├── trajectory_compressor.py → Training data compression — USE AS-IS
└── toolset_distributions.py → Tool sampling for training — USE AS-IS
```

### Key Extension Points

1. **New Terminal Backend: `nemoclaw`**
   - Add to `environments/` alongside local, docker, ssh, daytona, singularity, modal
   - Hermes Agent's tool execution routes through OpenShell sandbox
   - File I/O restricted to sandbox-permitted paths
   - Network calls governed by NemoClaw policy

2. **Tool Policy Bridge**
   - Intercept `model_tools.py` tool declarations
   - Map each tool's required network endpoints to NemoClaw YAML policy
   - Auto-generate policy from tool manifest
   - Surface new/unknown endpoints for operator approval

3. **Dolios Personality**
   - Custom SOUL.md with Dolios brand voice (cunning, precise, grounded, technical)
   - Context file with brand guidelines from handoff doc
   - Greek mythology references used sparingly per voice spec

4. **AI-DLC Context Integration**
   - Copy `core-workflow.md` to Hermes Agent's context files directory
   - Agent uses AI-DLC phases when executing complex multi-step tasks
   - Inception → understand what the user wants
   - Construction → plan and execute
   - Operations → verify and deliver

---

## 6. Integration Map: NemoClaw / OpenShell

### What Dolios Adapts

```
NemoClaw/
├── nemoclaw/           → Plugin (TS CLI) — FORK for Dolios CLI
├── nemoclaw-blueprint/ → Blueprint (Python) — MODIFY to install Hermes
│   └── policies/       → Sandbox policies — EXTEND with Hermes tool policies
│       └── presets/    → Common integration presets — ADD Hermes-specific
├── bin/                → Binary entrypoints — WRAP with `dolios` namespace
├── scripts/            → Setup scripts — ADAPT for Hermes Agent deps
├── install.sh          → Installer — CREATE dolios-specific installer
└── Dockerfile          → Container — EXTEND with Python/Hermes deps
```

### Critical Adaptation: Blueprint Modification

NemoClaw's blueprint creates a sandbox and installs OpenClaw inside it. Dolios needs to:

1. **Replace OpenClaw with Hermes Agent** in the blueprint's sandbox setup phase
2. **Install Python 3.11+ and uv** (Hermes Agent's dependency manager) in the sandbox image
3. **Configure Hermes Agent's `.env`** with inference routing through OpenShell gateway
4. **Map Hermes Agent's tool network requirements** to NemoClaw policy YAML

### Inference Extension

NemoClaw routes all inference through NVIDIA Endpoint by default. Dolios extends this:

| Provider | Routing Strategy |
|---|---|
| NVIDIA Nemotron | Direct through NemoClaw gateway (default) |
| Nous Portal | Allowlist `portal.nousresearch.com` in network policy |
| OpenRouter | Allowlist `openrouter.ai` in network policy |
| Kimi / Moonshot | Allowlist `api.moonshot.ai` |
| MiniMax | Allowlist `api.minimax.chat` |
| OpenAI | Allowlist `api.openai.com` |
| Local (Ollama) | Route through host network (experimental) |

---

## 7. Integration Map: AI-DLC Workflows

### How Dolios Uses AI-DLC

AI-DLC is used at TWO levels:

**Level 1: Building Dolios itself**
- AI-DLC rules placed in `.claude/CLAUDE.md` (for Claude Code) or `.clinerules/` (for Cline)
- Development follows Inception → Construction → Operations
- Extensions: security baseline enforced, custom Dolios compliance rules

**Level 2: Inside the running Dolios agent**
- AI-DLC `core-workflow.md` loaded as a Hermes Agent context file
- When users ask Dolios to build software, it follows AI-DLC methodology
- Structured questions, execution plans, human approval gates

### AI-DLC Extension: Dolios Security Rules

Custom extension at `.aidlc-rule-details/extensions/dolios-security/`:

```markdown
## Rule: DOLIOS-SEC-001 — Sandbox-Aware Tool Execution
Every tool call must be verified against the active NemoClaw policy before execution.
Blocked calls must surface to the operator, not silently fail.

## Verification:
- [ ] Tool's network endpoints are in the allowed egress list
- [ ] File paths are within sandbox-permitted directories
- [ ] No privilege escalation in command execution
- [ ] Inference calls route through the OpenShell gateway
```

---

## 8. Integration Map: Self-Evolution

### Pipeline Integration

```
Dolios Agent (running) 
    │
    ├── Execution traces logged to ~/.dolios/traces/
    │
    ▼
Self-Evolution Pipeline (scheduled or manual)
    │
    ├── Reads traces from ~/.dolios/traces/
    ├── Identifies underperforming skills/prompts
    ├── Runs DSPy + GEPA optimization
    ├── Validates against constraint gates
    │   ├── pytest tests/ -q must pass 100%
    │   ├── Skills ≤15KB
    │   ├── Tool descriptions ≤500 chars
    │   └── Semantic preservation check
    │
    ├── Generates PR against dolios repo
    └── Human reviews and merges
```

### Dolios-Specific Evolution Targets

Beyond the base self-evolution targets, Dolios adds:

| Target | Description |
|---|---|
| NemoClaw policy templates | Evolve policy YAML to minimize permission surface while maintaining functionality |
| AI-DLC steering rules | Optimize the AI-DLC context file for better methodology adherence |
| Brand voice prompts | Evolve Dolios personality/system prompt for better user experience |
| Inference routing heuristics | Optimize model selection based on task type and cost constraints |

---

## 9. Dolios-Specific Extensions

### 9.1 Dolios Skills (New)

Custom skills that ship with Dolios:

| Skill | Description |
|---|---|
| `sandbox-status` | Check NemoClaw sandbox health, policy state, and resource usage |
| `policy-request` | Request operator approval for a new network endpoint |
| `model-switch` | Switch inference provider with awareness of sandbox routing |
| `aidlc-phase` | Report current AI-DLC phase and suggest next steps |
| `evolution-report` | Show self-evolution pipeline status and recent optimizations |
| `trace-analyze` | Analyze recent execution traces for failure patterns |

### 9.2 Dolios Tools (New)

| Tool | Description |
|---|---|
| `dolios_sandbox_exec` | Execute a command inside the NemoClaw sandbox with policy enforcement |
| `dolios_policy_check` | Verify if a network endpoint is allowed before attempting connection |
| `dolios_inference_route` | Select optimal inference provider based on task type and budget |

---

## 10. Development Lifecycle (AI-DLC Adapted)

### Inception Phase

1. **Requirements Analysis** — This PRD document
2. **Complexity Assessment** — High (multi-repo integration, sandbox modification, new orchestration layer)
3. **Risk Assessment** — NemoClaw is alpha software; interfaces may change without notice
4. **Unit of Work Decomposition** — See Implementation Roadmap (Section 12)

### Construction Phase

Built using AI-DLC rules with Claude Code or Hermes Agent itself:

```
dolios/
├── CLAUDE.md                    ← AI-DLC core-workflow.md
├── .aidlc-rule-details/         ← Full AI-DLC rule details
│   ├── common/
│   ├── inception/
│   ├── construction/
│   ├── operations/
│   └── extensions/
│       └── dolios-security/     ← Custom security rules
└── aidlc-docs/                  ← AI-DLC generated artifacts
```

### Operations Phase

- Docker Compose deployment with NemoClaw sandbox
- Kubernetes operator (future)
- Monitoring via OpenShell TUI + Hermes Agent `/insights`

---

## 11. Repository Structure

```
dolios/
├── README.md
├── LICENSE                      # MIT
├── CLAUDE.md                    # AI-DLC workflow rules
├── AGENTS.md                    # Agent instructions
├── .aidlc-rule-details/         # AI-DLC detailed rules
├── pyproject.toml               # Python package config (uv)
├── Dockerfile                   # Extended NemoClaw + Hermes
├── docker-compose.yml           # Full stack local dev
│
├── dolios/                      # Core orchestrator
│   ├── __init__.py
│   ├── config.py                # Dolios configuration
│   ├── orchestrator.py          # Main orchestration loop
│   ├── policy_bridge.py         # Hermes tools → NemoClaw policy
│   ├── inference_router.py      # Multi-provider inference routing
│   ├── brand.py                 # Brand identity / personality
│   └── aidlc_engine.py          # AI-DLC workflow integration
│
├── environments/                # New Hermes Agent backend
│   └── nemoclaw_backend.py      # NemoClaw terminal backend
│
├── skills/                      # Dolios-specific skills
│   ├── sandbox-status/
│   ├── policy-request/
│   ├── model-switch/
│   ├── aidlc-phase/
│   ├── evolution-report/
│   └── trace-analyze/
│
├── policies/                    # NemoClaw policy templates
│   ├── dolios-default.yaml      # Base policy
│   ├── presets/                 # Common integration presets
│   └── generated/               # Auto-generated from tool manifest
│
├── evolution/                   # Self-evolution integration
│   ├── dolios_targets.py        # Dolios-specific evolution targets
│   ├── trace_collector.py       # Execution trace logging
│   └── constraint_gates.py      # Custom guardrails
│
├── brand/                       # Brand identity assets
│   ├── SOUL.md                  # Dolios personality
│   ├── context.md               # Brand context file
│   └── voice_guidelines.md      # Voice reference
│
├── scripts/
│   ├── install.sh               # One-line installer
│   ├── setup-sandbox.sh         # NemoClaw sandbox setup
│   └── migrate-hermes.sh        # Migrate from vanilla Hermes
│
├── tests/
│   ├── test_orchestrator.py
│   ├── test_policy_bridge.py
│   ├── test_inference_router.py
│   └── test_evolution.py
│
└── docs/
    ├── architecture.md
    ├── getting-started.md
    ├── deployment.md
    └── contributing.md
```

---

## 12. Implementation Roadmap

### M0: Foundation (Week 1-2)
- [ ] Fork hermes-agent, set up dolios repo structure
- [ ] Copy AI-DLC workflow rules into project root
- [ ] Create SOUL.md with Dolios brand personality
- [ ] Set up basic `dolios` CLI wrapper around `hermes`
- [ ] Write this PRD as the CLAUDE.md steering document

### M1: Sandbox Integration (Week 3-4)
- [ ] Install NemoClaw locally, understand blueprint lifecycle
- [ ] Modify NemoClaw blueprint to install Hermes Agent instead of OpenClaw
- [ ] Create `nemoclaw_backend.py` terminal environment for Hermes
- [ ] Extend sandbox Docker image with Python 3.11 + uv + Hermes deps
- [ ] Verify basic chat works inside sandbox

### M2: Policy Bridge (Week 5-6)
- [ ] Build `policy_bridge.py` — parse Hermes tool declarations → NemoClaw YAML
- [ ] Create `dolios-default.yaml` policy with baseline allowed endpoints
- [ ] Implement operator approval flow for new endpoints
- [ ] Add policy presets for common Hermes tools (web search, GitHub, etc.)
- [ ] Test: tool calls blocked when policy denies, approved when policy allows

### M3: Multi-Provider Inference (Week 7-8)
- [ ] Extend NemoClaw inference gateway for non-NVIDIA providers
- [ ] Implement `inference_router.py` with cost/capability selection
- [ ] Map Hermes Agent's `hermes model` command to policy-aware routing
- [ ] Test: switch between Nemotron, OpenRouter, Kimi with sandbox enforcement
- [ ] Verify inference calls never bypass sandbox gateway

### M4: AI-DLC Integration (Week 9-10)
- [ ] Create `aidlc_engine.py` — load AI-DLC context into Hermes Agent
- [ ] Build `aidlc-phase` skill for phase reporting
- [ ] Test: Dolios follows AI-DLC methodology when building software for users
- [ ] Create Dolios-specific AI-DLC security extension
- [ ] Validate extension loading during Inception phase

### M5: Self-Evolution (Week 11-12)
- [ ] Integrate `hermes-agent-self-evolution` as submodule
- [ ] Build `trace_collector.py` — log execution traces from sandbox
- [ ] Add Dolios-specific evolution targets (policy, brand voice, routing)
- [ ] Create `evolution-report` skill
- [ ] Run first evolution cycle on Dolios skills
- [ ] Validate constraint gates (tests pass, size limits, semantic preservation)

### M6: Polish & Release (Week 13-14)
- [ ] One-line installer script
- [ ] Docker Compose full-stack deployment
- [ ] Documentation (architecture, getting-started, deployment, contributing)
- [ ] Brand assets integrated (logo SVGs in README, favicon)
- [ ] v0.1.0 release

---

## 13. API & Interface Contracts

### Dolios CLI

```bash
dolios                  # Start interactive TUI (Hermes inside sandbox)
dolios setup            # Full setup wizard (NemoClaw + Hermes + providers)
dolios model            # Switch inference provider (sandbox-aware)
dolios sandbox status   # Check sandbox health
dolios sandbox policy   # View/edit network policy
dolios sandbox approve  # Approve pending endpoint requests
dolios evolve           # Run self-evolution pipeline
dolios evolve --dry-run # Preview evolution changes
dolios aidlc            # Show current AI-DLC phase
dolios gateway          # Start messaging gateway (Telegram, Discord, etc.)
dolios migrate hermes   # Migrate from vanilla Hermes Agent
dolios migrate openclaw # Migrate from OpenClaw (via Hermes bridge)
dolios doctor           # Diagnose issues
dolios update           # Update all components
```

### Policy YAML Contract

```yaml
# dolios-default.yaml
version: "1.0"
metadata:
  name: dolios-default
  description: Base policy for Dolios agent

network:
  default: deny
  allow:
    # Inference providers
    - host: "integrate.api.nvidia.com"
      ports: [443]
      label: "NVIDIA Nemotron"
    - host: "openrouter.ai"
      ports: [443]
      label: "OpenRouter"
    - host: "portal.nousresearch.com"
      ports: [443]
      label: "Nous Portal"
    
    # Tool requirements (auto-generated from tool manifest)
    - host: "api.github.com"
      ports: [443]
      label: "GitHub API (hermes-tool: github)"
    - host: "*.googleapis.com"
      ports: [443]
      label: "Google APIs (hermes-tool: web_search)"

filesystem:
  writable:
    - /sandbox/workspace
    - /sandbox/skills
    - /sandbox/memory
    - /tmp
  readonly:
    - /sandbox/dolios/brand
    - /sandbox/dolios/policies

process:
  allow_privilege_escalation: false
  blocked_syscalls: [ptrace, mount, reboot]
```

### Inference Router Interface

```python
class DoliosInferenceRouter:
    """Routes inference requests through sandbox gateway to optimal provider."""
    
    async def route(
        self,
        messages: list[dict],
        task_type: str = "general",  # general | code | creative | analysis
        max_cost_per_1k: float = 0.01,
        preferred_provider: str | None = None,
    ) -> InferenceResponse:
        """
        Select provider based on:
        1. Task type → capability matching
        2. Cost constraint → budget filtering
        3. Policy → allowed providers in sandbox
        4. Preference → user override
        """
        ...
```

---

## 14. Security Model

### Defense in Depth

| Layer | Mechanism | Provided By |
|---|---|---|
| Network | Egress policy (deny-by-default) | NemoClaw / OpenShell |
| Filesystem | Landlock (writable paths whitelist) | NemoClaw / OpenShell |
| Process | seccomp + no privilege escalation | NemoClaw / OpenShell |
| Inference | Gateway interception, no direct model API calls | NemoClaw |
| Tool Execution | Policy bridge validates before execution | Dolios |
| Operator Approval | Unknown endpoints surfaced for human decision | NemoClaw + Dolios |
| Evolution | PR-based review, never direct commit | Self-Evolution pipeline |
| AI-DLC | Human-in-the-loop at every phase gate | AI-DLC methodology |

### Threat Model

| Threat | Mitigation |
|---|---|
| Prompt injection leading to data exfiltration | Network policy blocks all non-whitelisted egress |
| Malicious skill installation | Skill files sandboxed to `/sandbox/skills`, evolution requires PR review |
| Model hallucination executing dangerous commands | seccomp blocks dangerous syscalls, filesystem restricts write paths |
| Supply chain attack via dependency | Sandbox image built from pinned deps, digest-verified blueprint |
| Inference data leakage | All inference routes through auditable gateway |

---

## 15. Deployment Targets

### Tier 1: Local Development
```bash
curl -fsSL https://dolios.dev/install.sh | bash
dolios setup  # Guided wizard
dolios        # Start chatting
```

### Tier 2: Docker Compose
```yaml
services:
  dolios:
    build: .
    ports: ["8080:8080"]
    volumes:
      - ./workspace:/sandbox/workspace
    environment:
      - NVIDIA_API_KEY=${NVIDIA_API_KEY}
      - OPENROUTER_API_KEY=${OPENROUTER_API_KEY}
```

### Tier 3: Serverless (Future)
- Daytona / Modal backends (inherited from Hermes Agent)
- Environment hibernates when idle
- Costs nearly nothing between sessions

### Tier 4: GPU Cluster (Future)
- Local inference via Ollama/vLLM inside sandbox
- NemoClaw host-routing for local model access
- Best for airgapped or privacy-sensitive deployments

---

## 16. Open Questions & Risks

### Open Questions

| # | Question | Impact | Owner |
|---|---|---|---|
| 1 | NemoClaw is alpha — will API/blueprint format change before M1? | High — could invalidate sandbox integration | Track NemoClaw releases |
| 2 | Can OpenShell sandbox run Hermes Agent's Node.js gateway alongside Python agent? | Medium — may need separate processes | Test in M1 |
| 3 | How does Hermes Agent's Docker terminal backend interact with NemoClaw's Docker-based sandbox? | Medium — nested containers? | Architecture decision in M1 |
| 4 | Should Dolios self-evolution auto-merge PRs for low-risk changes? | Low — start conservative (human review all) | Decide in M5 |
| 5 | License compatibility: Hermes (MIT) + NemoClaw (Apache 2.0) + AI-DLC (MIT-0)? | Low — all permissive, compatible | Verify with legal review |

### Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| NemoClaw breaking changes during alpha | High | High | Pin to specific commit, track upstream closely |
| OpenShell not supporting macOS host-routing for local inference | Medium | Medium | Default to cloud inference, document limitation |
| Hermes Agent upstream changes conflicting with Dolios fork | Medium | Medium | Keep fork minimal, upstream PRs where possible |
| Self-evolution producing degraded skills | Low | Medium | Constraint gates + mandatory human PR review |
| AI-DLC methodology overhead slowing simple tasks | Low | Low | AI-DLC is adaptive — simple tasks skip unnecessary phases |

---

## Appendix A: Key Repository Links

| Repository | URL | Stars | License |
|---|---|---|---|
| Hermes Agent | https://github.com/NousResearch/hermes-agent | 8.7k | MIT |
| NemoClaw | https://github.com/NVIDIA/NemoClaw | 15.2k | Apache 2.0 |
| AI-DLC Workflows | https://github.com/awslabs/aidlc-workflows | 618 | MIT-0 |
| Hermes Self-Evolution | https://github.com/NousResearch/hermes-agent-self-evolution | 17 | MIT |
| OpenShell | https://github.com/NVIDIA/OpenShell | — | — |

## Appendix B: AI-DLC Quick Reference

**Activate:** Start any prompt with "Using AI-DLC, ..." in chat.

**Phases:** INCEPTION (blue) → CONSTRUCTION (green) → OPERATIONS (yellow)

**Platform setup for Dolios development:**
```bash
# Claude Code
cp core-workflow.md ./CLAUDE.md
mkdir -p .aidlc-rule-details
cp -R aws-aidlc-rule-details/* .aidlc-rule-details/

# Cursor
mkdir -p .cursor/rules
# ... (see AI-DLC docs for full setup)
```

## Appendix C: Hermes Agent Key Commands Reference

```bash
hermes              # Start interactive CLI
hermes model        # Choose LLM provider/model
hermes tools        # Configure enabled tools
hermes config set   # Set config values
hermes gateway      # Start messaging gateway
hermes setup        # Full setup wizard
hermes claw migrate # Migrate from OpenClaw
hermes update       # Update to latest
hermes doctor       # Diagnose issues
```

---

*This document is the source of truth for the Dolios project. It should be placed at the repository root and referenced by AI-DLC workflow rules during development.*
