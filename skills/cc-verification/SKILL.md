---
name: cc-verification
description: >
  Run verification commands and confirm output before any completion claims. Evidence before assertions.
  TRIGGER: 'verify', 'check', 'done?', 'complete?', '验证', '检查完成'.
  FLOWS INTO: cc-refinement, cc-commit.
---

# Verification Before Completion

Claiming work is complete without verification is dishonesty, not efficiency.

**Core principle:** Evidence before claims, always.

## The Iron Law

```
NO COMPLETION CLAIMS WITHOUT FRESH VERIFICATION EVIDENCE
```

If you haven't run the verification command in this message, you cannot claim it passes.

## The Gate Function

```
BEFORE claiming any status:

1. IDENTIFY: What command proves this claim?
2. RUN: Execute the FULL command (fresh, complete)
3. READ: Full output, check exit code, count failures
4. VERIFY: Does output confirm the claim?
   - If NO: State actual status with evidence
   - If YES: State claim WITH evidence
5. ONLY THEN: Make the claim
```

## Common Failures

| Claim | Requires | Not Sufficient |
|-------|----------|----------------|
| Tests pass | `pytest` output: 0 failures | Previous run, "should pass" |
| Linter clean | `ruff check` output: 0 errors | Partial check |
| Build succeeds | `python -m py_compile`: exit 0 | "Looks correct" |
| Bug fixed | Reproduce original symptom: passes | Code changed |
| Types clean | `mypy .`: 0 errors | Linter passing |

## Red Flags — STOP

- Using "should", "probably", "seems to"
- Expressing satisfaction before verification ("Great!", "Done!")
- About to commit without verification
- Trusting agent success reports
- Thinking "just this once"

## Key Patterns

**Tests:**
```
OK: [Run pytest] [See: 34/34 pass] "All tests pass"
BAD: "Should pass now" / "Looks correct"
```

**Build:**
```
OK: [Run build] [See: exit 0] "Build passes"
BAD: "Linter passed" (linter != build)
```

**Requirements:**
```
OK: Re-read plan -> checklist -> verify each -> report gaps or completion
BAD: "Tests pass, phase complete"
```

## When To Apply

**ALWAYS before:**
- ANY success/completion claim
- Committing, PR creation, task completion
- Moving to next task
- Delegating to agents

**No shortcuts for verification.** Run the command. Read the output. THEN claim the result.

## E2E Example

```
Claim: "Tests pass after fixing the auth bug"

1. IDENTIFY: pytest is the verification command
2. RUN:
   $ pytest tests/ -v
   ========================= test session starts ==========================
   tests/test_auth.py::test_login_valid ✓
   tests/test_auth.py::test_login_invalid ✓
   tests/test_auth.py::test_token_refresh ✓
   tests/test_users.py::test_create_user ✓
   ========================= 4 passed in 1.23s ============================

3. READ: 4 passed, 0 failed, exit code 0
4. VERIFY: Output confirms "4 passed" — matches claim ✓
5. CLAIM: "All 4 tests pass (pytest output: 4 passed in 1.23s)"

WRONG way: "I fixed the bug, tests should pass now" ✗
RIGHT way: "pytest shows 4/4 pass (ran just now)" ✓
```

## Verification Commands by Language

| Language | Lint | Types | Tests | Build |
|----------|------|-------|-------|-------|
| Python | `ruff check .` | `mypy .` | `pytest -v` | `python -m py_compile` |
| JS/TS | `eslint .` | `tsc --noEmit` | `npm test` | `npm run build` |
| Go | `golangci-lint run` | built-in | `go test ./...` | `go build ./...` |
| Rust | `cargo clippy` | built-in | `cargo test` | `cargo build` |

**Full verification = ALL four pass.** Partial verification (e.g., only lint) is not sufficient for completion claims.


## On Completion

When done:
```bash
cc-flow skill ctx save cc-verification --data '{"all_pass": true, "steps": [...]}'
cc-flow skill next
```

## Related Skills

- **cc-tdd** — TDD requires verification at each Red/Green step
- **cc-refinement** — quality loop uses verification at each metric check
- **cc-debugging** — verify fix before claiming success
- **cc-autoimmune** — every commit requires verification pass
