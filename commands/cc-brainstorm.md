---
description: "Design exploration before coding. TRIGGER: 'brainstorm', 'let me think', 'design this', 'explore the idea', '头脑风暴', '想一想', '设计一下'. MUST use before any new feature implementation."
---

Activate the cc-brainstorming skill (SPARC phases S+A).

<HARD-GATE>
Do NOT write any code until design is approved by user.
</HARD-GATE>

## Auto-Scout Phase (NEW — run before interview)

Before asking the user anything, automatically run these scouts:

```bash
CCFLOW="python3 ${CLAUDE_PLUGIN_ROOT}/scripts/cc-flow.py"
```

1. **cc-scout-repo**: Scan for existing patterns, conventions, and reusable code related to the topic
2. **cc-scout-practices**: Search for best practices and anti-patterns for this type of feature
3. **cc-scout-gaps**: Pre-identify edge cases and missing requirements

Use scout findings to inform your interview questions — ask about gaps the scouts found, reference existing patterns to confirm reuse, and highlight anti-patterns to avoid.

## Interview Phase

1. Explore project context (files, docs, commits) — **USE scout findings, don't re-scan**
2. Interview: Who / What / Why / How / Edge cases / Non-functional
   - Reference cc-scout-gaps findings: "I found these edge cases — which matter?"
   - Reference cc-scout-repo findings: "There's an existing [pattern] — should we reuse it?"
3. Define measurable acceptance criteria
4. Propose 2-3 approaches with trade-offs
   - Include cc-scout-practices DO/DON'T in trade-off analysis
5. Present design section by section, get approval

## Output Phase

6. Write spec to `docs/specs/YYYY-MM-DD-<topic>-design.md`
7. Ask user to review
8. Transition to `/cc-plan` — the plan command will auto-import tasks

For complex features, suggest `/cc-team` (Feature Dev team: researcher → architect → planner → workers → reviewers).
