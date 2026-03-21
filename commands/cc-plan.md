---
description: "Create implementation plan with TDD tasks. TRIGGER: 'plan this', 'how should we build', 'design X', '规划', '写计划'. Use AFTER brainstorming, BEFORE /tdd."
---

Use the cc-plan skill to create a comprehensive implementation plan.

```bash
CCFLOW="python3 ${CLAUDE_PLUGIN_ROOT}/scripts/cc-flow.py"
```

## Planning Phase

1. Analyze the user's request or existing spec
2. If unfamiliar codebase: dispatch **researcher** agent first
3. If architectural change: dispatch **architect** agent before planning
4. Map out the file structure
5. Create bite-sized tasks with TDD workflow
6. Include exact file paths, code, and commands

## Auto-Import to cc-flow (NEW)

After the plan is written:

7. Save the plan to `docs/plans/YYYY-MM-DD-<feature>.md`
8. **Automatically import into cc-flow tasks:**
   ```bash
   $CCFLOW epic import --file docs/plans/YYYY-MM-DD-<feature>.md --sequential
   ```
9. Show the task graph:
   ```bash
   $CCFLOW graph --format ascii
   ```
10. Confirm with user: "Plan imported as [epic-id] with [N] tasks. Start with `/cc-tdd`?"

## Auto-Tagging

When creating tasks via cc-flow, add tags based on content:
- Task touches API routes → `--tags api`
- Task touches database → `--tags database`
- Task is a test → `--tags test`
- Task touches auth → `--tags auth,security`

## Auto-Template

Select template based on task type:
- New file creation → `--template feature`
- Bug fix in plan → `--template bugfix`
- Refactoring step → `--template refactor`
- Security hardening → `--template security`

If import fails or user prefers manual control, show the cc-flow commands they can run themselves.
