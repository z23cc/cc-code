---
name: cc-review-backend
description: >
  Multi-backend code review routing. Supports built-in agent review, RepoPrompt GUI,
  Codex CLI, and context export. Configurable per review type (plan/impl/completion).
  TRIGGER: 'review backend', 'use rp for review', 'codex review', 'review config',
  'switch reviewer', '审查后端', '配置审查方式', '切换审查工具'.
  NOT FOR: doing a review — use cc-review. This is for configuring HOW reviews run.
---

# Review Backend — Multi-Model Review Routing

## Backends

| Backend | ID | How it works | Best for |
|---------|-----|-------------|----------|
| **Agent** | `agent` | Built-in cc-code reviewer agents (parallel) | Default, fast, no setup |
| **RepoPrompt** | `rp` | GUI-based, full file context via Builder | Deep review, visual |
| **Codex CLI** | `codex` | Terminal-based, OpenAI model review | Multi-model, unattended |
| **Export** | `export` | Generate context markdown for external LLM | Manual review |
| **None** | `none` | Skip review | Speed, trust |

## Configuration

```bash
CCFLOW="python3 ${CLAUDE_PLUGIN_ROOT}/scripts/cc-flow.py"

# Set default backend
$CCFLOW config set review.backend agent

# Per-review-type overrides
$CCFLOW config set review.plan rp           # Plan review via RepoPrompt
$CCFLOW config set review.impl agent        # Impl review via built-in agents
$CCFLOW config set review.completion codex  # Epic review via Codex
```

**Override priority** (first wins):
1. Command argument: `--review=rp`
2. Environment variable: `CC_REVIEW_BACKEND=codex`
3. Per-type config: `review.impl`
4. Default config: `review.backend`
5. Fallback: `agent`

## Backend: Agent (Default)

Uses cc-code's built-in reviewer agents in parallel:

```
Dispatch in parallel:
  Agent(cc-code:code-reviewer, "Review diff: $BASE..$HEAD")
  Agent(cc-code:python-reviewer, "Review diff: $BASE..$HEAD")
  Agent(cc-code:security-reviewer, "Review diff: $BASE..$HEAD")

Consolidate → verdict: SHIP / NEEDS_WORK / MAJOR_RETHINK
```

**Verdict rules:**
- Any CRITICAL issue → NEEDS_WORK
- Any architectural problem → MAJOR_RETHINK
- All clear → SHIP

## Backend: RepoPrompt (rp)

Requires RepoPrompt app running (macOS).

### Setup

```bash
# One-time: configure rp-cli alias
alias rp='~/RepoPrompt/repoprompt_cli'
```

### Review Flow

```bash
# Phase 1: Setup review window
eval "$(rp setup-review --repo-root "$REPO_ROOT" --summary "$SUMMARY" --create)"
# Sets W (window) and T (tab)

# Phase 2: Add changed files
CHANGED=$(git diff $BASE..$HEAD --name-only)
for f in $CHANGED; do
  rp select-add --window "$W" --tab "$T" "$f"
done

# Phase 3: Get builder handoff
HANDOFF="$(rp prompt-get --window "$W" --tab "$T")"

# Phase 4: Send review request
rp chat-send --window "$W" --tab "$T" \
  --message-file /tmp/review-prompt.md \
  --new-chat --chat-name "Review: $BRANCH"

# Phase 5: Parse verdict from response
# <verdict>SHIP</verdict> or <verdict>NEEDS_WORK</verdict>

# Phase 6: Fix loop (if NEEDS_WORK)
# Re-review WITHOUT --new-chat (keep conversation context)
rp chat-send --window "$W" --tab "$T" --message-file /tmp/re-review.md
```

### Anti-Patterns (RP)
- Never call builder directly — use `setup-review`
- Never hard-code window IDs
- Never use `--new-chat` on re-reviews
- Never re-run `setup-review` (double context)

## Backend: Codex CLI

Requires Codex CLI installed.

