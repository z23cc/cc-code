---
description: "Assemble and dispatch an agent team. TRIGGER: 'assemble team', 'team for', 'dispatch team', '组团', '派团队'. Automatically selects the right team template."
---

Activate the cc-teams skill. Determine which team template to use:

| User intent | Team | Agents |
|------------|------|--------|
| "build feature X" / "implement X" | **Feature Dev** | researcher → architect → planner → workers → reviewers |
| "fix bug X" / "debug X" | **Bug Fix** | researcher → build-fixer → code-reviewer |
| "review PR" / "review these changes" | **Review** | researcher → parallel(reviewers) |
| "refactor X" / "restructure X" | **Refactor** | researcher → architect → refactor-cleaner → code-reviewer |
| "check project health" | **Audit** | researcher → architect → security-reviewer |
| "improve the code" | **Autoimmune** | per-task: researcher → fixer → verify |

Steps:
1. Identify the task type from user input
2. Select the team template
3. Dispatch agents sequentially (or parallel where indicated)
4. Each agent writes findings to `/tmp/cc-team-*.md` for handoff
5. Consolidate results and present to user

If the user specifies specific agents ("use researcher and architect only"), respect that — don't force the full template.
