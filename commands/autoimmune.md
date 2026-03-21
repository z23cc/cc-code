---
description: "Autonomous improvement loop integrated with cc-flow tasks. TRIGGER: 'autoimmune', 'auto improve', 'auto scan', '自动改进', '自动扫描', '跑改进循环'. 4 modes: code/test/full/scan."
---

Activate the autoimmune skill. **Use cc-flow auto commands for task-integrated loops.**

```bash
CCFLOW="python3 ${CLAUDE_PLUGIN_ROOT}/scripts/cc-flow.py"
```

| Input | cc-flow command | What Happens |
|-------|----------------|-------------|
| "autoimmune scan" / "自动扫描" | `$CCFLOW auto scan` | Scan → create epic + tasks |
| "autoimmune" / "自动改进" | `$CCFLOW auto run` | Pick task → implement → verify → done/revert |
| "autoimmune test" / "测试改进" | `$CCFLOW auto test` | Auto-fix ruff → then fix mypy/pytest |
| "autoimmune full" / "全量改进" | `$CCFLOW auto full` | scan → run → test |
| "autoimmune status" | `$CCFLOW auto status` | Session progress from task system |

Before starting:
1. `BASELINE_SHA=$(git rev-parse HEAD)`
2. `git checkout -b auto/improve-YYYYMMDD`
3. Run `$CCFLOW auto scan` to detect issues and create tasks
4. Run `$CCFLOW auto run` — pick next task, read spec, implement, verify
5. For each task: `$CCFLOW start <id>` → implement → verify → `$CCFLOW done <id>` or revert
6. After loop: `$CCFLOW auto status` for summary, `$CCFLOW progress` for visual
