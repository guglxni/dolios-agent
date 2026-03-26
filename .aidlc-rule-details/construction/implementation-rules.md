# AI-DLC Construction Rule: Implementation

## Rule: CONSTRUCTION-001 — Build Order
Follow the dependency graph:
1. config.py (no deps)
2. brand.py (depends on config)
3. policy_bridge.py (depends on config)
4. inference_router.py (depends on config)
5. aidlc_engine.py (depends on config)
6. orchestrator.py (depends on all above)
7. cli.py (depends on orchestrator)

## Rule: CONSTRUCTION-002 — Vendor Integration
- Import from vendor/ modules, never copy code
- Use adapter/wrapper pattern for extensions
- Pin vendor repos to specific commits
- Document any monkey-patches with justification

## Rule: CONSTRUCTION-003 — Validation
After each unit of work:
- Run `uv run pytest` — must pass
- Run `uv run ruff check dolios/` — must pass
- Manually verify the changed behavior
- Update tests if behavior changed
