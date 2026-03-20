---
name: task-tracking
description: >
  File-based task management with epic/task lifecycle. Uses markdown files
  in .tasks/ directory for tracking progress across sessions.
  TRIGGER: 'show tasks', 'what needs to be done', 'task status', 'create task',
  'list epics', '任务列表', '查看进度', '创建任务'.
---

# Task Tracking — File-Based Project Management

## Concept

Lightweight task tracking using plain files. No external tools needed — just markdown and JSON in a `.tasks/` directory. Works across sessions, survives git operations, and is human-readable.

Inspired by flow-next's `.flow/` system, simplified for single-developer Python projects.

## Directory Structure

```
.tasks/
├── meta.json                    # Next epic/task IDs
├── epics/
│   ├── epic-1-add-auth.md       # Epic spec (requirements)
│   └── epic-2-api-redesign.md
├── tasks/
│   ├── epic-1.1.json            # Task state (status, assignee)
│   ├── epic-1.1.md              # Task spec (description, acceptance)
│   ├── epic-1.2.json
│   ├── epic-1.2.md
│   └── ...
└── completed/                   # Archive for done tasks
```

## Task States

```
todo → in_progress → done
                  ↘ blocked (with reason)
```

## Operations

### Initialize

```bash
mkdir -p .tasks/{epics,tasks,completed}
echo '{"next_epic": 1}' > .tasks/meta.json
```

### Create Epic

Write a spec file:

```markdown
<!-- .tasks/epics/epic-1-add-auth.md -->
# Epic: Add Authentication

## Goal
Add JWT-based auth to the FastAPI backend.

## Requirements
- [ ] User registration with email/password
- [ ] Login endpoint returning JWT
- [ ] Protected route middleware
- [ ] Token refresh mechanism

## Acceptance Criteria
- All endpoints tested with pytest
- Security review passes (bandit clean)
- API docs updated
```

### Create Task

```json
// .tasks/tasks/epic-1.1.json
{
  "id": "epic-1.1",
  "epic": "epic-1-add-auth",
  "title": "Create User model and registration endpoint",
  "status": "todo",
  "depends_on": [],
  "created": "2026-03-21"
}
```

```markdown
<!-- .tasks/tasks/epic-1.1.md -->
# Task: Create User model and registration endpoint

## Description
Create SQLAlchemy User model and POST /api/register endpoint.

## Acceptance Criteria
- [ ] User model with email, hashed_password, created_at
- [ ] POST /api/register validates email, hashes password, returns 201
- [ ] Duplicate email returns 409
- [ ] Unit tests for model and endpoint
```

### Update Task Status

```bash
# Start working (update JSON)
python3 -c "
import json; f='.tasks/tasks/epic-1.1.json'
d=json.load(open(f)); d['status']='in_progress'; d['started']='2026-03-21'
json.dump(d, open(f,'w'), indent=2)
"

# Mark done
python3 -c "
import json; f='.tasks/tasks/epic-1.1.json'
d=json.load(open(f)); d['status']='done'; d['completed']='2026-03-21'
json.dump(d, open(f,'w'), indent=2)
"
```

### List Tasks

```bash
# Quick status overview
for f in .tasks/tasks/*.json; do
  python3 -c "import json; d=json.load(open('$f')); print(f'[{d[\"status\"]:12}] {d[\"id\"]}: {d[\"title\"]}')"
done
```

Output:
```
[todo        ] epic-1.1: Create User model and registration endpoint
[in_progress ] epic-1.2: Add login endpoint with JWT
[done        ] epic-1.3: Add password hashing utility
[blocked     ] epic-1.4: Add token refresh (depends on epic-1.2)
```

### Find Ready Tasks

```bash
# Tasks with status=todo and no unfinished dependencies
python3 -c "
import json, glob
tasks = {}
for f in glob.glob('.tasks/tasks/*.json'):
    d = json.load(open(f))
    tasks[d['id']] = d

for t in tasks.values():
    if t['status'] != 'todo': continue
    deps_done = all(tasks.get(d, {}).get('status') == 'done' for d in t.get('depends_on', []))
    if deps_done:
        print(f'READY: {t[\"id\"]}: {t[\"title\"]}')
"
```

## Integration with Worker Protocol

When executing tasks with the worker-protocol skill:

1. **Start**: Update task status to `in_progress`
2. **Dispatch**: Worker agent gets task spec from `.tasks/tasks/epic-N.M.md`
3. **Done**: Update status to `done`, move to `completed/`
4. **Failed**: Update status to `blocked` with reason

## Integration with Autoimmune

The autoimmune skill's `improvement-program.md` is effectively a flat task list. For larger projects, use `.tasks/` for structured tracking and have autoimmune reference task IDs.

## When to Use .tasks/ vs improvement-program.md

| Situation | Use |
|-----------|-----|
| Quick improvements, single session | `improvement-program.md` (flat list) |
| Multi-session project, dependencies | `.tasks/` (structured) |
| Multiple epics in parallel | `.tasks/` (epic grouping) |
| Team coordination | `.tasks/` (assignee tracking) |

## Related Skills

- **plan** — plan creates the tasks; this skill tracks their execution
- **worker-protocol** — workers consume tasks from .tasks/
- **autoimmune** — can reference .tasks/ for structured improvement tracking
- **git-workflow** — commit task state changes alongside code changes
