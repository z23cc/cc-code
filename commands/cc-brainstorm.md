---
team: "feature-dev"
description: "Design exploration before coding. TRIGGER: 'brainstorm', 'let me think', 'design this', 'explore the idea', '头脑风暴', '想一想', '设计一下'. MUST use before any new feature implementation."
---

Activate the cc-brainstorming skill (SPARC phases S+A).

<HARD-GATE>
Do NOT write any code until design is approved by user.
</HARD-GATE>

## Default Team: Feature Dev (researcher → architect)

```bash
CCFLOW="python3 ${CLAUDE_PLUGIN_ROOT}/scripts/cc-flow.py"
```

### Phase 1: Auto-Scout (researcher agent)
Dispatch **researcher** to run these scouts:
1. **cc-scout-repo**: existing patterns, conventions, reusable code
2. **cc-scout-practices**: best practices and anti-patterns
3. **cc-scout-gaps**: edge cases and missing requirements

Researcher writes findings to `/tmp/cc-team-research.md`.

### Phase 2: Interview (you + user)
Use scout findings to inform questions:
- Reference cc-scout-gaps: "I found these edge cases — which matter?"
- Reference cc-scout-repo: "There's an existing [pattern] — should we reuse it?"
- Interview: Who / What / Why / How / Edge cases / Non-functional
- Define measurable acceptance criteria

### Phase 3: Architecture (architect agent)
Dispatch **architect** with interview results:
- Propose 2-3 approaches with trade-offs
- Include cc-scout-practices DO/DON'T in analysis
- Write design to `/tmp/cc-team-design.md`

### Phase 4: Output
- Present design section by section, get user approval
- Write spec to `docs/specs/YYYY-MM-DD-<topic>-design.md`
- Transition to `/cc-plan`
