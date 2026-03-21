---
name: tdd
description: "Test-driven development workflow. Use when implementing any feature or bugfix — write the test first, watch it fail, write minimal code to pass."
---

# Test-Driven Development (TDD)

Write the test first. Watch it fail. Write minimal code to pass.

**Core principle:** If you didn't watch the test fail, you don't know if it tests the right thing.

## The Iron Law

```
NO PRODUCTION CODE WITHOUT A FAILING TEST FIRST
```

Write code before the test? Delete it. Start over. No exceptions.

## Red-Green-Refactor

### RED — Write Failing Test

Write one minimal test showing what should happen.

```python
def test_rejects_empty_email():
    result = validate_email("")
    assert result.is_valid is False
    assert result.error == "Email required"
```

Requirements: One behavior. Clear name. Real code (no mocks unless unavoidable).

### Verify RED — Watch It Fail

**MANDATORY. Never skip.**

```bash
pytest tests/path/test.py::test_name -v
```

Confirm: Test fails (not errors). Failure is expected. Fails because feature missing.

### GREEN — Minimal Code

Write simplest code to pass the test. Don't add features, don't refactor.

```python
def validate_email(email: str) -> ValidationResult:
    if not email or not email.strip():
        return ValidationResult(is_valid=False, error="Email required")
    return ValidationResult(is_valid=True, error=None)
```

### Verify GREEN — Watch It Pass

**MANDATORY.**

```bash
pytest tests/path/test.py -v
```

Confirm: Test passes. Other tests still pass.

### REFACTOR — Clean Up

After green only: Remove duplication, improve names, extract helpers. Keep tests green.

### Repeat

Next failing test for next behavior.

## Good Tests

| Quality | Good | Bad |
|---------|------|-----|
| **Minimal** | One thing. "and" in name? Split it. | `test_validates_and_saves_and_notifies` |
| **Clear** | Name describes behavior | `test1`, `test_it_works` |
| **Real** | Tests actual code | Tests mock behavior |

## Python Testing Quick Reference

```bash
pytest tests/ -v                                    # Run all
pytest tests/test_file.py::test_name -v            # Run one
pytest --cov=mypackage --cov-report=term-missing   # Coverage
pytest -x                                           # Stop on first failure
pytest --lf                                         # Re-run last failed
pytest -k "test_user"                               # Pattern match
```

## Common Rationalizations

| Excuse | Reality |
|--------|---------|
| "Too simple to test" | Simple code breaks. Test takes 30 seconds. |
| "I'll test after" | Tests passing immediately prove nothing. |
| "TDD will slow me down" | TDD is faster than debugging. |
| "Just this once" | That's rationalization. |

## E2E Example

```
Feature: "Add email validation to user registration"

Cycle 1 — Happy path:
  RED:   def test_valid_email_accepted():
             assert validate_email("user@example.com").is_valid is True
  RUN:   $ pytest tests/test_email.py::test_valid_email_accepted -v
         → FAILED (NameError: validate_email not defined) ✓ expected
  GREEN: def validate_email(email): return ValidationResult(is_valid=True)
  RUN:   $ pytest → PASS ✓

Cycle 2 — Empty input:
  RED:   def test_empty_email_rejected():
             result = validate_email("")
             assert result.is_valid is False
             assert result.error == "Email required"
  RUN:   → FAILED (returns is_valid=True) ✓ expected
  GREEN: if not email: return ValidationResult(is_valid=False, error="Email required")
  RUN:   → 2/2 PASS ✓

Cycle 3 — Invalid format:
  RED:   def test_invalid_format_rejected():
             assert validate_email("not-an-email").is_valid is False
  RUN:   → FAILED ✓
  GREEN: if "@" not in email: return ValidationResult(is_valid=False, error="Invalid format")
  RUN:   → 3/3 PASS ✓

REFACTOR: Extract regex pattern, add parametrize for edge cases
  RUN:   → 3/3 PASS ✓
  $ pytest --cov=src --cov-report=term-missing → 100% on validate_email
```

## Metrics

| Metric | Target | How to Check |
|--------|--------|-------------|
| Coverage on new code | ≥ 80% | `pytest --cov --cov-fail-under=80` |
| Tests per function | ≥ 2 (happy + error) | Manual count |
| Red before green | 100% | Self-discipline — never skip |
| Test run time | < 5s per test | `pytest --durations=5` |

## Related Skills

- **verification** — use before claiming TDD cycle is complete
- **python-testing** — pytest patterns, fixtures, parametrization
- **debugging** — when tests fail unexpectedly, switch to systematic debugging
- **plan** — each plan task follows Red-Green-Refactor

## Verification Checklist

- [ ] Every new function has a test
- [ ] Watched each test fail before implementing
- [ ] Each test failed for expected reason
- [ ] Wrote minimal code to pass
- [ ] All tests pass
- [ ] Edge cases and errors covered
- [ ] 80%+ coverage on new code
