# DOLIOS SECURITY AUDIT REPORT

**Date:** March 26, 2026
**Auditor:** Automated multi-agent security review (8 parallel agents, 2 audit rounds)
**Scope:** Full codebase, Dockerfile, docker-compose, install scripts, policies, vendor architecture comparison
**Frameworks:**
- [OWASP Top 10:2025](https://owasp.org/Top10/2025/) (A01-A10, updated from 2021)
- [OWASP Top 10 for LLM Applications 2025](https://genai.owasp.org/resource/owasp-top-10-for-llm-applications-2025/) (LLM01-LLM10)
- CIS Docker Benchmark
- SLSA Supply Chain Security Framework

---

## OWASP Top 10:2025 Categories Used

| # | Category | Change from 2021 |
|---|----------|-------------------|
| A01 | Broken Access Control | Unchanged (#1), now includes SSRF |
| A02 | Security Misconfiguration | Moved up from #5 |
| A03 | **Software Supply Chain Failures** | **NEW in 2025** |
| A04 | Cryptographic Failures | Moved down from #2 |
| A05 | Injection | Moved down from #3 |
| A06 | Insecure Design | Moved down from #4 |
| A07 | Authentication Failures | Renamed (was "Identification and...") |
| A08 | Software or Data Integrity Failures | Unchanged |
| A09 | Security Logging and Alerting Failures | Renamed (added "Alerting") |
| A10 | **Mishandling of Exceptional Conditions** | **NEW in 2025** |

## OWASP LLM Top 10:2025 Categories Used

| # | Category |
|---|----------|
| LLM01 | Prompt Injection |
| LLM02 | Sensitive Information Disclosure |
| LLM03 | Supply Chain |
| LLM06 | Excessive Agency |
| LLM07 | System Prompt Leakage |
| LLM10 | Unbounded Consumption |

---

## Executive Summary

Three audit passes + vendor architecture comparison identified **67 unique findings**. After two implementation rounds, the final status:

| Severity | Found | Fixed | Remaining |
|----------|-------|-------|-----------|
| CRITICAL | 4 | 4 | 0 |
| HIGH | 15 | 15 | 0 |
| MEDIUM | 28 | 21 | 7 |
| LOW | 20 | 8 | 12 |

The most urgent remaining issues:
1. **P0:** Duplicate `process:` YAML key silently drops all syscall blocking
2. **P0:** No prompt injection scanning on context files (bypasses Hermes Agent's built-in defense)
3. **P0:** Evolution pipeline can evolve policies and routing code (AI self-weakening sandbox)
4. **P1:** Path traversal via `brand_voice` config reads arbitrary files into system prompt
5. **P1:** Docker fallback leaks API keys via CLI arguments
6. **P1:** CWD-relative `sys.path` allows dependency confusion attacks

---

## Architectural Gaps vs. Vendor Upstreams

### vs. NemoClaw

| Dimension | NemoClaw | Dolios | Gap |
|-----------|----------|--------|-----|
| Sandbox requirement | Hard fail (sys.exit) if OpenShell missing | Soft fail → Docker → local (no isolation) | Warns at WARNING level (FIXED) |
| SSRF validation | No localhost exceptions, full RFC 1918 blocklist | Localhost restricted to /v1 path + specific ports | SSRF fail-closed on DNS failure (FIXED) |
| Image pinning | SHA256 digest on base images | Pinned by digest | FIXED — `python:3.12-slim@sha256:3d5e...` |
| Auth token | Per-build `secrets.token_hex(32)` in immutable config | None | Remaining — add per-build token |
| Policy enforcement | `binaries` field restricts which process can use each endpoint | No binary restrictions | Add `binaries` constraints |
| Credential handling | Env var NAME passed, never raw value | Raw API key in InferenceRoute dataclass and os.environ | Pass env var names only |

### vs. Hermes Agent

| Dimension | Hermes Agent | Dolios | Gap |
|-----------|-------------|--------|-----|
| Prompt injection defense | Active scanning with pattern matching, Unicode detection, HTML injection detection | No scanning — writes .hermes.md directly | Call `_scan_context_content()` or let Hermes discover files natively |
| Tool dispatch | Registry with check_fn, error isolation, toolset gating | No pre-dispatch policy check (documented but unimplemented) | Wire `check_endpoint()` into dispatch |
| State persistence | SQLite + atomic JSON writes | Plain `json.dump()` without atomic write | Use write-to-temp + rename |

### vs. Self-Evolution Pipeline

| Dimension | Vendor | Dolios | Gap |
|-----------|--------|--------|-----|
| Constraint gates | Growth limit, non-empty check, structural validation, per-type size limits | Only size check and security patterns (now with regex) | Add growth limit, non-empty, and structure validation |
| Evolvable targets | Skills only (tier 1) | Skills + policies + routing code + system prompts | Remove policies and code from auto-evolution |
| Fitness evaluation | LLM-as-judge with rubric-based scoring | Word-overlap heuristic | Adopt LLM-as-judge from vendor |

---

## Prioritized Resolution Plan

### P0 — Fix Immediately (Sandbox Integrity at Risk)

**1. Duplicate `process:` key drops all syscall blocking**
- File: `dolios-blueprint/policies/dolios-sandbox.yaml`
- The second `process:` key overwrites the first, silently removing `blocked_syscalls`
- Fix: Merge into a single `process:` block

**2. No prompt injection scanning on context files**
- Files: `dolios/orchestrator.py:115-133`
- Dolios creates `.hermes.md` directly, bypassing Hermes Agent's `_scan_context_content()`
- Fix: Import and call `_scan_context_content()` from vendor before writing, OR stop pre-composing `.hermes.md` and let Hermes discover individual files

**3. Evolution can modify security-critical files**
- File: `evolution/dolios_targets.py:49-72`
- Tier 2 (policy) and tier 4 (routing code) targets allow the AI to weaken its own sandbox
- Fix: Remove `dolios-policy-default` and `dolios-inference-routing` from `DOLIOS_TARGETS`

### P1 — Fix This Sprint (Credential/Data Exposure)

**4. Path traversal via `brand_voice` config**
- File: `dolios/brand.py:27-29`
- A malicious `dolios.yaml` can set `brand_voice: "../../etc/passwd"` to exfiltrate files
- Fix: Validate resolved path stays within project directory

**5. Docker fallback leaks API keys in CLI args** — **FIXED (Round 2)**
- Uses `--env-file` with temp file (0600 permissions, deleted after use)

**6. CWD-relative sys.path enables dependency confusion** — **FIXED (Round 2)**
- Created `dolios/vendor_path.py` anchored to `Path(__file__).parent.parent`
- All vendor imports now use shared `ensure_vendor_on_path()`

**7. Sandbox disable via any truthy env var** — **FIXED (Round 2)**
- Now checks `.lower() in ("1", "true", "yes")` explicitly

**8. InferenceRoute exposes API key in repr/logging** — **FIXED (Round 1)**
- `__repr__` redacts api_key

**9. Missing pre-dispatch policy check** — REMAINING
- Documented in comments but not yet implemented
- Requires hooking into Hermes Agent's tool dispatch

### P2 — Fix This Milestone (Hardening)

**10. Pin Docker base images by digest** — **FIXED (Round 2)**
- `python:3.12-slim@sha256:3d5ed973e458...`

**11. Pin uv image by version** — **FIXED (Round 2)**
- `ghcr.io/astral-sh/uv:0.6.14`

**12. Add vendor constraint gates** — **FIXED (Round 2)**
- Added `check_growth_limit`, `check_non_empty`, `check_skill_structure`

**13. Remove fallback pip install from Dockerfile** — **FIXED (Round 2)**
- Removed `|| true` suppression

**14. Trace file rotation** — **FIXED (Round 2)**
- `MAX_TRACE_FILES = 1000`, rotated on init

**15. Atomic state file writes** — **FIXED (Round 2)**
- Created `dolios/io.py` with `save_json` using write-to-temp + `os.replace()`

**16. Sanitize exception messages to user** — **FIXED (Round 2)**
- Generic error shown to user, full trace logged at DEBUG (A10:2025)

**17. File locking on pending_approvals.yaml** — REMAINING
- Low risk (single-user CLI), but should add `filelock` for multi-process safety

**18. Preset name validation against path traversal** — **FIXED (Round 2)**
- `re.match(r'^[a-zA-Z0-9_-]+$', preset_name)` in `load_preset()`

### P3 — Fix Before Release (Polish)

**18-23.** Validate `preset_name` against traversal, restrict config merge to allowlist, add size limits to Docker volumes, verify checksum in install.sh, remove dead code (`_load_hermes_model_metadata`, unused `PolicyEndpoint` dataclass, `get_voice_guidelines`, `get_phase_prompt`), add `binaries` constraints to network policies.

---

## Industry Best Practices Recommendations

### From OWASP Top 10 for LLM Applications (2025)
- Deploy **NeMo Guardrails** or **Guardrails AI** as a runtime safety layer
- Red-team all 10 categories using **Promptfoo** or **DeepTeam**
- Implement **Chain-of-Verification (CoVe)** for consequential agent actions
- Treat every tool call as potentially attacker-influenced (LLM06: Excessive Agency)

### From SLSA / Supply Chain Security
- Commit `uv.lock` to version control (DONE)
- Enable **Sigstore attestations** via Trusted Publishing when publishing to PyPI
- Run **pip-audit** or **Oracle Macaron** in CI
- Target **SLSA Level 2** (scripted build, provenance generated by hosted build service)

### From CIS Docker Benchmark
- Run **Docker Bench for Security** in CI
- Use **Chainguard** or **distroless** base images instead of `python:3.12-slim`
- Sign images with **Cosign/Sigstore** before deployment
- Scan images with **Trivy** or **Grype** for CVEs

### From DevOps/LLMOps Best Practices
- Implement an **egress proxy** (e.g., Squid, Envoy) instead of relying solely on sandbox policies
- Use **ephemeral sandboxes** that are destroyed after each task (not persistent containers)
- Deploy **structured audit logging** for every tool call, network request, and file write
- Consider **Firecracker microVMs** or **gVisor** for code execution (stronger than Docker containers)

---

## Positive Security Findings

The codebase already demonstrates good security awareness:
- All YAML loading uses `yaml.safe_load()` — no `yaml.load()` calls
- No `pickle`, `marshal`, or `shelve` deserialization
- No `shell=True` in subprocess calls
- Docker container runs with `read_only: true`, `no-new-privileges: true`, `cap_drop: ALL`
- `uuid.uuid4()` used for session IDs (cryptographically secure)
- SSRF protection validates private IP ranges (now with fail-closed DNS)
- Security gate uses regex patterns (fixed from literal substring)
- Policy defaults to DENY ALL when missing (fixed from allow-all)
- `MAX_TRACE_EVENTS` prevents unbounded in-memory growth
- `uv.lock` committed for reproducible builds (fixed from gitignored)
