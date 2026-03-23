---
name: cc-autoimmune
description: "Autonomous improvement loop: scan→implement→verify→commit/revert. 4 modes: A(code), B(lint+type+test fix), C(full), D(scan). TRIGGER: 'autoimmune', 'auto improve', 'auto scan', 'auto fix loop', '自动改进', '自动扫描', '跑改进循环'. NOT FOR: one-off lint fix (use cc-fix), manual code review (use cc-code-review-loop). FLOWS INTO: cc-review (review autonomous changes)."
---

# Autoimmune — Autonomous Project Improvement Loop

## cc-flow Integration

Autoimmune is fully integrated with cc-flow task management. Use `cc-flow auto` for CLI-driven loops:

```bash

cc-flow auto scan     # Detect issues → create epic + tasks
cc-flow auto run      # Pick next task → implement → verify → done/revert
cc-flow auto test     # Auto-fix lint + type + test errors
cc-flow auto full     # scan → run → test (all three)
cc-flow auto status   # Session progress from task system
```

Each iteration automatically:
- `cc-flow next` → pick highest-priority ready task
- `cc-flow start <id>` → mark in_progress
- Implement (< 50 lines diff)
- Verify (auto-detect language tools)
- `cc-flow done <id>` on success / `cc-flow block <id>` on failure
- `cc-flow log` → record KEPT/DISCARDED
- `cc-flow progress` → visual progress bar

## Mode Selection

| User says | Mode | cc-flow command | Action |
|-----------|------|----------------|--------|
| "autoimmune" / "自动改进" | A | `cc-flow auto run` | Pick tasks, implement, verify |
| "autoimmune test" / "test loop" / "测试改进" | B | Lint + type + test fix loop |
| "autoimmune full" / "全量改进" | C | Mode D → A → B (scan, improve, fix) |
| "autoimmune scan" / "auto scan" / "自动扫描" | D | Scan codebase, generate tasks, then Mode A |

## Prerequisites

1. Verify command passes (clean baseline). Auto-detect:
   - Python (`pyproject.toml`): `ruff check . && mypy . && pytest`
   - JS/TS (`package.json`): `npm run lint && npm test`
   - Go (`go.mod`): `go vet ./... && go test ./...`
   - Rust (`Cargo.toml`): `cargo check && cargo test`
   - Custom: `make verify` or `make test`
2. Record baseline: `git rev-parse HEAD` → `BASELINE_SHA`
3. For Mode A: `improvement-program.md` or `.tasks/` must exist
4. For Mode D: no prerequisites (it generates the task list)

---

## Mode D: Auto-Scan (NEW)

Automatically discover improvement opportunities. Creates `improvement-program.md` or `.tasks/` entries.

### D1: LINT SCAN
```bash
ruff check . --output-format json 2>/dev/null | python3 -c "
import sys,json
issues = json.load(sys.stdin)
by_rule = {}
for i in issues:
    rule = i['code']
    by_rule.setdefault(rule, []).append(i)
for rule, items in sorted(by_rule.items(), key=lambda x: -len(x[1]))[:10]:
    print(f'- [ ] Fix {len(items)}x {rule}: {items[0][\"message\"]}')
"
```

### D2: TYPE SCAN
```bash
mypy . --no-error-summary 2>/dev/null | head -20 | while read line; do
    echo "- [ ] $line"
done
```

### D3: SECURITY SCAN
```bash
bandit -r src/ -f json 2>/dev/null | python3 -c "
import sys,json
data = json.load(sys.stdin)
for r in data.get('results', [])[:10]:
    print(f'- [ ] [{r[\"issue_severity\"]}] {r[\"issue_text\"]} ({r[\"filename\"]}:{r[\"line_number\"]})')
"
```

### D4: QUALITY SCAN
```bash
# Dead code
ruff check . --select F841,F811,F401 --output-format json 2>/dev/null

# Complexity
radon cc src/ -n C -j 2>/dev/null  # Only complex functions

# Missing type hints
mypy . --strict 2>/dev/null | grep "Function is missing" | head -10
```

### D5: GENERATE TASK LIST
Assemble findings into `improvement-program.md` by priority:
- **P1**: Security (bandit HIGH/CRITICAL)
- **P2**: Type errors (mypy failures)
- **P3**: Lint errors (ruff violations)
- **P4**: Quality (dead code, complexity, missing type hints)

If `.tasks/` exists, optionally create an epic + tasks via cc-flow instead:
```bash
cc-flow epic create --title "Autoimmune scan $(date +%Y-%m-%d)"
# For each finding:
cc-flow task create --epic <epic-id> --title "Fix: <description>"
```

Then proceed to **Mode A**.

---

## Mode A: Code Improvement Loop

Create branch `auto/improve-YYYYMMDD-HHMM`, then iterate:

