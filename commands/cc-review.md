---
team: "review"
agent: "code-reviewer"
description: >
  Run code review on recent changes. Supports multiple backends: agent (default),
  rp (RepoPrompt GUI), codex (OpenAI CLI), export (context for external LLM).
  TRIGGER: 'review', 'code review', 'check my code', '看看代码', '代码审查'.
  FLOWS INTO: cc-commit (commit approved changes).
---

Activate code review. First determine the **review backend**, then route.

```bash
CCFLOW="python3 ${CLAUDE_PLUGIN_ROOT}/scripts/cc-flow.py"
```

## Backend Selection (first match wins)

1. User argument: `/cc-review --backend=rp` or `/cc-review --backend=codex`
2. Environment variable: `CC_REVIEW_BACKEND`
3. Config: `$CCFLOW config get review.backend`
4. Default: `agent`

## Route by Backend

### Backend: agent (default)

**Team: researcher → PARALLEL(reviewers) → consolidate**

#### Step 1: Researcher (sequential — needed before reviewers)
- `git diff --staged` and `git diff` to see all changes
- Classify changed files by type and risk level
- Write context to `/tmp/cc-team-research.md`

#### Step 2: Reviewers (PARALLEL — dispatch ALL applicable reviewers in ONE message)

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

#### Step 3: Consolidate (sequential — after all reviewers complete)
- Collect all verdicts
- Worst verdict wins: MAJOR_RETHINK > NEEDS_WORK > SHIP
- If NEEDS_WORK → auto-fix → re-review (max 3 loops)
- If MAJOR_RETHINK → STOP, present to user

### Backend: rp (RepoPrompt)

Requires RepoPrompt app running. See **cc-review-backend** skill for full RP protocol.

1. Identify changes: `git diff $BASE..HEAD --name-only`
2. Compose 1-2 sentence review summary
3. Atomic setup (run ONCE):
   ```bash
   eval "$(rp setup-review --repo-root "$REPO_ROOT" --summary "$SUMMARY" --create)"
   ```
4. Add changed files: `rp select-add --window "$W" --tab "$T" "$file"`
5. Add specs: `rp select-add --window "$W" --tab "$T" ".tasks/..."`
6. Get builder handoff: `rp prompt-get --window "$W" --tab "$T"`
7. Build review prompt with 7 criteria (Correctness, Simplicity, DRY, Architecture, Edge Cases, Tests, Security)
8. Send: `rp chat-send --window "$W" --tab "$T" --message-file /tmp/review-prompt.md --new-chat`
9. Parse verdict: `<verdict>SHIP|NEEDS_WORK|MAJOR_RETHINK</verdict>`
10. Fix loop (if NEEDS_WORK): fix → commit → re-send WITHOUT `--new-chat` (keep context)
11. Write receipt if `REVIEW_RECEIPT_PATH` set

**Anti-patterns:** Never hard-code window IDs. Never `--new-chat` on re-reviews. Never re-run `setup-review`.

### Backend: codex (OpenAI Codex CLI)

1. Identify changes: `git diff $BASE..HEAD`
2. Run:
   ```bash
   codex exec --model gpt-5.4 --approval-mode suggest \
     "Review changes. Output <verdict>SHIP|NEEDS_WORK</verdict>"
   ```
3. Parse verdict from output
4. Fix loop (if NEEDS_WORK): fix → commit → `codex exec resume --thread $session_id`
5. Write receipt with `session_id` for continuity

### Backend: export

1. Generate context: `git diff $BASE..HEAD > /tmp/review-diff.patch`
2. Build review prompt markdown to `/tmp/cc-review-export.md`
3. Print: "Review context exported. Paste into external LLM and report verdict."

### Backend: none

Skip review entirely. Use for speed when you trust the changes.

## Receipt (Proof-of-Work)

When `REVIEW_RECEIPT_PATH` is set (e.g., in Ralph mode), write after review:

```json
{
  "type": "impl_review",
  "id": "<task-id or branch>",
  "mode": "<backend>",
  "verdict": "SHIP",
  "timestamp": "2026-03-23T10:30:00Z"
}
```

## Auto-Learn

```bash
$CCFLOW learn --task "[reviewed]" --outcome [success/partial] \
  --approach "review found: [types]" --lesson "[pattern]" --score [1-5] --used-command /cc-review
```

After SHIP → suggest `/cc-commit`.
