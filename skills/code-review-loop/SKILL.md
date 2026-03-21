---
name: code-review-loop
description: >
  Verdict-driven code review with auto-fix loop. Reviewer gives a structured
  verdict (SHIP/NEEDS_WORK/MAJOR_RETHINK), implementer fixes, re-review until SHIP.
  No manual confirmation between iterations.
  TRIGGER: 'review and fix', 'review loop', 'get this to SHIP quality', '审查循环'.
---

# Code Review Loop — Verdict Gates

## Concept

Instead of "here are some suggestions", the reviewer gives a **verdict**. The implementer fixes automatically. Re-review. Repeat until SHIP.

```
Implement → Review → Verdict?
                      ├─ SHIP → Done, commit
                      ├─ NEEDS_WORK → Auto-fix → Re-review (max 3 loops)
                      └─ MAJOR_RETHINK → STOP, surface to user
```

## Verdict Definitions

| Verdict | Meaning | Action |
|---------|---------|--------|
| **SHIP** | No CRITICAL/HIGH issues. Ready to merge. | Commit immediately |
| **NEEDS_WORK** | Fixable issues found. Clear remediation. | Auto-fix, re-review |
| **MAJOR_RETHINK** | Architectural problems. Fix unclear. | STOP, ask user |

## Review Output Format

The reviewer MUST output structured findings:

```markdown
## Review Verdict: NEEDS_WORK

### Issues (2 HIGH, 1 MEDIUM)

#### [HIGH] Missing input validation on /api/users POST
File: src/api/users.py:42
Fix: Add Pydantic model validation for request body

#### [HIGH] N+1 query in user list endpoint
File: src/api/users.py:67
Fix: Add selectinload(User.posts) to query

#### [MEDIUM] Inconsistent error response format
File: src/api/users.py:55
Fix: Use AppError with standard JSON structure
```

## The Loop Protocol

### Step 1: Review (dispatch reviewer agent)

```
Review the changes since BASE_COMMIT using:
  git diff <BASE_COMMIT>..HEAD

Output structured verdict with file:line for each issue.
```

### Step 2: Parse Verdict

- **SHIP** → proceed to commit
- **MAJOR_RETHINK** → stop, print issues, ask user
- **NEEDS_WORK** → continue to Step 3

### Step 3: Auto-Fix

For each issue in the review:
1. Read the file at the specified line
2. Apply the minimal fix described
3. Run verification (ruff + mypy + pytest)
4. If verification fails → revert that fix, move to next issue

### Step 4: Re-Review

- Re-run review on the new diff
- Max 3 review loops total
- If still NEEDS_WORK after 3 loops → surface to user

## Scoped Reviews (BASE_COMMIT)

Always track where the current work started:

```bash
BASE_COMMIT=$(git rev-parse HEAD)  # Before starting work
# ... implement ...
git diff $BASE_COMMIT..HEAD        # Review only THIS task's changes
```

This prevents reviewing old code that isn't part of the current task.

## Review Backends

| Backend | When to Use |
|---------|-------------|
| **python-reviewer agent** | Default for .py files |
| **security-reviewer agent** | Auth, input handling, API endpoints |
| **RepoPrompt context_builder** | Deep architectural review (if MCP available) |
| **Manual** | User explicitly wants to review themselves |

## Post-Autoimmune Review

After an autoimmune session completes, review all accumulated changes:

```bash
# Review everything since baseline
git diff $BASELINE_SHA..HEAD
```

Dispatch review loop scoped to the full autoimmune diff. This catches cross-task issues that per-task reviews miss (e.g., inconsistent naming, duplicated code across tasks).

## E2E Example

```
Implementing: "Add user deletion endpoint"

Loop 1 — Review:
  $ git diff $BASE_COMMIT..HEAD | wc -l  → 48 lines
  Dispatch python-reviewer agent...

  ## Review Verdict: NEEDS_WORK
  ### Issues (1 HIGH, 1 MEDIUM)
  #### [HIGH] No authorization check — any user can delete any user
  File: src/api/users.py:78
  Fix: Add ownership check before deletion
  #### [MEDIUM] Missing 404 when user not found
  File: src/api/users.py:75
  Fix: Return 404 instead of 500 on missing user

Loop 1 — Auto-Fix:
  → Read src/api/users.py:75-85
  → Add: if user.id != current_user.id: raise ForbiddenError()
  → Add: if not user: raise NotFoundError()
  → Run: ruff + mypy + pytest → PASS ✓
  → Commit: "fix(api): add auth check and 404 to user deletion"

Loop 2 — Re-Review:
  Dispatch python-reviewer agent...

  ## Review Verdict: SHIP ✓
  No CRITICAL/HIGH issues. Code is ready.

→ Done in 2 loops. Total: 1 NEEDS_WORK → 1 SHIP.
```

## Loop Metrics

| Metric | Target | Red Flag |
|--------|--------|----------|
| Loops to SHIP | ≤ 2 | 3 = surface to user |
| Issues per review | Trending down | Same issue type recurring = systematic problem |
| MAJOR_RETHINK rate | < 10% | High rate = plan quality issue |

## Related Skills

- **verification** — verify after each fix iteration
- **refinement** — quality metrics complement review findings
- **parallel-agents** — dispatch multiple reviewers for large changes
- **autoimmune** — run review loop after autoimmune session completes
- **pr-review command** — GitHub PR variant of this loop
- **feedback-loop** — record review patterns for routing improvement
