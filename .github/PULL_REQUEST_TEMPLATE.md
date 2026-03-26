## What does this PR do?

<!-- Brief description of the changes -->

## Related Issue

<!-- Link to the GitHub issue, if applicable -->
Fixes #

## Type of Change

- [ ] Bug fix (non-breaking change that fixes an issue)
- [ ] New feature (non-breaking change that adds functionality)
- [ ] Security fix (addresses a vulnerability or audit finding)
- [ ] Breaking change (fix or feature that would cause existing functionality to change)
- [ ] Documentation update
- [ ] New skill
- [ ] New tool policy
- [ ] Refactoring / code quality

## Changes Made

-

## How to Test

1.
2.
3.

## Checklist

### Code
- [ ] Tests pass (`uv run pytest -v`)
- [ ] Lint passes (`uv run ruff check dolios/`)
- [ ] No vendor/ code was modified
- [ ] Imports use `dolios.io` for YAML/JSON I/O
- [ ] Imports use `dolios.vendor_path` for vendor access
- [ ] No hardcoded API keys or secrets

### Security
- [ ] New network endpoints have policy entries in `policy_bridge.py`
- [ ] No `shell=True` in subprocess calls
- [ ] No `yaml.load()` (use `yaml.safe_load()` via `dolios.io`)
- [ ] Exception messages don't leak internal details to users

### Documentation
- [ ] CLAUDE.md updated if workflow rules changed
- [ ] SECURITY-AUDIT.md updated if security-relevant
