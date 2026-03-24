---
name: cc-brainstorming
description: >
  MUST use before any creative work — explores intent, requirements and design before implementation.
  TRIGGER: 'brainstorm', 'idea', 'design', 'new feature', 'explore options', '头脑风暴', '设计方案'
  NOT FOR: bug fixes, code review, refactoring existing code.
  FLOWS INTO: cc-plan (turn design into implementation plan).
---

# Brainstorming Ideas Into Designs

Turn ideas into fully formed designs through collaborative dialogue. Understand context, ask questions one at a time, present the design, get approval.

<HARD-GATE>
Do NOT write any code, scaffold any project, or take any implementation action until you have presented a design and the user has approved it. This applies to EVERY project regardless of perceived simplicity.
</HARD-GATE>

## SPARC Phases (Specification → Pseudocode → Architecture → Refinement → Completion)

This skill covers **S** (Specification) and **A** (Architecture). The plan skill covers **P** and **R**. TDD covers **C**.

## Checklist

1. **[S] Explore project context** — check files, docs, recent commits
2. **[S] Ask clarifying questions** — one at a time, understand purpose/constraints/success criteria
3. **[S] Define acceptance criteria** — measurable, testable outcomes (not vague "should work")
4. **[A] Propose 2-3 approaches** — with trade-offs and your recommendation
5. **[A] Present design** — in sections scaled to complexity, get approval after each section
6. **Write design doc** — save to `docs/specs/YYYY-MM-DD-<topic>-design.md`
7. **User reviews spec** — ask user to review before proceeding
8. **Transition to implementation** — invoke plan skill

## The Process

**Understanding the idea (Interview Protocol):**
- Check current project state first (files, docs, recent commits)
- If the request describes multiple independent subsystems, flag this immediately — decompose first
- Ask questions one at a time, prefer multiple choice when possible
- Cover these dimensions systematically:
  1. **Who** — target users, personas, access levels
  2. **What** — core features, acceptance criteria, out-of-scope
  3. **Why** — business goal, success metrics, what happens if we don't build this
  4. **How** — technical constraints, existing integrations, performance requirements
  5. **Edge cases** — error scenarios, concurrent access, empty states, limits
  6. **Non-functional** — security, scalability, accessibility, i18n
- Stop interviewing when answers start repeating or user says "enough"

**Exploring approaches:**
- Propose 2-3 different approaches with trade-offs
- Lead with your recommended option and explain why

**Presenting the design:**
- Scale each section to its complexity
- Ask after each section whether it looks right
- Cover: architecture, components, data flow, error handling, testing

**Design for isolation:**
- Break into smaller units with one clear purpose each
- Well-defined interfaces, independently testable
- Smaller units are easier for agents to reason about

**Working in existing codebases:**
- Explore current structure before proposing changes
- Follow existing patterns
- Only include targeted improvements where they serve the current goal

## Design Spec Template

```markdown
# Design: [Feature Name]

## Goal
[One sentence — what this achieves]

## Acceptance Criteria
- [ ] [Measurable criterion 1]
- [ ] [Measurable criterion 2]

## Architecture
[Components, data flow, key interfaces]

## API Contract (if applicable)
- `POST /api/resource` → 201 (create)
- `GET /api/resource/{id}` → 200 | 404

## Data Model
- `Resource(id, name, owner_id, created_at)`
- Relationships: Resource → User (many-to-one)

## Error Scenarios
| Scenario | Response |
|----------|----------|
| Invalid input | 422 with field errors |
| Not found | 404 |
| Unauthorized | 401 |

## Out of Scope
- [Explicitly list what we're NOT building]

## Open Questions
- [Questions needing user input]
```

## After the Design

- Write spec to `docs/specs/YYYY-MM-DD-<topic>-design.md`
- Commit the design document
- Ask user to review before proceeding
- Invoke the plan skill to create implementation plan

## Key Principles

- **One question at a time** — don't overwhelm
- **Multiple choice preferred** — easier to answer
- **YAGNI ruthlessly** — remove unnecessary features
- **Explore alternatives** — always propose 2-3 approaches
- **Incremental validation** — present design, get approval, move on

## E2E Example

```
User: "add rate limiting to our API"

Interview:
Q1: "Which endpoints? All routes, or specific ones?"
A: "Just the auth endpoints — /login and /register"

Q2: "What limits? Options: (a) 5/min per IP, (b) 10/min per user, (c) both"
A: "a — IP-based for now"

Q3: "Storage? (a) In-memory (simple, lost on restart), (b) Redis (persistent)"
A: "b — we already have Redis"

Design Spec Output:
─────────────────────
# Rate Limiting Design

**Goal:** Prevent brute-force on /login and /register

**Acceptance Criteria:**
- [ ] /login and /register limited to 5 req/min per IP
- [ ] Returns 429 with Retry-After header when exceeded
- [ ] Uses existing Redis instance
- [ ] No impact on other endpoints

**Architecture:** Redis sliding window counter
**Data Model:** Key: `ratelimit:{ip}:{endpoint}`, TTL: 60s
**Error Response:** {"error": "Too many requests", "retry_after": 45}
**Out of Scope:** Per-user limits, global rate limiting, dashboard
─────────────────────
→ Next: /plan to create implementation tasks
```

## On Completion

When brainstorming is complete and the user has approved the design:
```bash
cc-flow skill ctx save cc-brainstorming --data '{"design_doc": "<path-to-spec>", "decisions": ["..."], "acceptance_criteria": ["..."]}'
cc-flow skill next
```

## Related Skills

- **cc-plan** — invoke AFTER brainstorming to create implementation plan
- **cc-research** — use for deep code investigation before design decisions
- **cc-verification** — verify design assumptions with evidence
