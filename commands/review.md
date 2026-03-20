---
description: "Run code review on recent changes. TRIGGER: 'review', 'code review', 'check my code', '看看代码', '代码审查'. Dispatches python-reviewer + security-reviewer."
---

Activate the code-review-loop skill. Steps:

1. Run `git diff --staged` and `git diff` to see all changes
2. Classify changed files:
   - `.py` files → dispatch **python-reviewer** agent
   - Other files → dispatch **code-reviewer** agent
3. **MUST dispatch security-reviewer** if changes touch: auth, database queries, file uploads, API endpoints, user input, secrets, or serialization
4. Collect all agent verdicts (SHIP / NEEDS_WORK / MAJOR_RETHINK)
5. If NEEDS_WORK → auto-fix issues, re-review (max 3 loops)
6. If MAJOR_RETHINK → STOP, present issues to user
7. Present consolidated findings sorted by severity

Related skills: `code-review-loop`, `verification`, `security-review`
