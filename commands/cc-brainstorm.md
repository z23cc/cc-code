---
team: "feature-dev"
description: "Design exploration before coding. TRIGGER: 'brainstorm', 'let me think', 'design this', 'explore the idea', '头脑风暴', '想一想', '设计一下'. MUST use before any new feature implementation."
---

Activate the cc-brainstorming skill (SPARC phases S+A).

<HARD-GATE>
Do NOT write any code until design is approved by user.
</HARD-GATE>

## Team: PARALLEL(scouts) → interview → architect

```bash
```

### Phase 1: Auto-Scout (PARALLEL — dispatch ALL 3 scouts in ONE message)

**IMPORTANT: Launch all 3 scouts simultaneously using multiple Agent tool calls in a single message.**

Dispatch 3 scout agents in parallel (each is a dedicated agent, not the researcher):
1. **cc-scout-repo** agent → existing patterns, conventions, reusable code
2. **cc-scout-practices** agent → best practices, anti-patterns, current guidance
3. **cc-scout-gaps** agent → edge cases, missing requirements, priority questions

Each scout agent runs independently and returns structured findings. Wait for all 3 to complete.

### Phase 2: Interview (sequential — needs scout results)
Use scout findings to inform questions:
- "I found these edge cases — which matter?"
- "There's an existing [pattern] — should we reuse it?"
- Interview: Who / What / Why / How / Edge cases / Non-functional
- Define measurable acceptance criteria

### Phase 3: Architecture (sequential — needs interview results)
Dispatch **architect** agent:
- Propose 2-3 approaches with trade-offs
- Include cc-scout-practices DO/DON'T in analysis
- Write design to `/tmp/cc-team-design.md`

### Phase 4: Output
- Present design section by section, get user approval
- Write spec to `docs/specs/YYYY-MM-DD-<topic>-design.md`
- Transition to `/cc-plan`
