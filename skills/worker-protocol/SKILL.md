---
name: worker-protocol
description: >
  Fresh-context worker subagent protocol for task isolation. Each task gets
  a dedicated agent with re-anchor, implement, verify, commit cycle.
  Prevents context bleed between tasks.
  TRIGGER: 'execute plan', 'work through tasks', 'implement the plan', '执行计划'.
---

# Worker Protocol — Task Isolation

## Problem

When implementing a multi-task plan in one session, context accumulates:
- Earlier task's code patterns bleed into later tasks
- Errors from task 2 pollute context for task 3
- Context window fills up, quality degrades

## Solution: One Worker Per Task

```
Orchestrator (you)
  ├─ Worker Agent → Task 1 (fresh context)
  ├─ Worker Agent → Task 2 (fresh context)
  └─ Worker Agent → Task 3 (fresh context)
```

Each worker:
1. Gets a **clean context** with only what it needs
2. **Re-anchors** by reading the spec and current code state
3. Implements **one task only**
4. Commits or reverts
5. Reports back to orchestrator

## Worker Prompt Template

```markdown
## Task: [Task Title]

### Context
- Spec: [path to spec or inline requirements]
- Plan step: [which step from the plan]
- BASE_COMMIT: [sha — for scoped review later]

### Files to Touch
- Modify: src/api/users.py
- Create: tests/test_users.py

### Acceptance Criteria
- [ ] User creation endpoint returns 201
- [ ] Input validation rejects invalid email
- [ ] Unit tests cover happy path and error cases

### Constraints
- Do NOT modify files outside the listed scope
- Follow TDD: write test first, then implement
- Max 50 lines diff
- Run `ruff check . && mypy . && pytest` before committing

### When Done
- Commit with: `feat(users): add creation endpoint`
- Report: what was done, files changed, tests added
```

## Orchestrator Protocol

### Before Dispatching Workers

```bash
BASE_COMMIT=$(git rev-parse HEAD)
```

### For Each Task

1. **Dispatch** worker agent with the template above
2. **Wait** for worker to complete
3. **Verify** worker's commit: `git log --oneline -1` + `git diff --stat $BASE_COMMIT..HEAD`
4. **Review** if needed: dispatch review agent scoped to `$BASE_COMMIT..HEAD`
5. **Update** BASE_COMMIT for next task: `BASE_COMMIT=$(git rev-parse HEAD)`

### Sequential vs Parallel

| Situation | Strategy |
|-----------|----------|
| Tasks have dependencies | Sequential workers |
| Tasks touch different files | **Parallel workers** (each in worktree) |
| Tasks share models/schemas | Sequential (earlier task may change interface) |

## Re-Anchor Phase

Every worker MUST start by reading current state:

```
1. Read the spec/plan for this specific task
2. git log --oneline -3  (what just happened)
3. Read files I'll modify  (current state, not cached)
4. Check git status  (clean working tree?)
```

This prevents working against stale assumptions.

## Failure Handling

| Worker Reports | Orchestrator Action |
|----------------|-------------------|
| Task completed, tests pass | Accept, move to next task |
| Task completed, tests fail | Dispatch build-fixer agent |
| Task partially done, stuck | Log progress, try different approach |
| Task impossible (missing dep) | Skip, log, continue with next |

## Integration with Autoimmune

Autoimmune Mode A can use worker-protocol for each task:

```
Autoimmune Orchestrator
  ├─ SELECT task from .tasks/ or improvement-program.md
  ├─ Worker Agent (fresh context):
  │   ├─ Re-anchor: read task spec + current code
  │   ├─ Implement: < 50 lines diff
  │   ├─ Self-check: git diff --stat
  │   └─ Verify: ruff + mypy + pytest
  ├─ PASS → commit + mark done
  └─ FAIL → revert + mark discarded
```

This is useful when autoimmune tasks are complex enough to benefit from isolated context per task.

## Integration with Task Tracking

```bash
TASKCTL="python3 ${CLAUDE_PLUGIN_ROOT}/scripts/taskctl.py"

# Before dispatching worker:
TASK_ID=$($TASKCTL ready --epic epic-1 | python3 -c "import sys,json; r=json.load(sys.stdin)['ready']; print(r[0]['id'] if r else '')")
$TASKCTL start $TASK_ID

# Worker receives task spec:
$TASKCTL show $TASK_ID  # Read spec for worker prompt

# After worker completes:
$TASKCTL done $TASK_ID --summary "Implemented X"
```

## Related Skills

- **plan** — the plan that workers execute
- **task-tracking** — workers consume tasks from .tasks/ via taskctl
- **parallel-agents** — parallel worker dispatch patterns
- **autoimmune** — similar loop but for improvement tasks, not plan execution
- **code-review-loop** — review each worker's output with verdict gates
