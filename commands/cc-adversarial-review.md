---
description: "3-engine adversarial debate: Claude × Codex × Gemini review with battle rounds. TRIGGER: 'adversarial review', 'debate review', '对抗审查', '辩论审查'."
---

Run 3-engine adversarial debate review: `cc-flow adversarial-review`

Phase 0: RP gathers deep codebase context
Round 1: 3 engines independently review (parallel)
Round 2: Each engine sees the other two's arguments, debates (parallel)
Round 3: Majority vote + surviving issues

Options: `--range HEAD~5` `--path scripts/` `--engines claude,gemini`

## On Completion
Save: `cc-flow skill ctx save cc-adversarial-review --data '{"verdict": "...", "issues": [...]}'`
Next: `/cc-commit` if SHIP, fix issues if NEEDS_WORK
