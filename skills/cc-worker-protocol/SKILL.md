---
name: cc-worker-protocol
description: >
  Fresh-context worker subagent protocol for task isolation. Each task gets
  a dedicated agent with re-anchor, implement, verify, commit cycle.
  Prevents context bleed between tasks.
  TRIGGER: 'execute plan', 'work through tasks', 'implement the plan', 'worker isolation',
  '执行计划', '任务隔离', '工作协议'.
  NOT FOR: single quick tasks — just implement directly.
  USED BY: cc-work (task execution), cc-ralph (autonomous harness).
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
| Tasks touch different files | **Parallel workers** (each in worktree — see cc-worktree) |
| Tasks share models/schemas | Sequential (earlier task may change interface) |

### Worktree Boundary Enforcement

Workers run in worktrees by default. The guard auto-detects worktree context —
no manual `CC_WORKTREE_PATH` needed when `claude` is launched from a worktree.
For programmatic dispatch, set explicitly:

```bash
# Before spawning worker
export CC_WORKTREE_PATH="$WORK_DIR"
```

This activates the worktree-guard hook which **blocks** Edit/Write operations
targeting files outside the assigned worktree. The guard allows shared state
dirs (`.tasks/`, `.flow/`, `.git/cc-flow-state/`).

Without this, a worker could accidentally edit files in the main checkout —
causing conflicts with other parallel workers or corrupting the main branch.

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
CCFLOW="python3 ${CLAUDE_PLUGIN_ROOT}/scripts/cc-flow.py"

# Before dispatching worker:
TASK_ID=$($CCFLOW ready --epic epic-1 | python3 -c "import sys,json; r=json.load(sys.stdin)['ready']; print(r[0]['id'] if r else '')")
$CCFLOW start $TASK_ID

# Worker receives task spec:
$CCFLOW show $TASK_ID  # Read spec for worker prompt

# After worker completes:
$CCFLOW done $TASK_ID --summary "Implemented X"
```

## E2E Example

```
Plan: 3 tasks for "Add JWT Auth" epic

Orchestrator:
  $ BASE_COMMIT=$(git rev-parse HEAD)  # abc1234
  $ cc-flow start epic-1-add-jwt.1

  → Dispatch Worker 1:
    Prompt: "Implement User model. Spec: .tasks/tasks/epic-1-add-jwt.1.md
            BASE_COMMIT: abc1234. TDD. Max 50 lines."
    Worker re-anchors:
      $ cc-flow show epic-1-add-jwt.1   # read spec
      $ git log --oneline -3            # recent state
      $ Read src/domain/models.py       # current code
    Worker implements:
      RED:   test_user_has_email_and_id → FAIL ✓
      GREEN: @dataclass class User: id, email, password_hash → PASS ✓
      $ ruff check . && mypy . && pytest → all green
      $ git commit -m "feat(domain): add User model"
    Worker reports: "Done. +18 lines, 2 tests added."

  $ cc-flow done epic-1-add-jwt.1 --summary "User model with tests"
  → diff: {insertions: 18, files_changed: 2}
  $ BASE_COMMIT=$(git rev-parse HEAD)  # def5678

  → Dispatch Worker 2: (fresh context, only reads task 2 spec)
    ... same cycle for token service ...

  → Dispatch Worker 3: (fresh context)
    ... same cycle for login endpoint ...

Final:
  $ cc-flow progress --epic epic-1-add-jwt
  → Add JWT Auth: ████████████████████ 100% (3/3)
  $ cc-flow graph --epic epic-1-add-jwt --format ascii
  → ● Task 1 → ● Task 2 → ● Task 3 (all done)
```

## Worker Success Metrics

| Metric | Target | Action if Missed |
|--------|--------|-----------------|
| First-attempt success | ≥ 70% | Improve spec clarity |
| Diff size per worker | ≤ 50 lines | Split task further |
| Worker runtime | < 5 min | Simplify scope |
| Context bleed incidents | 0 | Always fresh agent |

## Related Skills

- **cc-plan** — the plan that workers execute
- **cc-task-tracking** — workers consume tasks from .tasks/ via cc-flow
- **cc-parallel-agents** — parallel worker dispatch patterns
- **cc-autoimmune** — similar loop but for improvement tasks, not plan execution
- **cc-code-review-loop** — review each worker's output with verdict gates
- **cc-worktree** — worktree management for parallel worker isolation
