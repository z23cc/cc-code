---
name: cc-requirement-gate
description: >
  Validate requirements before planning — assess complexity, clarity, risks,
  and missing info. Prevents vague specs from entering implementation.
  TRIGGER: 'validate requirements', 'requirement gate', 'are requirements clear',
  'check spec', 'ready to plan', '需求验证', '需求清晰吗', '检查需求'.
  NOT FOR: writing requirements — use cc-brainstorming. NOT FOR: task planning — use cc-plan.
  DEPENDS ON: cc-brainstorming (design spec as input).
  FLOWS INTO: cc-prd (if clear), cc-plan (if simple enough to skip PRD).
---

# Requirement Gate

Structured quality check before investing time in planning and implementation. Catches ambiguity, missing info, and scope issues early.

## Input

The output from `/cc-brainstorm` or `/cc-office-hours`:
- Design spec document
- Acceptance criteria
- Design decisions

## Assessment Process

### Step 1: Read the spec/requirements thoroughly

### Step 2: Assess each dimension

| Dimension | Question | Rating |
|-----------|----------|--------|
| **Clarity** | Can an engineer implement this without asking questions? | clear / needs_confirmation / needs_clarification |
| **Completeness** | Are all user flows, error cases, and edge cases covered? | complete / partial / insufficient |
| **Complexity** | How many systems/modules does this touch? | low / medium / high |
| **Feasibility** | Can this be built with current tech stack and constraints? | feasible / risky / blocked |
| **Testability** | Can acceptance criteria be verified automatically? | testable / partially / untestable |

### Step 3: Identify gaps

List specifically:
- **Missing information**: What must be answered before coding?
- **Ambiguities**: Where could two engineers interpret this differently?
- **Key risks**: What could go wrong?
- **Recommended questions**: What to ask the user to clarify?

### Step 4: Produce structured output

```markdown
## Requirement Assessment

### Summary
[One-paragraph assessment]

### Ratings
| Dimension | Rating | Notes |
|-----------|--------|-------|
| Clarity | clear | ... |
| Completeness | partial | Missing error handling for X |
| Complexity | medium | Touches auth + API + DB |
| Feasibility | feasible | All within current stack |
| Testability | testable | Clear acceptance criteria |

### Missing Information
1. [What's missing]
2. [What's missing]

### Key Risks
1. [Risk + mitigation]

### Decision
- **PROCEED** — requirements clear enough for planning
- **CONFIRM** — need user to confirm 1-2 assumptions
- **CLARIFY** — need answers to N questions before proceeding
```

### Step 5: Act on decision

- **PROCEED** → invoke `/cc-prd` or `/cc-plan`
- **CONFIRM** → present assumptions, ask user, then proceed
- **CLARIFY** → present questions, wait for answers, re-assess

## On Completion

When assessment is done:
```bash
cc-flow skill ctx save cc-requirement-gate --data '{"decision": "PROCEED", "complexity": "medium", "clarity": "clear", "risks": ["..."], "missing": []}'
cc-flow skill next
```

## Related Skills

- **cc-brainstorming** — produces the spec this skill validates
- **cc-prd** — converts validated spec to implementation plan
- **cc-plan** — creates tasks from the plan
- **cc-grill-me** — adversarial review (complementary, not replacement)
