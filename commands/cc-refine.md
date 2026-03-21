---
team: "refactor"
description: "Post-TDD quality hardening with measurable thresholds. TRIGGER: 'refine', 'harden', 'production ready', 'polish', 'quality check', '加固', '打磨', '上线前检查'. Use AFTER /tdd passes."
---

Activate the cc-refinement skill with **Refactor team** support.

## Default Team: researcher → refactor-cleaner → code-reviewer

### Step 1: Dispatch researcher
Measure all quality dimensions:
1. **Coverage**: `pytest --cov --cov-fail-under=80`
2. **Complexity**: `radon cc src/ -a -nc` (CC > 10 = BLOCK)
3. **Type safety**: `mypy . --strict`
4. **Security**: `bandit -r src/`
5. **Dependencies**: `pip-audit`

Write findings to `/tmp/cc-team-research.md` with pass/fail per dimension.

### Step 2: Dispatch refactor-cleaner
Fix failing dimensions (priority: security → types → coverage → complexity):
- Each fix: MEASURE → FIX → RE-MEASURE → COMMIT or REVERT
- Max 50 lines diff per fix

### Step 3: Dispatch code-reviewer
Review all refinement changes. Ensure no behavior change.

Stop when all thresholds met or diminishing returns.
