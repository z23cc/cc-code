---
description: "3-engine collaborative plan: Claude designs → Codex stress-tests → Gemini researches + synthesizes. TRIGGER: 'multi plan', '3 engine plan', '多引擎规划', '协作规划'."
---

Run 3-engine collaborative planning: `cc-flow multi-plan "your goal"`

Phase 0: RP gathers codebase context
Round 1: Claude designs structured plan
Round 2: Codex finds pitfalls + Gemini researches (parallel)
Round 3: Gemini synthesizes final plan

## On Completion
Save: `cc-flow skill ctx save cc-multi-plan --data '{"plan_file": "...", "verdict": "..."}'`
Next: `/cc-work` to execute, or `/cc-adversarial-review` to validate
