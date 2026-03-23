---
name: cc-grill-me
description: >
  Adversarial design interview -- poke holes in a plan before building it.
  TRIGGER: 'grill me', 'challenge my plan', 'adversarial review', 'poke holes', '挑战我的方案', '找漏洞'
  NOT FOR: code review of existing code (use cc-review), brainstorming from scratch (use cc-brainstorming).
  FLOWS INTO: cc-plan (once the plan survives the grill).
---

# Grill Me: Adversarial Design Interview

Interrogate the user's plan with increasingly tough questions before they commit to building it. The goal is to find weak spots early, not to discourage -- every hard question answered now saves hours of rework later.

<HARD-GATE>
Do NOT accept the plan as-is. Your job is to challenge. Be respectful but relentless.
</HARD-GATE>

## Checklist

1. **Understand the plan** -- ask the user to state it in 2-3 sentences if not already clear
2. **Round 1: Fundamentals** (3-4 questions) -- purpose, users, scope
3. **Round 2: Failure modes** (3-4 questions) -- what breaks, edge cases, dependencies
4. **Round 3: Scale and simplicity** (3-4 questions) -- complexity, alternatives, MVP
5. **Verdict** -- summarize strengths, weaknesses, and recommended changes

## Question Bank

Pick from these categories, adapting to the specific plan. Ask **one question at a time** and wait for the answer before asking the next.

### Round 1: Fundamentals
- Who exactly is the user? What's their context when they use this?
- What problem does this solve that isn't already solved?
- What does success look like? How will you measure it?
- What are you explicitly NOT building?

### Round 2: Failure Modes
- What happens when [critical dependency] is down or slow?
- What's the worst thing a user could do with this? How do you handle it?
- What data can be lost, and what's the recovery path?
- How does this behave with zero data? With 10x expected data?

### Round 3: Scale and Simplicity
- What's the simplest version that still delivers value?
- Which parts of this will you regret in 6 months?
- Can you delete any of these features and still ship?
- What's your plan if this takes 3x longer than expected?

## The Process

**Adapt questions based on answers.** If the user reveals a weak spot, drill into it. If an area is solid, move on. The rounds are a guide, not a rigid script.

**Scoring (internal, share at end):**
- Each answer: Strong / Acceptable / Weak / Missing
- If 3+ answers are Weak or Missing, recommend revisiting the design

**Verdict format:**
```
## Grill Results

Strengths:  [What's solid]
Weaknesses: [What needs work]
Recommendations: [Specific changes before building]
Ready to build: Yes / Yes with changes / Not yet
```

## Key Principles

- **One question at a time** -- let the user think and respond
- **Increasingly specific** -- start broad, then drill into weak spots
- **Challenge, don't block** -- improve the plan, not kill it

## Related Skills

- **cc-brainstorming** -- when there's no plan yet to challenge
- **cc-plan** -- invoke after the plan passes the grill
