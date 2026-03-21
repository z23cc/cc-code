---
team: "refactor"
description: "Post-TDD quality hardening with measurable thresholds. TRIGGER: 'refine', 'harden', 'production ready', 'polish', 'quality check', '加固', '打磨', '上线前检查'. Use AFTER /tdd passes."
---

Activate the cc-refinement skill with **parallel measurement + sequential fix**.

## Team: PARALLEL(measure) → refactor-cleaner → code-reviewer

### Step 1: Measure ALL dimensions in PARALLEL

**IMPORTANT: Run all measurement commands simultaneously — they are independent read-only checks.**

Launch in parallel (each via separate Bash tool call in one message):
- `pytest --cov --cov-fail-under=80` — Coverage
- `radon cc src/ -a -nc` — Complexity
- `mypy . --strict 2>&1 | head -20` — Type safety
- `bandit -r src/ -f json -q 2>&1 | head -10` — Security
- `pip-audit 2>&1 | head -10` — Dependencies

Collect results, determine which dimensions fail thresholds.

### Step 2: Fix failing dimensions (sequential — each fix may affect others)
Dispatch **refactor-cleaner**:
- Fix in priority order: security → types → coverage → complexity
- Each fix: MEASURE → FIX → RE-MEASURE → COMMIT or REVERT
- Max 50 lines diff per fix

### Step 3: Dispatch code-reviewer (sequential — needs fix results)
Review all refinement changes. Ensure no behavior change.

Stop when all thresholds met or diminishing returns.
