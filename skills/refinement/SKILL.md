---
name: refinement
description: >
  Post-implementation refinement loop — quality metrics, performance budgets,
  edge case hardening. Use AFTER initial implementation passes TDD.
  TRIGGER: 'refine', 'harden', 'polish', 'production-ready', '加固', '打磨'.
---

# Refinement Loop

After TDD green, before shipping. This is SPARC phase **R**.

## The Loop

```
FOR each quality dimension:
  1. MEASURE current state
  2. COMPARE against budget/threshold
  3. FIX if below threshold
  4. RE-MEASURE to confirm improvement
  5. COMMIT if improved, REVERT if not
```

## Quality Dimensions

### 1. Test Coverage

```bash
pytest --cov=src --cov-report=term-missing --cov-fail-under=80
```

| Threshold | Action |
|-----------|--------|
| < 60% | BLOCK — add tests for uncovered paths |
| 60-80% | WARNING — add tests for critical paths |
| > 80% | PASS |

### 2. Code Complexity

```bash
radon cc src/ -a -nc    # Cyclomatic complexity
radon mi src/ -nc       # Maintainability index
```

| Metric | Threshold | Action |
|--------|-----------|--------|
| Function CC > 10 | BLOCK | Split function |
| File CC avg > 5 | WARNING | Review structure |
| MI < 20 | BLOCK | Refactor for clarity |

### 3. Type Safety

```bash
mypy src/ --strict --no-error-summary | wc -l
```

Goal: 0 errors with `--strict`. Progressively enable strict flags.

### 4. Performance Budget

```python
# Define budgets in tests
def test_api_response_time():
    start = time.perf_counter()
    response = client.get("/api/users")
    elapsed = time.perf_counter() - start
    assert elapsed < 0.5, f"API too slow: {elapsed:.2f}s (budget: 0.5s)"

def test_memory_usage():
    import tracemalloc
    tracemalloc.start()
    process_large_dataset(data)
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    assert peak < 100 * 1024 * 1024, f"Peak memory {peak/1e6:.1f}MB (budget: 100MB)"
```

### 5. Security Hardening

```bash
bandit -r src/ -f json | python -c "import sys,json; d=json.load(sys.stdin); print(f'{len(d[\"results\"])} issues')"
pip-audit --strict
```

Goal: 0 HIGH/CRITICAL findings.

### 6. Dependency Hygiene

```bash
pip-audit                  # Known vulnerabilities
ruff check . --select I    # Import sorting
```

## Refinement Checklist

- [ ] Coverage ≥ 80% on new code
- [ ] No function with CC > 10
- [ ] mypy passes (ideally --strict)
- [ ] Performance tests within budget
- [ ] bandit: 0 HIGH/CRITICAL
- [ ] pip-audit: 0 known vulnerabilities
- [ ] No TODO without ticket reference
- [ ] Docstrings on all public functions

## When to Stop

- All thresholds met → ship it
- Diminishing returns (spending 2h to go from 82% to 85% coverage) → ship it
- Blocked by external dependency → log and ship

## Related Skills

- **tdd** — refinement happens AFTER TDD green
- **verification** — verify each refinement step
- **performance** — deep profiling when perf budget fails
- **security-review** — deep audit when bandit finds issues
