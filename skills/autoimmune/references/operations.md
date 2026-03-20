# Autoimmune — Operations Reference

## TSV Log Format

Every attempt → one row in `improvement-results.tsv`:

```
timestamp	iteration	mode	area	task_id	description	status	files_changed	diff_lines	duration_sec	notes
```

| Field | Values |
|-------|--------|
| mode | `code` (A) or `test` (B) |
| status | `KEPT`, `DISCARDED`, `SKIPPED` |
| notes | error details or skip reason |

Create if missing:
```bash
printf 'timestamp\titeration\tmode\tarea\ttask_id\tdescription\tstatus\tfiles_changed\tdiff_lines\tduration_sec\tnotes\n' > improvement-results.tsv
```

## improvement-program.md Template

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

## Failure Modes & Recovery

| Symptom | Action |
|---------|--------|
| Verify fails before starting | Fix baseline first |
| Same task fails 2x | Skip area, move on |
| 5 consecutive DISCARDED | STOP — loop is churning |
| Context getting large | STOP, start fresh session |
| No unchecked tasks | STOP — all done |

## Resuming a Session

1. Check `improvement-results.tsv` for last completed iteration
2. Check `improvement-program.md` for last checked-off item
3. `git log --oneline -5` to see branch state
4. Run verify command to confirm clean baseline
5. Resume from next unchecked item

## Session Summary Template

```
## Autoimmune Session Summary

| Metric | Value |
|--------|-------|
| Mode | A / B / Full |
| Iterations | X |
| Kept | Y (Z%) |
| Discarded | W |
| Skipped areas | [list or "none"] |
| Branch | auto/improve-XXXXXXXX-XXXX |
| Baseline | <SHA> |

### Changes Made
- improve(auth): add input validation on login endpoint
- improve(api): handle empty response from payment API
- fix(cache): resolve race condition in invalidation

### Next Steps
- Review: `git log --oneline <SHA>..HEAD`
- Remaining unchecked items in improvement-program.md
- Skipped areas need manual investigation
```
