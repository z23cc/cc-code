---
team: "review"
agent: "code-reviewer"
description: "Run code review on recent changes. TRIGGER: 'review', 'code review', 'check my code', '看看代码', '代码审查'. Dispatches review team."
---

Activate code review with **Review team** dispatch.

```bash
CCFLOW="python3 ${CLAUDE_PLUGIN_ROOT}/scripts/cc-flow.py"
```

## Default Team: researcher → parallel(reviewers) → consolidate

### Step 1: Dispatch researcher
- `git diff --staged` and `git diff` to see all changes
- Classify changed files by type and risk level
- Write context to `/tmp/cc-team-research.md`

### Step 2: Dispatch reviewers in parallel
Based on file types:
- `.py` files → **python-reviewer**
- Other files → **code-reviewer**
- Auth/input/API/DB → **security-reviewer** (ALWAYS if applicable)
- Schema/query changes → **db-reviewer** (if applicable)

### Step 3: Consolidate verdicts
- Collect all verdicts (SHIP / NEEDS_WORK / MAJOR_RETHINK)
- If NEEDS_WORK → auto-fix → re-review (max 3 loops)
- If MAJOR_RETHINK → STOP, present to user
- Present consolidated findings sorted by severity

## Auto-Learn

After review completes:
```bash
$CCFLOW learn --task "[what was reviewed]" --outcome [success/partial] \
  --approach "review found: [issue types]" \
  --lesson "[pattern to check next time]" \
  --score [1-5] --used-command /cc-review
```

## Auto-Chain
After SHIP → suggest `/cc-commit`.
If docs changed → suggest `/cc-scout docs-gap`.
