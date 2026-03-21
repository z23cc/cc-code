---
description: "Run code review on recent changes. TRIGGER: 'review', 'code review', 'check my code', '看看代码', '代码审查'. Dispatches python-reviewer + security-reviewer."
---

Activate the cc-code-review-loop skill. Steps:

```bash
CCFLOW="python3 ${CLAUDE_PLUGIN_ROOT}/scripts/cc-flow.py"
```

1. Run `git diff --staged` and `git diff` to see all changes
2. Classify changed files:
   - `.py` files → dispatch **python-reviewer** agent
   - Other files → dispatch **code-reviewer** agent
3. **MUST dispatch security-reviewer** if changes touch: auth, database queries, file uploads, API endpoints, user input, secrets, or serialization
4. Collect all agent verdicts (SHIP / NEEDS_WORK / MAJOR_RETHINK)
5. If NEEDS_WORK → auto-fix issues, re-review (max 3 loops)
6. If MAJOR_RETHINK → STOP, present issues to user
7. Present consolidated findings sorted by severity

## Auto-Learn from Review (NEW)

After review completes, if non-trivial issues were found:
```bash
$CCFLOW learn --task "[what was reviewed]" --outcome [success/partial] \
  --approach "review found: [issue types]" \
  --lesson "[pattern to check next time]" \
  --score [1-5] --used-command /cc-review
```

This helps the routing system learn which types of changes need more careful review.

## Auto-Chain

After SHIP verdict:
- Suggest: "Review passed. Run `/cc-commit` to commit."
- If cc-scout-docs-gap is relevant: "Consider running `/cc-scout docs-gap` to check if docs need updating."
