---
team: "refactor"
agent: "refactor-cleaner"
description: "Simplify and clean up code. TRIGGER: 'clean up', 'simplify', 'remove dead code', 'refactor', '简化', '清理代码'. NOT for: build errors (/fix), new features (/tdd). FLOWS INTO: cc-review (review the refactored code)."
---

Code simplification with **Refactor team** dispatch.

## Default Team: researcher → refactor-cleaner → code-reviewer

### Step 1: Dispatch researcher
- Map all usages and dependents of target code
- Identify dead code, unused imports, duplicates
- Write findings to `/tmp/cc-team-research.md`

### Step 2: Dispatch refactor-cleaner
- Read research findings
- Simplify logic, remove dead code, apply idioms
- Run tests after each change (no regressions)
- Max 50 lines diff per change

### Step 3: Dispatch code-reviewer
- Verify behavior preserved
- Verdict: SHIP / NEEDS_WORK
