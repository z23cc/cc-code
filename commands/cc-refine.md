---
description: "Post-TDD quality hardening with measurable thresholds. TRIGGER: 'refine', 'harden', 'production ready', 'polish', 'quality check', '加固', '打磨', '上线前检查'. Use AFTER /tdd passes."
---

Activate the cc-refinement skill. Quality loop with thresholds:

1. **Coverage**: `pytest --cov --cov-fail-under=80` → add tests if below
2. **Complexity**: `radon cc src/ -a -nc` → split functions with CC > 10
3. **Type safety**: `mypy . --strict` → add annotations
4. **Performance**: Run perf tests → fix if over budget
5. **Security**: `bandit -r src/` → fix HIGH/CRITICAL findings
6. **Dependencies**: `pip-audit` → update vulnerable packages

Each dimension: MEASURE → COMPARE → FIX → RE-MEASURE → COMMIT or REVERT.
Stop when all thresholds met or diminishing returns.
