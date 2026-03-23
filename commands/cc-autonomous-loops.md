---
description: >
  Reference for autonomous execution loop patterns and safety controls.
  TRIGGER: 'autonomous', 'loop', 'unattended', 'continuous', '自治循环', '无人值守', '连续执行'.
---

Activate the cc-autonomous-loops skill. Help the user select and configure the right loop pattern.

| User says | Route to |
|-----------|----------|
| `/cc-autonomous-loops` | Show all 5 patterns, help pick one |
| `/cc-autonomous-loops simple` | Simple Pipeline: `cc-flow auto run` |
| `/cc-autonomous-loops ralph` | Ralph Loop: `bash scripts/ralph/ralph.sh` |
| `/cc-autonomous-loops worktree` | Worktree Parallel: `/cc-work --branch=worktree` |
| `/cc-autonomous-loops pr` | Continuous PR: task → branch → PR → merge loop |
| `/cc-autonomous-loops deep` | OODA Deep: `cc-flow auto deep` |

## Steps

1. Understand the user's goal (batch fix, epic execution, exploration)
2. Recommend the appropriate pattern from the skill
3. Confirm safety settings: max iterations, review gates, boundary guards
4. Help configure and launch the selected loop
5. Remind about sentinel files (PAUSE/STOP) for Ralph loops