### A1: SELECT
1. Re-read task source every iteration (never cache):
   - If `.tasks/` has an active autoimmune epic → use `cc-flow ready`
   - Else → read `improvement-program.md`, pick first unchecked `- [ ]`
2. Skip items in `skipped_areas`
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

### A5: VERIFY + REVIEW

Run the project's verification command:
Auto-detect project language and run appropriate verify command (see Prerequisites).

**PASS:**
1. `git add <specific files>` (NEVER `git add -A`)
2. `git commit`: `"improve(<area>): <description>"`
3. Mark task done:
   - `.tasks/`: `cc-flow done <task-id> --summary "..."`
   - `improvement-program.md`: mark `[x]`
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

## Mode B: Lint + Type + Test Fix Loop

Create branch `auto/testfix-YYYYMMDD-HHMM`, then iterate in 3 phases:

### Phase B1: Ruff Auto-fix
```bash
ruff check . --fix --unsafe-fixes
```
If changes were made → verify → commit `"fix(lint): auto-fix ruff violations"`

### Phase B2: Mypy Fix Loop
1. Run `mypy . --no-error-summary` — capture errors
2. Group by file
3. For each file: fix type errors (add annotations, fix incompatible types)
4. Verify after each file → commit or revert

### Phase B3: Pytest Fix Loop
1. Run `pytest --tb=short -q` — capture failures
2. Group by file/module
3. For each failure:
   - Read test code and code under test
   - Determine: test bug or code bug?
   - Fix minimally (< 30 lines diff)
   - Verify → commit or revert

### Churn Detection
Same as Mode A. 5 consecutive DISCARDED in any phase → STOP that phase, move to next.

---

## Mode C: Full Loop

1. Run **Mode D** (scan and generate tasks)
2. Run **Mode A** (implement improvements)
3. Run **Mode B** (fix remaining lint/type/test issues)
4. Print combined session summary

---

## Hard Rules

- NEVER use `git add -A` — always add specific files
- NEVER add new dependencies without user approval
- NEVER modify `.env*` files, generated code, or migration files
- ALWAYS verify before commit — no exceptions
- ALWAYS revert on failure — no partial commits
- ALWAYS `git diff --stat` before commit to confirm scope
- ALWAYS re-read task source each iteration (never cache)
- MAX 50 lines diff per improvement (Mode A)
- MAX 30 lines diff per fix (Mode B)

---

## Session Metrics

Track per-session and print at end:

| Metric | Formula | Threshold |
|--------|---------|-----------|
| Success rate | kept / (kept + discarded) | ≥ 50% to continue |
| Avg diff size | total lines changed / kept | Target < 30 |
| Churn ratio | discarded in last 5 / 5 | ≥ 0.8 → STOP |
| Consecutive fails | per area | ≥ 2 → skip area |
| Velocity | kept / elapsed hours | Track trend |

**Trend indicators:** ↗ improving (rate going up), → stable, ↘ declining (consider stopping)

## E2E Example

```bash
# 1. Scan
$ cc-flow auto scan
# → Created epic-3-scan-20260321 with 8 tasks (2×P1 security, 3×P2 type, 3×P3 lint)

# 2. Run
$ cc-flow auto run --epic epic-3-scan-20260321
# --- Iteration 1: epic-3-scan-20260321.1 — [P1] bandit HIGH: hardcoded password ---
# Team: security-fix (researcher → security-reviewer → build-fixer)
# → Replaced with env var. Diff: +3 -1. Verified. KEPT.

# --- Iteration 2: epic-3-scan-20260321.2 — [P1] bandit HIGH: SQL injection ---
# → Parameterized query. Diff: +5 -3. Verified. KEPT.

# --- Iteration 3: epic-3-scan-20260321.3 — [P2] mypy: missing return type ---
# → Added type annotation. Diff: +1 -1. Verified. KEPT.

# 3. Status
$ cc-flow auto status
# | Metric        | Value |
# | Tasks total   | 8     |
# | Done          | 3     |
# | Success rate  | 100%  |

# 4. Dashboard
$ cc-flow dashboard
# ╔══════════════════════════════════════════╗
# ║  Progress: ██████░░░░░░░░░░░░░░  38%   ║
# ║  ● 3 done  ◐ 0 active  ○ 5 todo       ║
# ╚══════════════════════════════════════════╝
```

## Related Skills

- **cc-task-tracking** — `.tasks/` integration for structured task management
- **cc-readiness-audit** — scan results can seed Mode D
- **cc-verification** — the verify step uses evidence-before-claims principle
- **cc-debugging** — when a fix attempt fails, switch to systematic debugging
- **cc-tdd** — Mode B follows: failing test → minimal fix → green
- **cc-code-review-loop** — for reviewing accumulated changes after the loop
- **cc-git-workflow** — commit messages follow conventional commits
