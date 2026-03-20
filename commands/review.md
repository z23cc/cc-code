---
description: "Run code review on recent changes. Dispatches python-reviewer for .py files, code-reviewer for others."
---

Analyze the recent git changes and run a comprehensive code review.

1. Run `git diff --staged` and `git diff` to see all changes
2. If Python files changed (`.py`), dispatch the **python-reviewer** agent
3. For all other files, dispatch the **code-reviewer** agent
4. If security-sensitive code changed (auth, user input, API endpoints), also dispatch the **security-reviewer** agent
5. Present consolidated findings sorted by severity
