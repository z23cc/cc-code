---
name: verification
description: "Use before claiming work is complete — requires running verification commands and confirming output before any success claims. Evidence before assertions."
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
