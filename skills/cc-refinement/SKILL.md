---
name: cc-refinement
description: >
  Post-implementation refinement loop — quality metrics, performance budgets,
  edge case hardening. Use AFTER initial implementation passes TDD.
  TRIGGER: 'refine', 'harden', 'polish', 'production-ready', 'edge cases',
  '加固', '打磨', '上线前优化'.
  NOT FOR: initial implementation — use cc-tdd or cc-work first.
  FLOWS INTO: cc-review, cc-commit.
  DEPENDS ON: cc-tdd.
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
# Auto-detect:
# Python: pytest --cov=src --cov-fail-under=80
# JS/TS:  npx jest --coverage --coverageThreshold='{"global":{"lines":80}}'
# Go:     go test -cover ./... | grep -v "100.0%"
# Rust:   cargo llvm-cov --fail-under-lines 80
```

| Threshold | Action |
|-----------|--------|
| < 60% | BLOCK — add tests for uncovered paths |
| 60-80% | WARNING — add tests for critical paths |
| > 80% | PASS |

### 2. Code Complexity

```bash
# Python: radon cc src/ -a -nc
# JS/TS:  npx eslint . --rule 'complexity: [warn, 10]'
# Go:     gocyclo -over 10 .
# Rust:   cargo clippy -- -W clippy::cognitive_complexity
```

| Metric | Threshold | Action |
|--------|-----------|--------|
| Function CC > 10 | BLOCK | Split function |
| File CC avg > 5 | WARNING | Review structure |
| MI < 20 | BLOCK | Refactor for clarity |

### 3. Type Safety

```bash
# Python: mypy . --strict
# JS/TS:  npx tsc --noEmit --strict
# Go:     go vet ./... (built-in)
# Rust:   cargo check (built-in, strict by default)
```

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

## Automated Refinement via Autoimmune

`/autoimmune test` (Mode B) automates parts of this refinement loop:
- Phase B1: `ruff check --fix` → automatic lint fixes
- Phase B2: mypy error loop → type annotation fixes
- Phase B3: pytest fix loop → test failure fixes

Use `/refine` for **manual, threshold-driven** quality hardening.
Use `/autoimmune test` for **automated, fix-what-you-can** passes.

## E2E Example

```
Feature just passed TDD. Now refine:

Dimension 1 — Coverage:
  $ pytest --cov=src/auth --cov-report=term-missing
  → 73% (BELOW 80% threshold)
  → Missing: src/auth/token.py lines 45-52 (error handling branch)
  → Write test_token_expired_raises_error, test_token_malformed
  $ pytest --cov=src/auth → 87% ✓ PASS
  → Commit: "test(auth): add token error path tests"

Dimension 2 — Complexity:
  $ radon cc src/auth/ -a -nc
  → src/auth/middleware.py: authenticate — CC=12 (ABOVE 10 threshold)
  → Extract _validate_token() and _check_permissions() from authenticate()
  $ radon cc src/auth/ -a -nc → authenticate CC=4 ✓ PASS
  → Commit: "refactor(auth): extract token validation for lower complexity"

Dimension 3 — Security:
  $ bandit -r src/auth/ -f json → 0 issues ✓ PASS

Dimension 4 — Types:
  $ mypy src/auth/ → 0 errors ✓ PASS

Result: All thresholds met → ship it.
```

## Refinement Priority Order

Always fix in this order (highest risk first):
1. **Security** — 0 HIGH/CRITICAL (bandit, pip-audit)
2. **Types** — 0 mypy errors (prevent runtime crashes)
3. **Coverage** — ≥ 80% (catch regressions)
4. **Complexity** — CC ≤ 10 per function (maintainability)
5. **Performance** — within budget (user experience)
6. **Dependencies** — no known vulnerabilities


## On Completion

When done:
```bash
cc-flow skill ctx save cc-refinement --data '{"quality_score": 90, "hardened": true}'
cc-flow skill next
```

## Related Skills

- **cc-tdd** — refinement happens AFTER TDD green
- **cc-verification** — verify each refinement step
- **cc-performance** — deep profiling when perf budget fails
- **cc-security-review** — deep audit when bandit finds issues
- **cc-autoimmune** — Mode B automates lint/type/test fixing
