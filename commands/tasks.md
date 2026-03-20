---
description: "File-based task management with taskctl CLI. TRIGGER: 'show tasks', 'create task', 'next task', 'progress', '任务列表', '查看任务', '创建任务', '进度'. Init, list, create, update task states."
---

Activate the task-tracking skill. Use the bundled taskctl CLI:

```bash
TASKCTL="python3 ${CLAUDE_PLUGIN_ROOT}/scripts/taskctl.py"
```

Parse the user's intent:

| User says | Command |
|-----------|---------|
| "show tasks" / "list tasks" / "任务列表" | `$TASKCTL list` |
| "what's ready" / "next task" | `$TASKCTL ready` (optionally with `--epic`) |
| "create epic" / "new feature" | `$TASKCTL epic create --title "..."` |
| "create task" / "add task" / "创建任务" | `$TASKCTL task create --epic ... --title "..."` |
| "start task X" | `$TASKCTL start <task-id>` |
| "done with X" / "task X done" | `$TASKCTL done <task-id> --summary "..."` |
| "block task X" | `$TASKCTL block <task-id> --reason "..."` |
| "progress" / "进度" | `$TASKCTL progress` |
| "show task/epic X" | `$TASKCTL show <id>` |

If `.tasks/` doesn't exist, run `$TASKCTL init` first.
Always read current state from taskctl — never cache.
