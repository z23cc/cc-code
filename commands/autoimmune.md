---
description: "Autonomous improvement loop. Picks tasks from improvement-program.md, implements, verifies, commits or reverts. Modes: code / test / full. Triggers: autoimmune, auto improve, 自动改进."
---

Activate the autoimmune skill. Parse the user's input for mode:

- No qualifier or "code" → **Mode A** (code improvement loop)
- "test" → **Mode B** (test-driven fix loop)
- "full" → **Mode A then Mode B**

Optional focus topic after the mode (e.g., "autoimmune 数据库层").

Before starting:
1. Check `improvement-program.md` exists (if not, create from template in references/operations.md)
2. Check `improvement-results.tsv` exists (if not, create header)
3. Run verify command to confirm clean baseline
4. Create branch `auto/improve-YYYYMMDD-HHMM`

Then run the selected mode loop per the autoimmune skill until STOP conditions are met.
Print session summary when done.
