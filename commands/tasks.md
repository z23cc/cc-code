---
description: "File-based task management with cc-flow CLI. TRIGGER: 'show tasks', 'create task', 'next task', 'progress', 'close epic', 'validate', '任务列表', '查看任务', '创建任务', '进度'."
---

Activate the task-tracking skill. Use the bundled cc-flow CLI:

```bash
CCFLOW="python3 ${CLAUDE_PLUGIN_ROOT}/scripts/cc-flow.py"
```

Parse the user's intent:

| User says | Command |
|-----------|---------|
| "show tasks" / "list" / "任务列表" | `$CCFLOW list` |
| "what's next" / "next task" | `$CCFLOW next` (priority-aware) |
| "what's ready" | `$CCFLOW ready` |
| "create epic" / "new feature" | `$CCFLOW epic create --title "..."` |
| "create task" / "add task" | `$CCFLOW task create --epic ... --title "..."` |
| "start task X" | `$CCFLOW start <task-id>` |
| "done with X" / "task X done" | `$CCFLOW done <task-id> --summary "..."` |
| "block task X" | `$CCFLOW block <task-id> --reason "..."` |
| "reset task X" | `$CCFLOW task reset <task-id>` |
| "add dependency" | `$CCFLOW dep add <task-id> <dep-id>` |
| "close epic" / "archive" | `$CCFLOW epic close <epic-id>` |
| "progress" / "进度" | `$CCFLOW progress` |
| "status" / "overview" | `$CCFLOW status` |
| "validate" / "check structure" | `$CCFLOW validate` |

If `.tasks/` doesn't exist, run `$CCFLOW init` first.
Always read current state from cc-flow — never cache.
