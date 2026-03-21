---
description: "Deep requirements interview — extracts complete implementation details through structured questioning. TRIGGER: 'interview', 'flesh out requirements', 'what exactly do you need', '需求访谈', '详细聊聊需求'. Use before /cc-plan when spec is vague."
---

Conduct a structured requirements interview to extract complete implementation details.

## Interview Protocol

### Phase 1: Understand the Goal (1-2 questions)
- "What problem does this solve?" (not "what do you want to build")
- "Who uses this and when?"

### Phase 2: Scope Definition (2-3 questions)
- "What's the minimum that would be useful?" (MVP)
- "What's explicitly out of scope?"
- "Is there an existing solution being replaced?"

### Phase 3: Behavior Specification (3-5 questions)
- Walk through the happy path step by step
- For each step: "What if this fails?"
- "What are the edge cases?" (use cc-scout-gaps categories)
- "Are there security/auth requirements?"
- "Performance requirements?" (latency, throughput, data size)

### Phase 4: Technical Constraints (1-3 questions)
- "Any tech stack requirements or preferences?"
- "Integration points with existing systems?"
- "Data model — new tables/fields needed?"

### Phase 5: Acceptance Criteria (confirm)
- Restate understanding as measurable checklist
- "If all these pass, is the feature done?"

## Rules

- **One question at a time** — don't overwhelm
- **Multiple choice when possible** — easier to answer
- **Summarize after each phase** — confirm understanding before proceeding
- **Run cc-scout-gaps** during Phase 3 to find missing edge cases
- **Output a spec file** at the end (write to `.tasks/` or `docs/specs/`)

## Output

Write the interview results as a spec:

```markdown
# Feature: [Name]

## Problem
[What problem this solves, who needs it]

## Scope
- In scope: [list]
- Out of scope: [list]

## User Flow
1. [Step] → expected result
2. [Step] → expected result

## Edge Cases
| Case | Expected Behavior |
|------|------------------|
| [edge case] | [what should happen] |

## Technical Requirements
- Stack: [requirements]
- Integration: [external systems]
- Data: [schema changes]

## Acceptance Criteria
- [ ] [Measurable criterion]
- [ ] [Measurable criterion]
```

After the interview, suggest: `/cc-plan` to create implementation tasks.
