# Dolios Release Checklist

## Scope
Use this checklist before tagging a release or merging a high-risk integration PR.

## Preflight
1. Sync upstream sources and AI-DLC rules:
   - `uv run dolios upstream sync --include-aidlc`
2. Confirm current upstream state:
   - `uv run dolios upstream status --include-aidlc --refresh-remote`
3. Verify no unresolved policy approvals in runtime home:
   - inspect `~/.dolios/pending_approvals.yaml` (if present)

## Quality Gates
1. Run lint:
   - `uv run ruff check dolios tests`
2. Run tests:
   - `uv run pytest -q`
3. Run release verification:
   - `uv run dolios verify release`

## Security and Operations
1. Ensure active policy generates successfully:
   - `policies/generated/dolios-active.yaml` is updated
2. Confirm fused runtime compatibility:
   - `uv run dolios upstream compat`
3. Confirm AI-DLC sync metadata exists:
   - `.aidlc-rule-details/upstream-sync.yaml`
4. Review optional Hermes dependency diagnostics:
   - `optional-tool-deps` row in `uv run dolios verify release`
   - install with `uv sync --extra optional-tools` when required for target deployment

## Release Notes Inputs
1. Include upstream SHAs from `vendor/upstream-manifest.yaml`.
2. Include test and lint pass status.
3. Include behavior/security-impact summary for changed seams.
