---
name: cc-work
description: >
  End-to-end task execution with worker isolation, verification, and review.
  Orchestrates: pick task → optional worktree → spawn worker → verify → review → done → loop.
  TRIGGER: 'work through tasks', 'execute epic', 'implement the plan', 'start working',
  '执行任务', '开始实现', '跑任务', '执行计划'.
  NOT FOR: planning — use cc-plan first. NOT FOR: single quick fixes — just do them.
  DEPENDS ON: cc-plan (plan before executing).
  FLOWS INTO: cc-epic-review (verify epic completion).
---

# Work Execution — Full Pipeline

## Overview

`/cc-work` is the one-stop command for executing tasks. It replaces the manual loop of
start → implement → verify → commit → done.

```
/cc-work epic-1           # Work all ready tasks in epic
/cc-work epic-1.3         # Work single task
/cc-work --branch=worktree epic-1  # Each task in isolated worktree
```

## Execution Modes

| Mode | Flag | Behavior |
|------|------|----------|
| **Worktree** | `--branch=worktree` (default) | Create `.claude/worktrees/<task-id>/` per task (max isolation) |
| **New branch** | `--branch=new` | Create feature branch per epic |
| **Current branch** | `--branch=current` | Work on current branch, no isolation |

## Pipeline Phases

### Phase 1: Resolve Input

```bash

# Detect input type
if input is epic ID:
    MODE=epic   # Loop all ready tasks
elif input is task ID:
    MODE=single # Execute one task
elif input is markdown file:
    # Import as epic + tasks
    cc-flow epic import --file input.md
    MODE=epic
else:
    # Treat as idea → create epic
    cc-flow epic create --title "$input"
    MODE=epic
fi
```

### Phase 2: Branch Setup

```bash
WORKTREE_SH="${CLAUDE_PLUGIN_ROOT}/scripts/worktree.sh"

# Detect if already inside a worktree — if so, work here directly
GIT_DIR=$(git rev-parse --git-dir 2>/dev/null)
GIT_COMMON=$(git rev-parse --git-common-dir 2>/dev/null)
GIT_DIR_REAL=$(cd "$GIT_DIR" 2>/dev/null && pwd -P)
GIT_COMMON_REAL=$(cd "$GIT_COMMON" 2>/dev/null && pwd -P)

if [[ "$GIT_DIR_REAL" != "$GIT_COMMON_REAL" ]]; then
  # Already in a worktree — work here, no nesting
  BRANCH_MODE=current
  echo "Already in worktree ($(git branch --show-current)). Working here directly."
fi

case $BRANCH_MODE in
  current)  # Nothing to do (or already in worktree)
    ;;
  new)
    git checkout -b "feature/$EPIC_ID"
    ;;
  worktree)
    # Worktrees created per-task in Phase 3
    ;;
esac
```

### Phase 3: Task Loop

```bash
BASE_COMMIT=$(git rev-parse HEAD)

while true; do
    # 3a. Find next ready task
    TASK=$(cc-flow ready --epic $EPIC_ID | parse next task)
    [[ -n "$TASK" ]] || break  # All done

    # 3b. Start task
    cc-flow start $TASK

    # 3c. Read spec
    SPEC=$(cc-flow show $TASK)

    # 3d. Optional: create worktree
    if [[ $BRANCH_MODE == "worktree" ]]; then
        bash "$WORKTREE_SH" create "$TASK"
        WORK_DIR=$(bash "$WORKTREE_SH" switch "$TASK")
        # Set boundary guard — prevents agent from editing outside worktree
        export CC_WORKTREE_PATH="$WORK_DIR"
    fi

    # 3e. Spawn worker agent (fresh context)
    # When CC_WORKTREE_PATH is set, the worktree-guard hook blocks edits
    # outside the assigned worktree. Worker prompt also includes the path.
    Agent(
        prompt: worker_prompt(TASK, SPEC, BASE_COMMIT, WORK_DIR),
        subagent_type: "cc-code:build-fixer" or general,
        isolation: "worktree"  # Claude Code native worktree isolation
    )

    # 3f. Verify worker output
    git log --oneline -1
    git diff --stat $BASE_COMMIT..HEAD
    cc-flow verify  # ruff + mypy + pytest

    # 3g. Review (if enabled)
    # Uses cc-code-review-loop skill
    # Verdict: SHIP → continue, NEEDS_WORK → fix loop, MAJOR_RETHINK → stop

    # 3h. Mark done
    SUMMARY=$(git log --oneline $BASE_COMMIT..HEAD)
    cc-flow done $TASK --summary "$SUMMARY"

    # 3i. Plan-sync (if enabled) — update downstream task specs
    # See cc-plan-sync skill

    # 3j. Update base for next task
    BASE_COMMIT=$(git rev-parse HEAD)

    # 3k. Merge worktree back (if applicable)
    if [[ $BRANCH_MODE == "worktree" ]]; then
        cd $REPO_ROOT
        git merge "$TASK"
        bash "$WORKTREE_SH" remove "$TASK"
    fi

    # Single task mode → break after one
    [[ $MODE == "epic" ]] || break
done
```

