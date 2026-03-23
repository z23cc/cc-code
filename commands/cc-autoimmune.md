---
description: "Autonomous improvement loop integrated with cc-flow tasks. TRIGGER: 'autoimmune', 'auto improve', 'auto scan', '自动改进', '自动扫描', '跑改进循环'. 4 modes: code/test/full/scan."
team: "autoimmune"
---

Activate the cc-autoimmune skill. **Use cc-flow auto commands for task-integrated loops.**

```bash
```

| Input | cc-flow command | What Happens |
|-------|----------------|-------------|
| "autoimmune scan" / "自动扫描" | `cc-flow auto scan` | Scan → create epic + tasks |
| "autoimmune" / "自动改进" | `cc-flow auto run` | Pick task → implement → verify → done/revert |
| "autoimmune test" / "测试改进" | `cc-flow auto test` | Auto-fix ruff → then fix mypy/pytest |
| "autoimmune full" / "全量改进" | `cc-flow auto full` | scan → run → test |
| "autoimmune status" | `cc-flow auto status` | Session progress from task system |

## Before Starting

1. `BASELINE_SHA=$(git rev-parse HEAD)`
2. `git checkout -b auto/improve-YYYYMMDD`
3. **Auto-save session** before starting:
   ```bash
   cc-flow session save --name "pre-autoimmune" --notes "baseline before auto improvement"
   ```
4. Run `cc-flow auto scan` to detect issues and create tasks

## During Loop

5. Run `cc-flow auto run` — pick next task, read spec, implement, verify
6. For each task: `cc-flow start <id>` → implement → verify → `cc-flow done <id>` or revert
7. After each done, **auto-record learning**:
   ```bash
   cc-flow learn --task "[task title]" --outcome [success/failed] \
     --approach "[what was done]" --lesson "[what worked/didn't]" \
     --score [1-5] --used-command /cc-autoimmune
   ```

## After Loop Ends

8. Print session summary: `cc-flow auto status`
9. Show dashboard: `cc-flow dashboard`
10. **Auto-consolidate** if 10+ learnings accumulated:
    ```bash
    cc-flow consolidate
    ```
11. **Auto-save session** with results:
    ```bash
    cc-flow session save --name "post-autoimmune-YYYYMMDD" \
      --notes "autoimmune complete: [N] kept, [M] discarded, [X]% success"
    ```
12. Suggest next: "Run `/cc-review` to review accumulated changes, or `/cc-commit` to commit."
