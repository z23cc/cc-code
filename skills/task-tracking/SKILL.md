---
name: task-tracking
description: >
  File-based task management with epic/task lifecycle, dependency tracking,
  and progress visualization. Uses taskctl CLI and .tasks/ directory.
  TRIGGER: 'show tasks', 'what needs to be done', 'task status', 'create task',
  'list epics', 'next task', 'progress', '任务列表', '查看进度', '创建任务'.
---

# Task Tracking — File-Based Project Management

## Setup

taskctl is BUNDLED with cc-code. Always use:

```bash
TASKCTL="python3 ${CLAUDE_PLUGIN_ROOT}/scripts/taskctl.py"
```

## Quick Reference

```bash
# Initialize .tasks/ directory
$TASKCTL init

# Create epic
$TASKCTL epic create --title "Add user authentication"

# Create tasks under epic
$TASKCTL task create --epic epic-1-add-user-auth --title "Create User model"
$TASKCTL task create --epic epic-1-add-user-auth --title "Add login endpoint" --deps "epic-1-add-user-auth.1"
$TASKCTL task create --epic epic-1-add-user-auth --title "Add JWT middleware" --deps "epic-1-add-user-auth.2"

# View everything
$TASKCTL list                                         # All epics + tasks (human)
$TASKCTL epics                                        # Epics only (JSON)
$TASKCTL tasks --epic epic-1-add-user-auth            # Tasks for one epic
$TASKCTL tasks --status todo                          # Filter by status
$TASKCTL status                                       # Global overview (JSON)
$TASKCTL next --epic epic-1-add-user-auth             # Smart next task (priority-aware)
$TASKCTL show epic-1-add-user-auth                    # Epic detail + spec
$TASKCTL show epic-1-add-user-auth.2                  # Task detail + spec

# What's ready to work on?
$TASKCTL ready --epic epic-1-add-user-auth

# Work on a task
$TASKCTL start epic-1-add-user-auth.1
# ... implement ...
$TASKCTL done epic-1-add-user-auth.1 --summary "Created User model with SQLAlchemy"

# Block a task
$TASKCTL block epic-1-add-user-auth.3 --reason "Waiting for auth library decision"

# Reset a task back to todo
$TASKCTL task reset epic-1-add-user-auth.3

# Add dependency after creation
$TASKCTL dep add epic-1-add-user-auth.3 epic-1-add-user-auth.1

# Progress bar
$TASKCTL progress
# epic-1-add-user-auth: ██████░░░░░░░░░░░░░░ 33% (1/3)

# Close epic (requires all tasks done) — archives to completed/
$TASKCTL epic close epic-1-add-user-auth

# Validate structure (deps, cycles, missing specs)
$TASKCTL validate
```

## Task States

```
todo → in_progress → done
                  ↘ blocked (with reason)
```

Dependencies are enforced: `$TASKCTL start` fails if dependencies aren't done. `$TASKCTL ready` only shows tasks with all deps satisfied.

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
$TASKCTL init
$TASKCTL epic create --title "Feature name from plan"

# For each task in the plan:
$TASKCTL task create --epic epic-N-slug --title "Task from plan step 1"
$TASKCTL task create --epic epic-N-slug --title "Task from plan step 2" --deps "epic-N-slug.1"
```

Then edit each `.tasks/tasks/epic-N-slug.M.md` to add description and acceptance criteria from the plan.

### 2. Execute with Worker Protocol

```bash
# Find next task
$TASKCTL ready --epic epic-1-add-user-auth
# → {"ready": [{"id": "epic-1-add-user-auth.2", "title": "Add login endpoint"}]}

# Start it
$TASKCTL start epic-1-add-user-auth.2

# Dispatch worker agent with the task spec
# Worker reads: .tasks/tasks/epic-1-add-user-auth.2.md

# When worker completes
$TASKCTL done epic-1-add-user-auth.2 --summary "Added POST /api/login with JWT"

# Check progress
$TASKCTL progress
```

### 3. With Autoimmune

For improvement loops, create an epic with improvement tasks:

```bash
$TASKCTL epic create --title "Code quality improvements"
$TASKCTL task create --epic epic-2-code-quality --title "Add type hints to api module"
$TASKCTL task create --epic epic-2-code-quality --title "Extract validation logic"
$TASKCTL task create --epic epic-2-code-quality --title "Add missing docstrings"
```

Then run autoimmune referencing these tasks.

## JSON Output

All commands output JSON for machine parsing. Use in scripts:

```bash
READY=$($TASKCTL ready --epic epic-1-add-user-auth)
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

- **plan** — creates the task list; this skill tracks execution
- **worker-protocol** — workers consume tasks from .tasks/
- **autoimmune** — can reference .tasks/ for structured improvement tracking
- **git-workflow** — commit task state changes alongside code changes
- **code-review-loop** — review each completed task before marking done
