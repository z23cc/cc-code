---
description: "Run code review on recent changes. Dispatches python-reviewer for .py files, code-reviewer for others, security-reviewer for auth/input/API code."
---

Analyze the recent git changes and run a comprehensive code review.

1. Run `git diff --staged` and `git diff` to see all changes
2. If Python files changed (`.py`), dispatch the **python-reviewer** agent
3. For all other files, dispatch the **code-reviewer** agent
4. **MUST dispatch security-reviewer** if any changes touch: authentication, authorization, database queries, file uploads, API endpoints, user input handling, secrets/credentials, or serialization
5. Present consolidated findings sorted by severity

Related skills: `verification` (verify fixes after review), `security-review` (checklist)
