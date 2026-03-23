---
name: cc-epic-review
description: "Epic completion review — verify all tasks fully implement the epic spec. Catches missing requirements, partial impl, scope drift. TRIGGER: 'epic review', 'completion review', 'verify epic', 'did we finish', 'acceptance review', '验收', '完成审查', '检查是否完成', '需求覆盖'. NOT FOR: code quality review (use cc-code-review-loop), PR review (use cc-review). DEPENDS ON: cc-work (all tasks done before epic review)."
---

# Epic Review — Completion Verification

## Purpose

This is NOT a code quality review (cc-code-review-loop handles that).
This verifies that the **epic spec requirements** are fully satisfied by the
combined implementation across all tasks.

## What It Catches

| Issue | Example |
|-------|---------|
| Missing requirement | Spec says "email notifications" but no task implemented it |
| Partial implementation | Spec says "CRUD for users" but only Create/Read done |
| Scope drift | Tasks added features not in spec |
| Missing docs | Spec says "update API docs" but docs unchanged |
| Missing tests | Spec says "90% coverage" but tests only cover happy path |

## Workflow

### Step 1: Verify All Tasks Done

```bash
CCFLOW="python3 ${CLAUDE_PLUGIN_ROOT}/scripts/cc-flow.py"

PROGRESS=$($CCFLOW progress --epic $EPIC_ID --json)
# Must be 100% — if not, show remaining tasks and stop
```

### Step 2: Extract Requirements from Spec

Read the epic spec and extract ALL explicit requirements:

```bash
SPEC=$($CCFLOW show $EPIC_ID)
```

Parse the spec for:
- **Acceptance criteria** (checkboxes)
- **API contracts** (endpoints, methods, request/response shapes)
- **Data models** (fields, relationships, constraints)
- **Business rules** (validation, authorization, error handling)
- **Non-functional requirements** (performance, security, docs)

Build a requirements checklist:

```markdown
## Requirements Extracted from Epic Spec

1. [ ] User can register with email/password
2. [ ] Registration validates email format
3. [ ] Duplicate email returns 409
4. [ ] Password hashed with bcrypt
5. [ ] JWT token returned on success
6. [ ] API docs updated
7. [ ] Unit tests for all endpoints
```

### Step 3: Verify Each Requirement

For each requirement, check the actual implementation:

1. **Read the relevant code** — find where it's implemented
2. **Read the tests** — verify tests cover this requirement
3. **Check git log** — which task/commit implemented it

Mark each requirement:

| Status | Meaning |
|--------|---------|
| **DONE** | Fully implemented and tested |
| **PARTIAL** | Implemented but incomplete (e.g., missing edge case) |
| **MISSING** | Not implemented at all |
| **DRIFT** | Implemented differently than spec describes |

### Step 4: Verdict

```markdown
## Epic Review Verdict

### SHIP ✓
All 7 requirements verified. No gaps found.

### — OR —

### NEEDS_WORK
5/7 requirements verified. 2 gaps:

**MISSING**: Requirement 6 — API docs not updated
  → Fix: Update `docs/api.md` with new endpoints

**PARTIAL**: Requirement 3 — Duplicate email returns 500 not 409
  → Fix: Add IntegrityError handler in `views.py`
```

### Step 5: Fix Loop (if NEEDS_WORK)

If gaps found:

1. Create tasks for missing requirements: `$CCFLOW task create --epic $EPIC_ID --title "Fix: ..."`
2. Or fix directly if small (< 20 lines)
3. Re-verify after fix
4. Repeat until all requirements DONE

### Step 6: Record Review

```bash
$CCFLOW task comment $EPIC_ID --text "Epic review: SHIP — all requirements verified"
```

## Integration with /cc-work

When `/cc-work` completes all tasks in an epic:

```
/cc-work epic-1
  → All 5 tasks done ✓
  → Running epic review...
  → 4/5 requirements verified
  → NEEDS_WORK: missing error handling for edge case X
  → Creating fix task...
  → Fix task done ✓
  → Re-review: 5/5 requirements verified
  → SHIP ✓
```

## Review Depth

| Level | What's checked | When to use |
|-------|---------------|-------------|
| **Quick** | Acceptance criteria checkboxes only | Small epics (< 3 tasks) |
| **Standard** | All explicit requirements + tests | Default |
| **Deep** | Requirements + code paths + edge cases + docs | Critical features |

## Related Skills

- **cc-work** — the execution pipeline that triggers epic review
- **cc-code-review-loop** — per-task code quality review (different concern)
- **cc-plan** — creates the epic spec that this skill verifies against
- **cc-task-tracking** — task lifecycle and progress tracking
