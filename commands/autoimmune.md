---
description: "Autonomous improvement loop. TRIGGER: 'autoimmune', 'auto improve', 'auto scan', '自动改进', '自动扫描', '跑改进循环'. 4 modes: code/test/full/scan."
---

Activate the autoimmune skill. Parse the user's input for mode:

| Input | Mode | What Happens |
|-------|------|-------------|
| "autoimmune" / "自动改进" | A | Pick from improvement-program.md or .tasks/, implement, verify, commit/revert |
| "autoimmune test" / "测试改进" | B | Auto-fix ruff → mypy → pytest failures |
| "autoimmune scan" / "自动扫描" | D | Scan codebase (ruff/mypy/bandit/radon), generate task list, then run Mode A |
| "autoimmune full" / "全量改进" | C | Mode D → A → B (scan + improve + fix) |

Optional focus topic: "autoimmune 数据库层" → scope Mode A/D to matching area.

Before starting:
1. Run verify command to confirm clean baseline
2. Record `BASELINE_SHA=$(git rev-parse HEAD)`
3. For Mode A: check improvement-program.md or .tasks/ exists
4. For Mode D: no prerequisites (scan generates the list)
5. Create branch `auto/improve-YYYYMMDD-HHMM`

Run the loop. Print session summary with before/after metrics when done.
