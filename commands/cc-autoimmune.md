---
description: "Autonomous improvement loop integrated with cc-flow tasks. TRIGGER: 'autoimmune', 'auto improve', 'auto scan', '自动改进', '自动扫描', '跑改进循环'. 4 modes: code/test/full/scan."
---

Activate the cc-autoimmune skill. **Use cc-flow auto commands for task-integrated loops.**

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

## Before Starting

1. `BASELINE_SHA=$(git rev-parse HEAD)`
2. `git checkout -b auto/improve-YYYYMMDD`
3. **Auto-save session** before starting:
   ```bash
   $CCFLOW session save --name "pre-autoimmune" --notes "baseline before auto improvement"
   ```
4. Run `$CCFLOW auto scan` to detect issues and create tasks

## During Loop

5. Run `$CCFLOW auto run` — pick next task, read spec, implement, verify
6. For each task: `$CCFLOW start <id>` → implement → verify → `$CCFLOW done <id>` or revert
7. After each done, **auto-record learning**:
   ```bash
   $CCFLOW learn --task "[task title]" --outcome [success/failed] \
     --approach "[what was done]" --lesson "[what worked/didn't]" \
     --score [1-5] --used-command /cc-autoimmune
   ```

## After Loop Ends

8. Print session summary: `$CCFLOW auto status`
9. Show dashboard: `$CCFLOW dashboard`
10. **Auto-consolidate** if 10+ learnings accumulated:
    ```bash
    $CCFLOW consolidate
    ```
11. **Auto-save session** with results:
    ```bash
    $CCFLOW session save --name "post-autoimmune-YYYYMMDD" \
      --notes "autoimmune complete: [N] kept, [M] discarded, [X]% success"
    ```
12. Suggest next: "Run `/cc-review` to review accumulated changes, or `/cc-commit` to commit."
