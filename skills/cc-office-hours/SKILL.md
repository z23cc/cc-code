---
name: cc-office-hours
description: >
  YC-style idea validation before building. Asks forcing questions about
  demand, status quo, specificity, wedge, and insight. Produces a 1-page
  design brief.
  TRIGGER: 'office hours', 'validate idea', 'is this worth building',
  '想法验证', '值不值得做', '创业思路'.
  FLOWS INTO: cc-brainstorming (validated idea ready for design).
---

# Office Hours -- Idea Validation

<HARD-GATE>
Do NOT design or build anything until all 5 questions are answered.
</HARD-GATE>

## The Five Forcing Questions

Ask each question sequentially. Wait for the user's answer before proceeding.
Push back on vague answers -- specificity is the signal.

### Q1: Demand -- What problem are you solving?

- Who has this problem? How often? How painful?
- "Lots of people" is not an answer. Name a specific person or role.
- Red flag: solution looking for a problem.

### Q2: Status Quo -- How are people solving it now?

- What's the current workaround? (Spreadsheet? Manual process? Competitor?)
- If nobody is solving it, ask why. Maybe it's not a real problem.
- Red flag: "nobody does this today" with no explanation.

### Q3: Specificity -- What makes your approach better?

- Not "better UX" -- what *specifically* is different?
- 10x improvement on one dimension beats 2x on five dimensions.
- Red flag: feature list without a core differentiator.

### Q4: Wedge -- What's the smallest version you could test?

- What's the one thing it must do on day 1?
- Can you validate with a script, spreadsheet, or landing page first?
- Red flag: "we need all features before launching."

### Q5: Insight -- What have you observed that others missed?

- What non-obvious truth does this bet on?
- Best insights come from personal experience, not market research.
- Red flag: "AI will change everything" (too generic).

## Scoring

After all 5 answers, score each dimension:

| Dimension | Score (1-5) | Notes |
|-----------|-------------|-------|
| Demand    |             |       |
| Status Quo|             |       |
| Specificity|            |       |
| Wedge     |             |       |
| Insight   |             |       |

- **20-25**: Strong signal. Proceed to `/cc-brainstorm`.
- **15-19**: Promising but gaps. Highlight which questions need more thought.
- **Below 15**: Reconsider. Identify the weakest dimension and workshop it.

## Output: 1-Page Design Brief

Produce a single-page brief with sections: **Problem** (from Q1), **Status Quo** (Q2),
**Our Approach** (Q3), **MVP Scope** (Q4), **Key Insight** (Q5), **Validation Score** (N/25),
**Recommended Next Step** (`/cc-brainstorm` | rethink dimension X | talk to N more users).

## Related Skills

- **cc-brainstorming** -- validated ideas flow into design exploration
- **cc-plan** -- design brief becomes the plan input
- **cc-research** -- deepen understanding of status quo