```bash
# Review via Codex
RECEIPT_PATH="/tmp/cc-review-receipt.json"
codex exec \
  --model gpt-5.4 \
  --approval-mode suggest \
  "Review the changes in $CHANGED_FILES. Output <verdict>SHIP|NEEDS_WORK</verdict>"

# Parse verdict from output
VERDICT=$(grep -oE '<verdict>(SHIP|NEEDS_WORK|MAJOR_RETHINK)</verdict>' output \
  | tail -1 | sed 's/<[^>]*>//g')
```

### Session Continuity
Codex receipts include `session_id` for re-review context:
```json
{
  "type": "impl_review",
  "id": "epic-1.3",
  "mode": "codex",
  "verdict": "NEEDS_WORK",
  "session_id": "thread_abc123",
  "timestamp": "2026-01-11T10:30:00Z"
}
```

Re-review with `codex exec resume --thread $session_id`.

## Backend: Export

Generate context markdown for manual review via external LLM:

```bash
# Generate review context
git diff $BASE..$HEAD > /tmp/review-diff.patch
git log $BASE..$HEAD --oneline > /tmp/review-log.txt

# Build review prompt
cat > /tmp/review-export.md << 'EOF'
# Code Review Request

## Changes
[DIFF CONTENT]

## Review Criteria
1. Correctness 2. Simplicity 3. DRY 4. Architecture
5. Edge Cases 6. Tests 7. Security

## Output
End with: <verdict>SHIP</verdict> or <verdict>NEEDS_WORK</verdict>
EOF

echo "Review context exported to /tmp/review-export.md"
echo "Paste into ChatGPT/Claude web and report verdict."
```

## Receipt System (Proof-of-Work)

Every review produces a receipt JSON:

```json
{
  "type": "plan_review|impl_review|completion_review",
  "id": "epic-1|epic-1.3",
  "mode": "agent|rp|codex|export",
  "verdict": "SHIP|NEEDS_WORK|MAJOR_RETHINK",
  "timestamp": "2026-03-23T10:30:00Z",
  "session_id": "optional-for-codex"
}
```

**Receipt storage:**
- Default: `/tmp/cc-review-receipt.json`
- Ralph mode: `scripts/ralph/runs/<run-id>/receipts/<type>-<id>.json`

**Receipt validation:**
```python
def verify_receipt(path, expected_type, expected_id):
    receipt = json.load(open(path))
    return receipt["type"] == expected_type and receipt["id"] == expected_id
```

## Verdict Extraction

```bash
# Universal verdict extraction from any backend response
VERDICT="$(echo "$RESPONSE" \
  | grep -oE '<verdict>(SHIP|NEEDS_WORK|MAJOR_RETHINK)</verdict>' \
  | tail -1 \
  | sed 's/<[^>]*>//g')"
```

## Review Criteria

### Implementation Review (7 dimensions)
1. **Correctness** — Matches spec? Logic errors?
2. **Simplicity** — Simplest solution? Over-engineering?
3. **DRY** — Duplicated logic?
4. **Architecture** — Data flow? Clear boundaries?
5. **Edge Cases** — Failure modes? Race conditions?
6. **Tests** — Adequate coverage?
7. **Security** — Injection? Auth gaps?

### Plan Review (7 dimensions)
1. **Completeness** — All requirements covered?
2. **Feasibility** — Can this be built as described?
3. **Clarity** — Unambiguous specs?
4. **Architecture** — Sound design?
5. **Risks** — Identified and mitigated?
6. **Scope** — Appropriately bounded?
7. **Testability** — Verifiable acceptance criteria?

## Fix Loop

On NEEDS_WORK verdict (max 3 iterations):

```
1. Parse issues from review feedback
2. Fix code + run verification ($CCFLOW verify)
3. Commit: git add -A && git commit -m "fix: address review feedback"
4. Re-review (same backend, same session if applicable)
5. Repeat until SHIP or max iterations
```

## Related Skills

- **cc-code-review-loop** — the verdict gate pattern (SHIP/NEEDS_WORK/MAJOR_RETHINK)
- **cc-work** — orchestrates review as part of the execution pipeline
- **cc-ralph** — autonomous loop that uses review backends as quality gates
