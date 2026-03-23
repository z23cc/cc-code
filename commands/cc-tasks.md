---
description: "File-based task management with cc-flow CLI. TRIGGER: 'show tasks', 'create task', 'next task', 'progress', 'close epic', 'validate', '任务列表', '查看任务', '创建任务', '进度'."
---

Activate the cc-task-tracking skill. Use the bundled cc-flow CLI:

```bash
```

Parse the user's intent:

| User says | Command |
|-----------|---------|
| "show tasks" / "list" / "任务列表" | `cc-flow list` |
| "what's next" / "next task" | `cc-flow next` (priority-aware) |
| "what's ready" | `cc-flow ready` |
| "create epic" / "new feature" | `cc-flow epic create --title "..."` |
| "create task" / "add task" | `cc-flow task create --epic ... --title "..."` |
| "start task X" | `cc-flow start <task-id>` |
| "done with X" / "task X done" | `cc-flow done <task-id> --summary "..."` |
| "block task X" | `cc-flow block <task-id> --reason "..."` |
| "reset task X" | `cc-flow task reset <task-id>` |
| "add dependency" | `cc-flow dep add <task-id> <dep-id>` |
| "close epic" / "archive" | `cc-flow epic close <epic-id>` |
| "progress" / "进度" | `cc-flow progress` |
| "status" / "overview" | `cc-flow status` |
| "validate" / "check structure" | `cc-flow validate` |

If `.tasks/` doesn't exist, run `cc-flow init` first.
Always read current state from cc-flow — never cache.
