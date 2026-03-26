# AI-DLC Common Rule: Coding Standards

## Rule: COMMON-CODE-001 — Code Quality
- All code must pass ruff check and ruff format
- Type hints required on all function signatures
- No unused imports or variables
- Keep functions under 50 lines where practical
- Keep modules under 400 lines

## Rule: COMMON-CODE-002 — Testing
- Write tests alongside implementation, not after
- Minimum 80% code coverage target
- Test both happy path and error cases
- Use pytest fixtures for shared setup
- Mock external services, not internal modules

## Rule: COMMON-CODE-003 — Dependencies
- Use uv for dependency management
- Pin major versions in pyproject.toml
- No circular imports between modules
- Vendor repos accessed via import, never copied
