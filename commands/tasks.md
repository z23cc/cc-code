---
description: "File-based task management. TRIGGER: 'show tasks', 'create task', 'what needs to be done', 'task status', '任务列表', '查看任务', '创建任务'. Init, list, create, update task states."
---

Activate the task-tracking skill. Parse the user's intent:

| User says | Action |
|-----------|--------|
| "show tasks" / "list tasks" / "任务列表" | List all tasks with status |
| "what's ready" / "next task" | Show tasks with no unfinished dependencies |
| "create task" / "add task" / "创建任务" | Create new task under an epic |
| "create epic" / "new feature" | Create new epic with spec |
| "start task X" | Update task status to in_progress |
| "done with X" / "task X done" | Update task status to done |
| "task status" / "progress" / "进度" | Show epic progress overview |

If `.tasks/` doesn't exist, offer to initialize it.
Always read current state from files before reporting — never cache.
