# Autoimmune — Operations Reference

## TSV Log Format

Every attempt → one row in `improvement-results.tsv`:

```
timestamp	iteration	mode	area	task_id	description	status	files_changed	diff_lines	duration_sec	notes
```

| Field | Values |
|-------|--------|
| mode | `code` (A), `lint` (B1), `type` (B2), `test` (B3), `scan` (D) |
| status | `KEPT`, `DISCARDED`, `SKIPPED`, `AUTOFIX` |
| notes | error details or skip reason |

Create if missing:
```bash
printf 'timestamp\titeration\tmode\tarea\ttask_id\tdescription\tstatus\tfiles_changed\tdiff_lines\tduration_sec\tnotes\n' > improvement-results.tsv
```

## Task Sources

### Option 1: improvement-program.md (flat list)

```markdown
# Improvement Program

## Rules
- Maximum 50 lines diff per task
- No new dependencies
- No breaking API changes

## Areas to AVOID
- Database migrations
- Generated code
- Third-party integrations

---

## P1 — Critical (security, crashes)
- [ ] Fix SQL injection in user search endpoint
- [ ] Add input validation on file upload

## P2 — High (bugs, correctness)
- [ ] Handle empty response from payment API
- [ ] Fix race condition in cache invalidation

## P3 — Medium (code quality)
- [ ] Extract duplicate validation logic into shared module
- [ ] Replace print statements with structured logging
- [ ] Add type hints to public API functions

## P4 — Low (polish)
- [ ] Improve error messages in CLI
- [ ] Add docstrings to exported functions
```

### Option 2: .tasks/ (structured, with taskctl)

```bash
TASKCTL="python3 ${CLAUDE_PLUGIN_ROOT}/scripts/taskctl.py"

# Mode D auto-generates an epic:
$TASKCTL epic create --title "Autoimmune scan 2026-03-21"

# With tasks from scan results:
$TASKCTL task create --epic epic-N-autoimmune-scan --title "[P1] Fix bandit HIGH: hardcoded secret in config.py:42"
$TASKCTL task create --epic epic-N-autoimmune-scan --title "[P2] Fix mypy: missing return type on process_order"
$TASKCTL task create --epic epic-N-autoimmune-scan --title "[P3] Fix ruff F401: unused import os in utils.py"

# During Mode A, the loop uses:
$TASKCTL ready --epic epic-N-autoimmune-scan  # Find next task
$TASKCTL start <task-id>                       # Claim it
$TASKCTL done <task-id> --summary "..."        # Mark done after commit
```

Use `.tasks/` when:
- Running multiple autoimmune sessions across days
- Tracking which tasks were addressed vs skipped
- Dependencies between improvements exist

Use `improvement-program.md` when:
- Single session, flat task list
- Quick one-off improvement run

## Failure Modes & Recovery

| Symptom | Action |
|---------|--------|
| Verify fails before starting | Fix baseline first |
| Same task fails 2x | Skip area, move on |
| 5 consecutive DISCARDED | STOP — loop is churning |
| Context getting large | STOP, start fresh session |
| No unchecked tasks | STOP — all done |
| ruff --fix breaks code | Revert, log DISCARDED, continue to mypy phase |
| Mode D finds 100+ issues | Auto-prioritize P1/P2 only for first run |

## Resuming a Session

1. Check `improvement-results.tsv` for last completed iteration
2. Check task source:
   - `.tasks/`: `$TASKCTL progress` → see what's left
   - `improvement-program.md`: look for last `[x]`
3. `git log --oneline -5` to see branch state
4. Run verify command to confirm clean baseline
5. Resume from next unchecked item

## Session Summary Template

```
## Autoimmune Session Summary

| Metric | Value |
|--------|-------|
| Mode | A / B / C / D |
| Scan findings (D) | N issues across M categories |
| Iterations (code) | X |
| Kept | Y (Z%) |
| Discarded | W |
| Auto-fixed (lint) | L |
| Skipped areas | [list or "none"] |
| Branch | auto/improve-XXXXXXXX-XXXX |
| Baseline | <SHA> |

### Changes Made
- improve(auth): add input validation on login endpoint
- improve(api): handle empty response from payment API
- fix(lint): auto-fix 12 ruff violations
- fix(types): add return type annotations to 5 functions

### Metrics Before/After
| Metric | Before | After |
|--------|--------|-------|
| ruff errors | 23 | 3 |
| mypy errors | 15 | 7 |
| pytest failures | 2 | 0 |
| bandit HIGH | 1 | 0 |

### Next Steps
- Review: `git log --oneline <SHA>..HEAD`
- Remaining tasks: `$TASKCTL progress` or check improvement-program.md
- Skipped areas need manual investigation
```
