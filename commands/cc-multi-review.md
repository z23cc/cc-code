---
description: "Multi-model review — run independent reviews with 2+ AI engines, compare verdicts, resolve conflicts via consensus. TRIGGER: 'multi model review', 'cross review', 'roundtable', 'consensus', '多模型审查', '圆桌审查', '交叉审查'."
---

Run multi-model code review with independent engines and consensus.

## Protocol

### Phase 1: Detect Available Engines
```bash
cc-flow review-setup
```
Check which backends are available: agent (Claude), rp (RepoPrompt), codex (Codex), gemini (Gemini).

### Phase 2: Independent Reviews (PARALLEL)

Launch 2+ independent review agents simultaneously:

1. **Agent Review** (Claude built-in) — dispatch python-reviewer + security-reviewer in parallel
2. **RP Review** (if available) — `cc-flow rp review "review recent changes"`
3. **Codex Review** (if available) — `codex review` with diff context

Each produces: verdict (SHIP/NEEDS_WORK/MAJOR_RETHINK), issues list, severity scores.

### Phase 3: Consensus Engine

Compare all verdicts:
- **All SHIP** → consensus = SHIP, proceed to commit
- **Mixed verdicts** → merge issue lists, rank by severity × frequency:
  - Issues flagged by 2+ engines = HIGH CONFIDENCE
  - Issues flagged by only 1 engine = REVIEW MANUALLY
- **Any MAJOR_RETHINK** → consensus = NEEDS_WORK, present all findings to user

### Phase 4: Conflict Resolution (if needed)

When engines disagree:
1. Present the disagreement clearly: "Engine A says X, Engine B says Y"
2. Show evidence from each engine
3. Let the user decide, or auto-resolve if one engine has higher-severity evidence

## Output

```markdown
# Multi-Model Review Consensus

## Verdicts
- Agent (Claude): SHIP ✓
- RP (RepoPrompt): NEEDS_WORK — 2 high-severity issues
- Codex: SHIP ✓

## Consensus: NEEDS_WORK (1 engine flagged blocking issues)

## High-Confidence Issues (2+ engines agree)
1. [HIGH] Missing input validation in /api/users — flagged by Agent + RP

## Single-Engine Issues (review manually)
1. [MEDIUM] RP: Consider extracting helper function — style preference
```

## On Completion
Save context: `cc-flow skill ctx save cc-multi-review --data '{"final_verdict": "...", "consensus_report": "...", "engines_used": [...]}'`
