---
name: cc-plan-sync
description: >
  Detect implementation drift and update downstream task specs after a task completes.
  Ensures later tasks reference the actual code state, not outdated assumptions.
  TRIGGER: 'sync plan', 'update downstream', 'plan drift', 'specs outdated',
  'tasks out of date', '同步计划', '更新下游任务', '计划偏移'.
  NOT FOR: creating plans — use cc-plan. This is for fixing drift AFTER implementation.
  DEPENDS ON: cc-work.
---

# Plan Sync — Implementation Drift Detection

## Problem

Plans written before implementation assume a codebase state. As tasks complete,
the actual code diverges from what later task specs expect:

```
Plan says Task 3: "Add auth to UserViewSet in views.py"
But Task 1 renamed it to UserAPIView in api/views/users.py
→ Task 3 spec is now wrong
```

## When to Sync

| Trigger | Action |
|---------|--------|
| After each task completes (via `/cc-work`) | Auto-sync if `work.plan_sync=true` |
| Manual: `/cc-plan-sync epic-1` | Sync all remaining tasks in epic |
| Manual: `/cc-plan-sync epic-1.3` | Sync one specific task |

## How It Works

### Step 1: Detect Drift

After task N completes, compare what changed vs what downstream tasks expect:

```bash

# What files changed in the completed task?
CHANGED_FILES=$(cc-flow diff $COMPLETED_TASK --stat)

# What do remaining tasks reference?
for TASK in $(cc-flow tasks --epic $EPIC_ID --status todo); do
    SPEC=$(cc-flow show $TASK)
    # Check if spec references any changed files/functions/classes
done
```

### Step 2: Identify Affected Tasks

A downstream task is affected if its spec mentions:
- **File paths** that were renamed/moved
- **Function/class names** that were renamed
- **API endpoints** that changed signature
- **Database fields** that were added/removed
- **Import paths** that changed

### Step 3: Update Specs

For each affected task, dispatch a research agent to:

1. Read the current code state (post-implementation)
2. Read the downstream task spec
3. Identify stale references
4. Rewrite the spec with correct references

```bash
# Update task spec
cc-flow task set-spec $TASK --file /tmp/updated-spec.md
```

### Step 4: Report

```
Plan Sync Report:
  Completed: epic-1.1 "Add User model"
  Changed: src/domain/models.py, src/api/serializers.py

  Updated tasks:
    epic-1.2 "Add auth endpoint" — updated file references
    epic-1.3 "Add permissions"   — updated import paths

  No changes needed:
    epic-1.4 "Add tests" — no overlap with changed files
```

## Dry Run

Check what would change without modifying specs:

```
/cc-plan-sync epic-1 --dry-run
```

## Integration with /cc-work

When `work.plan_sync=true`, plan-sync runs automatically after each task:

```
/cc-work epic-1
  → Task 1: done ✓
  → Plan sync: updated tasks 2, 3 (file paths changed)
  → Task 2: done ✓
  → Plan sync: no drift detected
  → Task 3: done ✓
  → All tasks complete
```

## Config

```bash
cc-flow config set work.plan_sync true   # Enable auto-sync in /cc-work
```


## On Completion

When done:
```bash
cc-flow skill ctx save cc-plan-sync --data '{"epic_id": "<id>", "task_ids": [...]}'
cc-flow skill next
```

## Related Skills

- **cc-work** — orchestrates the full execution pipeline including plan-sync
- **cc-task-tracking** — task spec management (show, set-spec)
- **cc-worker-protocol** — workers that produce the drift
