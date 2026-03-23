---
name: cc-task-tracking
description: >
  File-based task management with epic/task lifecycle, dependency tracking,
  and progress visualization. Uses cc-flow CLI and .tasks/ directory.
  TRIGGER: 'show tasks', 'what needs to be done', 'task status', 'create task',
  'list epics', 'next task', 'progress', '任务列表', '查看进度', '创建任务', '任务管理'.
  NOT FOR: background job queues — use cc-task-queues instead.
---

# Task Tracking — File-Based Project Management

## Setup

cc-flow is BUNDLED with cc-code. Always use:

```bash
CCFLOW="python3 ${CLAUDE_PLUGIN_ROOT}/scripts/cc-flow.py"
```

## Quick Reference

```bash
# Initialize .tasks/ directory
$CCFLOW init

# Create epic
$CCFLOW epic create --title "Add user authentication"

# Create tasks under epic
$CCFLOW task create --epic epic-1-add-user-auth --title "Create User model"
$CCFLOW task create --epic epic-1-add-user-auth --title "Add login endpoint" --deps "epic-1-add-user-auth.1"
$CCFLOW task create --epic epic-1-add-user-auth --title "Add JWT middleware" --deps "epic-1-add-user-auth.2"

# View everything
$CCFLOW list                                         # All epics + tasks (human)
$CCFLOW epics                                        # Epics only (JSON)
$CCFLOW tasks --epic epic-1-add-user-auth            # Tasks for one epic
$CCFLOW tasks --status todo                          # Filter by status
$CCFLOW status                                       # Global overview (JSON)
$CCFLOW next --epic epic-1-add-user-auth             # Smart next task (priority-aware)
$CCFLOW show epic-1-add-user-auth                    # Epic detail + spec
$CCFLOW show epic-1-add-user-auth.2                  # Task detail + spec

# What's ready to work on?
$CCFLOW ready --epic epic-1-add-user-auth

# Work on a task
$CCFLOW start epic-1-add-user-auth.1
# ... implement ...
$CCFLOW done epic-1-add-user-auth.1 --summary "Created User model with SQLAlchemy"

# Block a task
$CCFLOW block epic-1-add-user-auth.3 --reason "Waiting for auth library decision"

# Reset a task back to todo
$CCFLOW task reset epic-1-add-user-auth.3

# Add dependency after creation
$CCFLOW dep add epic-1-add-user-auth.3 epic-1-add-user-auth.1

# Progress bar
$CCFLOW progress
# epic-1-add-user-auth: ██████░░░░░░░░░░░░░░ 33% (1/3)

# Close epic (requires all tasks done) — archives to completed/
$CCFLOW epic close epic-1-add-user-auth

# Validate structure (deps, cycles, missing specs)
$CCFLOW validate
```

## Task States

```
todo → in_progress → done
                  ↘ blocked (with reason)
```

Dependencies are enforced: `$CCFLOW start` fails if dependencies aren't done. `$CCFLOW ready` only shows tasks with all deps satisfied.

## Directory Structure

```
.tasks/
├── meta.json                          # Auto-increment IDs
├── epics/
│   └── epic-1-add-user-auth.md        # Epic spec (editable markdown)
├── tasks/
│   ├── epic-1-add-user-auth.1.json    # Task state (status, dates)
│   ├── epic-1-add-user-auth.1.md      # Task spec (description, acceptance)
│   └── ...
└── completed/                         # Archive
```

## Workflow: Plan → Track → Execute

### 1. From Plan to Tasks

After creating a plan (see plan skill), convert each task to tracked items:

```bash
$CCFLOW init
$CCFLOW epic create --title "Feature name from plan"

# For each task in the plan:
$CCFLOW task create --epic epic-N-slug --title "Task from plan step 1"
$CCFLOW task create --epic epic-N-slug --title "Task from plan step 2" --deps "epic-N-slug.1"
```

Then edit each `.tasks/tasks/epic-N-slug.M.md` to add description and acceptance criteria from the plan.

### 2. Execute with Worker Protocol

```bash
# Find next task
$CCFLOW ready --epic epic-1-add-user-auth
# → {"ready": [{"id": "epic-1-add-user-auth.2", "title": "Add login endpoint"}]}

# Start it
$CCFLOW start epic-1-add-user-auth.2

# Dispatch worker agent with the task spec
# Worker reads: .tasks/tasks/epic-1-add-user-auth.2.md

# When worker completes
$CCFLOW done epic-1-add-user-auth.2 --summary "Added POST /api/login with JWT"

# Check progress
$CCFLOW progress
```

### 3. With Autoimmune

For improvement loops, create an epic with improvement tasks:

```bash
$CCFLOW epic create --title "Code quality improvements"
$CCFLOW task create --epic epic-2-code-quality --title "Add type hints to api module"
$CCFLOW task create --epic epic-2-code-quality --title "Extract validation logic"
$CCFLOW task create --epic epic-2-code-quality --title "Add missing docstrings"
```

Then run autoimmune referencing these tasks.

## JSON Output

All commands output JSON for machine parsing. Use in scripts:

```bash
READY=$($CCFLOW ready --epic epic-1-add-user-auth)
NEXT_ID=$(echo "$READY" | python3 -c "import sys,json; r=json.load(sys.stdin)['ready']; print(r[0]['id'] if r else '')")
```

## When to Use .tasks/ vs improvement-program.md

| Situation | Use |
|-----------|-----|
| Quick improvements, single session | `improvement-program.md` (flat list) |
| Multi-session project, dependencies | `.tasks/` (structured) |
| Multiple epics in parallel | `.tasks/` (epic grouping) |
| Need progress tracking | `.tasks/` (progress bars) |

## Related Skills

- **cc-plan** — creates the task list; this skill tracks execution
- **cc-worker-protocol** — workers consume tasks from .tasks/
- **cc-autoimmune** — can reference .tasks/ for structured improvement tracking
- **cc-git-workflow** — commit task state changes alongside code changes
- **cc-code-review-loop** — review each completed task before marking done
