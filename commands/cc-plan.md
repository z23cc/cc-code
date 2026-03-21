---
description: "Create implementation plan with TDD tasks. TRIGGER: 'plan this', 'how should we build', 'design X', '规划', '写计划'. Use AFTER brainstorming, BEFORE /tdd."
---

Use the cc-plan skill to create a comprehensive implementation plan.

1. Analyze the user's request or existing spec
2. Map out the file structure
3. Create bite-sized tasks with TDD workflow
4. Include exact file paths, code, and commands
5. Save the plan to `docs/plans/YYYY-MM-DD-<feature>.md`
6. For multi-task plans, import into cc-flow: `cc-flow epic import --file <plan> --sequential`

For unfamiliar codebases, dispatch **researcher** agent first. For architectural changes, dispatch **architect** agent before planning.
