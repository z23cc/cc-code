---
team: "review"
description: >
  Code review — auto-selects best mode based on available engines.
  3 engines (claude+codex+gemini) → adversarial debate (best quality).
  2 engines → multi-engine consensus. 1 engine → agent lint review.
  TRIGGER: 'review', 'code review', 'check my code', '看看代码', '代码审查'.
  FLOWS INTO: cc-commit.
---

Run code review: `cc-flow review`

Auto-selects the best mode:
- **3 engines available** → Adversarial debate (Claude × Codex × Gemini)
- **2 engines available** → Multi-engine consensus
- **1 engine** → Agent lint review (fallback)

RP Builder always provides deep codebase context when available.

## Options

```bash
cc-flow review                              # auto-detect best mode
cc-flow review --mode adversarial           # force 3-engine debate
cc-flow review --mode multi                 # force consensus mode
cc-flow review --mode agent                 # force single-engine
cc-flow review --range HEAD~5              # review last 5 commits
cc-flow review --path scripts/ tests/      # limit to directories
cc-flow review --dry-run                    # show plan only
```

## Debate Flow (3 engines)

```
Phase 0: RP Builder → deep codebase context
Round 1: Claude (security) ∥ Codex (bugs) ∥ Gemini (architecture) — parallel
Round 2: Each sees others' arguments → rebut/agree — parallel
Round 3: Majority vote + surviving issues → verdict
```

## On Completion
Save: `cc-flow skill ctx save cc-review --data '{"verdict": "...", "issues": [...]}'`
Next: `/cc-commit` if SHIP
