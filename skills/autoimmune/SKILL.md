---
name: autoimmune
description: >
  Autonomous project improvement loop.
  Mode A (code): pick task from improvement-program.md, implement, verify, commit or revert.
  Mode B (test): run pytest suite, discover failures, auto-fix, re-verify.
  Mode C (full): Mode A then Mode B.
  Triggers: "autoimmune", "auto improve", "自动改进", "跑改进循环",
  "autoimmune test", "test loop", "测试改进",
  "autoimmune full", "全量改进".
  User may append a focus topic (e.g. "autoimmune 数据库层") to scope Mode A.
---

# Autoimmune — Autonomous Project Improvement Loop

## Mode Selection

| User says | Mode | Action |
|-----------|------|--------|
| "autoimmune" / "auto improve" / "自动改进" | A | Code quality loop |
| "autoimmune test" / "test loop" / "测试改进" | B | Test-driven fix loop |
| "autoimmune full" / "全量改进" | A→B | Code first, then test |

## Prerequisites

1. `improvement-program.md` exists in project root (if not, tell user to create one)
2. `improvement-results.tsv` exists (if not, create — see [references/operations.md](references/operations.md))
3. Verify command passes (clean baseline): `ruff check . && mypy . && pytest`
4. Record baseline: `git rev-parse HEAD` → `BASELINE_SHA`

---

## Mode A: Code Improvement Loop

Create branch `auto/improve-YYYYMMDD-HHMM`, then iterate:

### A1: SELECT
1. Re-read `improvement-program.md` every iteration (never cache)
2. Pick first unchecked `- [ ]` from highest-priority section not in `skipped_areas`
3. If user specified focus topic → only pick from matching section
4. If all done → STOP

### A2: PLAN
1. Research relevant code (read files, grep patterns)
2. Define acceptance criteria (what must be true after fix)
3. If > 50 lines diff → split, do first sub-task only
4. Estimate risk: LOW (formatting, naming) / MED (logic change) / HIGH (architecture)

### A3: IMPLEMENT
Target < 50 lines diff. Follow project's coding standards and rules.

### A4: SELF-CHECK
1. `git diff --stat` — only intended files changed?
2. `git diff` — no debug prints, no `.env` changes, no accidental deletions?
3. Acceptance criteria met?
4. Fail → revert, log DISCARDED, continue

### A5: VERIFY

Run the project's verification command:
- Python default: `ruff check . && mypy . && pytest`
- Or project-specific: `make verify` / `make test` / custom

**PASS:**
1. `git add <specific files>` (NEVER `git add -A`)
2. `git commit`: `"improve(<area>): <description>"`
3. Mark `[x]` in `improvement-program.md`, commit that too
4. Append KEPT to `improvement-results.tsv`
5. Reset `consecutive_fail[area] = 0`

**FAIL:**
1. Capture first error
2. `git checkout -- . && git clean -fd`
3. Append DISCARDED to `improvement-results.tsv`
4. `consecutive_fail[area] += 1`; if >= 2 → skip area

### A6: CHURN DETECTION (every 5 iterations)
- Last 5 all DISCARDED → STOP
- kept/iteration < 0.3 after 10+ iterations → STOP
- Print: `"Iteration X: Y kept, Z discarded"`

Continue immediately to next iteration.

---

## Mode B: Test-Driven Fix Loop

Create branch `auto/testfix-YYYYMMDD-HHMM`, then iterate:

### B1: DISCOVER
1. Run `pytest --tb=short -q` — capture all failures
2. Group failures by file/module
3. If all pass → STOP (nothing to fix)

### B2: SELECT
1. Pick the first failing test
2. Read the test code and the code under test
3. Determine: is this a test bug or a code bug?

### B3: FIX
1. If test bug → fix the test
2. If code bug → fix the code (minimal change)
3. Target < 30 lines diff

### B4: VERIFY
Run `pytest` on the specific test file first, then full suite.

**PASS:** commit with `"fix(<module>): <what was wrong>"`
**FAIL:** revert, log DISCARDED, move to next failure

### B5: CHURN DETECTION
Same rules as Mode A. 5 consecutive DISCARDED → STOP.

---

## Hard Rules

- NEVER use `git add -A` — always add specific files
- NEVER add new dependencies without user approval
- NEVER modify `.env*` files, generated code, or migration files
- ALWAYS verify before commit — no exceptions
- ALWAYS revert on failure — no partial commits
- ALWAYS `git diff --stat` before commit to confirm scope
- ALWAYS re-read `improvement-program.md` each iteration (never cache)

---

## When Done

Print session summary and next steps — see [references/operations.md](references/operations.md).

## Related Skills

- **verification** — the verify step uses this skill's evidence-before-claims principle
- **debugging** — when a fix attempt fails, switch to systematic debugging
- **tdd** — Mode B follows the TDD principle: failing test → minimal fix → green
- **git-workflow** — commit messages follow conventional commits
