---
description: >
  Fresh-context worker subagent protocol for task isolation. Each task gets
  a dedicated agent with re-anchor, implement, verify, commit cycle.
  TRIGGER: 'worker protocol', 'task isolation', 'execute plan', 'work through tasks', 'worker agent'.
  USED BY: cc-work (task execution), cc-ralph (autonomous harness).
---

Activate the cc-worker-protocol skill.

## Pattern: One Worker Per Task

```
Orchestrator
  +-- Worker Agent -> Task 1 (fresh context)
  +-- Worker Agent -> Task 2 (fresh context)
  +-- Worker Agent -> Task 3 (fresh context)
```

## Worker Cycle

1. **Re-anchor** — read spec, git log, current file state (never stale assumptions)
2. **Implement** — one task only, max 50 lines diff
3. **Verify** — ruff + mypy + pytest (all must pass)
4. **Commit or revert** — report back to orchestrator

## Orchestrator Protocol

```bash
BASE_COMMIT=$(git rev-parse HEAD)
# For each task:
#   1. Dispatch worker with spec, BASE_COMMIT, constraints
#   2. Wait for completion
#   3. Verify: git log + git diff --stat $BASE_COMMIT..HEAD
#   4. Review if needed
#   5. Update BASE_COMMIT
```

## Worktree Isolation

Set `CC_WORKTREE_PATH` before spawning to activate boundary guard.
Workers in worktrees cannot edit files outside their assigned tree.