### Phase 4: Quality Gate

```bash
cc-flow verify --fix  # Auto-fix lint/type errors
```

### Phase 5: Completion

```bash
# If all tasks done, optionally run epic review
cc-flow progress --epic $EPIC_ID

# If epic complete → /cc-epic-review
```

## Worker Prompt Template

Each worker receives a self-contained prompt:

```markdown
## Task: {task_title}

### Context
- Epic: {epic_id} — {epic_title}
- Task: {task_id}
- Spec: (inline task spec content)
- BASE_COMMIT: {sha}
- WORK_DIR: {worktree_path or repo_root}

### Files to Touch
{from task spec or auto-detected}

### Acceptance Criteria
{from task spec}

### Constraints
- ONLY edit files within WORK_DIR ({worktree_path})
- Do NOT modify files outside scope or in the main checkout
- Follow TDD: test first, then implement
- Max 50 lines diff
- Run verification before committing

### When Done
- Commit with conventional message
- Report: files changed, tests added
```

## Review Integration

Review is optional. Three modes:

| Flag | Behavior |
|------|----------|
| `--review=auto` (default) | Review if diff > 30 lines (uses configured backend) |
| `--review=always` | Review every task |
| `--review=none` | Skip review |
| `--backend=agent` | Use built-in reviewer agents (default) |
| `--backend=rp` | Use RepoPrompt GUI for review |
| `--backend=codex` | Use Codex CLI for review |
| `--backend=export` | Export context for external LLM review |

When reviewing, uses **cc-code-review-loop** skill:
1. Dispatch reviewer agent (code-reviewer + python-reviewer in parallel)
2. Get verdict: SHIP / NEEDS_WORK / MAJOR_RETHINK
3. NEEDS_WORK → auto-fix → re-review (max 3 loops)
4. MAJOR_RETHINK → stop, surface to user

## Evidence Recording

On task completion, record proof-of-work:

```bash
cc-flow done $TASK --summary "Implemented user auth" \
    --evidence '{"commits":["abc123"],"tests":["pytest tests/"]}'
```

## Error Recovery

| Situation | Action |
|-----------|--------|
| Worker fails (tests don't pass) | Dispatch build-fixer agent |
| Worker stuck (timeout) | Kill, rollback: `cc-flow rollback $TASK --confirm` |
| Review gives MAJOR_RETHINK | Stop loop, ask user |
| Worktree merge conflict | Stop, surface conflict to user |
| All retries exhausted | Block task: `cc-flow block $TASK --reason "3 attempts failed"` |

## Config

```bash
cc-flow config set work.branch_mode worktree   # default: worktree (max isolation)
cc-flow config set work.review auto             # default review mode
cc-flow config set work.max_attempts 3          # retries before blocking
cc-flow config set work.plan_sync true          # auto-sync downstream specs
```

## Related Skills

- **cc-worktree** — worktree management (create/remove/cleanup)
- **cc-worker-protocol** — worker agent isolation pattern
- **cc-code-review-loop** — verdict-driven review with auto-fix
- **cc-plan-sync** — update downstream tasks after implementation drift
- **cc-epic-review** — verify all tasks satisfy epic spec
- **cc-task-tracking** — task lifecycle (start/done/block/ready)
- **cc-parallel-agents** — parallel worker dispatch
