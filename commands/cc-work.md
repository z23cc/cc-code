---
description: >
  Execute tasks end-to-end with worker isolation, verification, and review.
  TRIGGER: 'work on', 'execute epic', 'implement tasks', 'start working on',
  '执行', '开始实现', '跑任务', '干活'.
---

Activate the cc-work skill. Parse user input to determine mode:

## Input Resolution

| User says | Resolved as |
|-----------|-------------|
| `/cc-work epic-1` | Epic mode — loop all ready tasks in epic-1 |
| `/cc-work epic-1.3` | Single task mode — execute task epic-1.3 only |
| `/cc-work --branch=worktree epic-1` | Epic mode with worktree isolation per task |
| `/cc-work --branch=new epic-1` | Epic mode on new feature branch |
| `/cc-work --review=always epic-1` | Epic mode with review after every task |
| `/cc-work --review=none epic-1.2` | Single task, skip review |
| `/cc-work "Add user auth"` | Create epic from idea, then work |

## Execution Steps

```bash
CCFLOW="python3 ${CLAUDE_PLUGIN_ROOT}/scripts/cc-flow.py"
WORKTREE_SH="${CLAUDE_PLUGIN_ROOT}/scripts/worktree.sh"
```

### Step 1: Resolve input → epic ID + mode (epic or single)

If input is a task ID (contains `.`):
- Extract epic ID from task ID
- Set MODE=single, TASK_ID from input

If input is an epic ID:
- Set MODE=epic

Otherwise:
- Create epic: `$CCFLOW epic create --title "$input"`
- Set MODE=epic

### Step 2: Show progress and confirm

```bash
$CCFLOW progress --epic $EPIC_ID
$CCFLOW ready --epic $EPIC_ID
```

Show user what will be executed. Proceed.

### Step 3: Branch setup

- `--branch=current` (default): stay on current branch
- `--branch=new`: `git checkout -b feature/$EPIC_ID`
- `--branch=worktree`: worktrees created per-task in loop

### Step 4: Task execution loop

For each ready task (or single task):

1. **Start**: `$CCFLOW start $TASK_ID`
2. **Re-anchor**: Read task spec via `$CCFLOW show $TASK_ID`
3. **Worktree** (if --branch=worktree):
   - `bash "$WORKTREE_SH" create $TASK_ID`
4. **Dispatch worker**: Spawn Agent with fresh context
   - Worker prompt includes: task spec, acceptance criteria, BASE_COMMIT, constraints
   - Worker implements using TDD, commits, reports back
5. **Verify**: `$CCFLOW verify`
   - If fails → dispatch build-fixer agent, retry once
6. **Review** (if enabled):
   - Use cc-code-review-loop skill
   - SHIP → continue, NEEDS_WORK → auto-fix loop, MAJOR_RETHINK → stop
7. **Done**: `$CCFLOW done $TASK_ID --summary "..."`
8. **Plan-sync** (if enabled): Update downstream task specs
9. **Worktree merge** (if applicable):
   - Merge task branch back, remove worktree

### Step 5: Completion

After all tasks done:
- Show: `$CCFLOW progress --epic $EPIC_ID`
- If 100%: suggest `/cc-epic-review` for completion verification
