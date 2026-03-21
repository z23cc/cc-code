---
team: "review"
agent: "code-reviewer"
description: "Run code review on recent changes. TRIGGER: 'review', 'code review', 'check my code', '看看代码', '代码审查'. Dispatches review team."
---

Activate code review with **Review team** — uses parallel agent dispatch.

```bash
CCFLOW="python3 ${CLAUDE_PLUGIN_ROOT}/scripts/cc-flow.py"
```

## Team: researcher → PARALLEL(reviewers) → consolidate

### Step 1: Researcher (sequential — needed before reviewers)
- `git diff --staged` and `git diff` to see all changes
- Classify changed files by type and risk level
- Write context to `/tmp/cc-team-research.md`

### Step 2: Reviewers (PARALLEL — dispatch ALL applicable reviewers in ONE message)

**IMPORTANT: Use multiple Agent tool calls in a single message to run reviewers in parallel.**

Classify files and dispatch all applicable reviewers simultaneously:
- `.py` files → dispatch **python-reviewer** agent
- Other files → dispatch **code-reviewer** agent
- Auth/input/API/DB → dispatch **security-reviewer** agent
- Schema/query → dispatch **db-reviewer** agent

Each reviewer gets:
- The research findings from `/tmp/cc-team-research.md`
- Only the files relevant to their expertise
- Returns structured verdict: SHIP / NEEDS_WORK / MAJOR_RETHINK

### Step 3: Consolidate (sequential — after all reviewers complete)
- Collect all verdicts
- Worst verdict wins: MAJOR_RETHINK > NEEDS_WORK > SHIP
- If NEEDS_WORK → auto-fix → re-review (max 3 loops)
- If MAJOR_RETHINK → STOP, present to user

## Auto-Learn

```bash
$CCFLOW learn --task "[reviewed]" --outcome [success/partial] \
  --approach "review found: [types]" --lesson "[pattern]" --score [1-5] --used-command /cc-review
```

After SHIP → suggest `/cc-commit`.
