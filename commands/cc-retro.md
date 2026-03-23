---
description: >
  Weekly engineering retrospective. Analyzes git history to show what shipped,
  code quality trends, and action items.
  TRIGGER: 'retro', 'retrospective', 'weekly review', 'what did we ship',
  '回顾', '周报', '复盘'.
---

Activate the cc-retro skill.

## Workflow

1. Run git log/diff commands to gather the past week's data
2. Classify commits by category (feature/fix/improve/chore/docs/test)
3. Analyze code quality trends (churn hotspots, test coverage, code volume)
4. Present retrospective: what went well, what could improve, action items
5. Save output to `docs/retros/YYYY-MM-DD-retro.md` if docs/ exists

Accept optional `--since=<date>` argument to override the default 1-week window.
