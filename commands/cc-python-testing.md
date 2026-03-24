---
description: >
  Python testing with pytest — TDD, fixtures, parametrization, mocking, async testing, and coverage.
  TRIGGER: 'pytest', 'python test', 'TDD', 'coverage', 'mock', 'fixture', 'write tests'.
  FLOWS INTO: cc-verification, cc-refinement.
---

Activate the cc-python-testing skill.

## Covers

- TDD cycle (RED -> GREEN -> REFACTOR)
- pytest fixtures and conftest.py
- Parametrization with ids
- Mocking with unittest.mock (patch, side_effect)
- Async testing (pytest-asyncio)
- Test pyramid (70% unit, 20% integration, 10% E2E)
- Edge case matrix (boundaries, null/None, concurrency, error paths, security)

## Quick Reference

```bash
pytest                                      # All tests
pytest tests/test_file.py::test_name -v    # One test
pytest --cov=mypackage --cov-report=html   # Coverage
pytest -x                                   # Stop on first fail
pytest --lf                                 # Re-run last failed
```
