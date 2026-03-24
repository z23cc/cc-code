---
description: "Multi-engine consensus review — runs 2+ engines in parallel, merges findings. Usually auto-triggered via /cc-review. TRIGGER: 'multi review', 'consensus review', '多引擎审查'."
---

Run multi-engine parallel review: `cc-flow multi-review`

Normally you don't need this directly — `/cc-review` auto-escalates to the best mode.

Options: `--engines codex,gemini` `--range HEAD~5` `--path scripts/` `--dry-run`
