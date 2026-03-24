---
description: >
  Review engine configuration. /cc-review auto-selects the best mode, but you can
  override with: cc-flow review --mode agent|multi|adversarial.
  TRIGGER: 'review backend', 'review config', 'switch reviewer'.
---

Review mode is auto-selected by `/cc-review` based on available engines:
- 3 engines → adversarial debate (Claude × Codex × Gemini)
- 2 engines → multi-engine consensus
- 1 engine → agent lint review

Override: `cc-flow review --mode agent` to force a specific mode.

Check engines: `cc-flow review-setup`
