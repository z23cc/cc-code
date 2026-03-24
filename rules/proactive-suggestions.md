---
description: "AI-first skill routing — analyze intent, then suggest optimal skill"
alwaysApply: true
---

# Skill Routing

When the user describes a task:

1. **Classify intent**: BUILD / FIX / IMPROVE / VERIFY / SHIP / UNDERSTAND / PLAN
2. **Detect domains**: security, database, api, frontend, performance → auto-add relevant skill
3. **Route**: `cc-flow go "description"` for auto-routing, or suggest 1-3 specific skills

## Key Routes

| Intent | Primary | Auto-add if domain detected |
|--------|---------|----------------------------|
| BUILD | `/cc-brainstorm` → `/cc-plan` → `/cc-tdd` | +security-review (auth), +database (schema), +architecture (complex) |
| FIX | `/cc-debug` → `/cc-tdd` → `/cc-commit` | +security-review (auth bugs) |
| IMPROVE | `/cc-simplify` or `/cc-performance` | +browser-qa (frontend) |
| VERIFY | `/cc-review` or `/cc-audit` | +security-review (always) |
| SHIP | `/cc-ship` | +review, +verification |
| UNDERSTAND | `/cc-research` | +scout-repo |
| PLAN | `/cc-brainstorm` → `/cc-architecture` | +elicit (challenge) |

## Rules
- Suggest ONCE per session per skill — don't nag
- Max 3 skills per suggestion
- If user says "stop suggesting", respect immediately
- When unsure: `cc-flow go "description" --dry-run`
