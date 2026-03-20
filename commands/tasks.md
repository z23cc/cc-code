---
description: "File-based task management with taskctl CLI. TRIGGER: 'show tasks', 'create task', 'next task', 'progress', 'close epic', 'validate', '任务列表', '查看任务', '创建任务', '进度'."
---

Activate the task-tracking skill. Use the bundled taskctl CLI:

```bash
TASKCTL="python3 ${CLAUDE_PLUGIN_ROOT}/scripts/taskctl.py"
```

Parse the user's intent:

| User says | Command |
|-----------|---------|
| "show tasks" / "list" / "任务列表" | `$TASKCTL list` |
| "what's next" / "next task" | `$TASKCTL next` (priority-aware) |
| "what's ready" | `$TASKCTL ready` |
| "create epic" / "new feature" | `$TASKCTL epic create --title "..."` |
| "create task" / "add task" | `$TASKCTL task create --epic ... --title "..."` |
| "start task X" | `$TASKCTL start <task-id>` |
| "done with X" / "task X done" | `$TASKCTL done <task-id> --summary "..."` |
| "block task X" | `$TASKCTL block <task-id> --reason "..."` |
| "reset task X" | `$TASKCTL task reset <task-id>` |
| "add dependency" | `$TASKCTL dep add <task-id> <dep-id>` |
| "close epic" / "archive" | `$TASKCTL epic close <epic-id>` |
| "progress" / "进度" | `$TASKCTL progress` |
| "status" / "overview" | `$TASKCTL status` |
| "validate" / "check structure" | `$TASKCTL validate` |

If `.tasks/` doesn't exist, run `$TASKCTL init` first.
Always read current state from taskctl — never cache.
