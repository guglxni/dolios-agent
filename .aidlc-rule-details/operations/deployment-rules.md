# AI-DLC Operations Rule: Deployment

## Rule: OPERATIONS-001 — Pre-Deployment
Before any deployment:
- [ ] All tests pass (`uv run pytest`)
- [ ] Linting clean (`uv run ruff check`)
- [ ] Docker image builds (`docker compose build`)
- [ ] Policy YAML validates
- [ ] No hardcoded secrets in codebase

## Rule: OPERATIONS-002 — Deployment Targets
Priority order:
1. Local development (uv run dolios)
2. Docker Compose (docker compose up)
3. Serverless (Modal/Daytona) — future
4. GPU Cluster (Ollama/vLLM) — future

## Rule: OPERATIONS-003 — Monitoring
- Execution traces logged to ~/.dolios/traces/
- Inference costs tracked per session
- Sandbox health checks on startup
- Policy enforcement verified on every tool call
