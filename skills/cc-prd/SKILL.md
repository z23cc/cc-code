---
name: cc-prd
description: >
  Convert a PRD, spec, or feature brief into a phased implementation plan with
  architectural decisions, vertical slices, and tracer-bullet first milestone.
  Bridges the gap between brainstorm output and cc-plan input.
  TRIGGER: 'prd', 'spec to plan', 'convert spec', 'implementation strategy',
  'from requirements', 'PRD', '需求转计划', '规格转计划', '需求文档'.
  NOT FOR: writing the PRD itself — use cc-brainstorming. NOT FOR: task-level planning — use cc-plan.
  DEPENDS ON: cc-brainstorming (design spec as input).
  FLOWS INTO: cc-plan (detailed task breakdown).
---

# PRD to Implementation Plan

Convert a Product Requirements Document (PRD), feature spec, or design brief into a concrete, phased implementation strategy.

## Input

One of:
- A PRD or spec file (markdown, docs/specs/*.md)
- A design brief from `/cc-brainstorming` or `/cc-office-hours`
- A verbal description of requirements
- A GitHub issue or feature request

## Process

### Phase 1: Analyze Requirements
1. Read the spec/PRD thoroughly
2. Extract: functional requirements, non-functional requirements, constraints, assumptions
3. Identify: actors, data entities, external integrations, error scenarios
4. Flag: ambiguities, missing requirements, conflicting constraints

### Phase 2: Architectural Decisions
For each major decision point:
```markdown
### Decision: [Topic]
- **Options**: A (description) | B (description) | C (description)
- **Chosen**: [option] — because [rationale]
- **Trade-off**: [what we give up]
- **Reversibility**: high | medium | low
```

Key decisions to make:
- Data model design (entities, relationships)
- API contract (endpoints, request/response shapes)
- State management approach
- Authentication/authorization strategy
- Error handling strategy
- Testing strategy (unit/integration/e2e split)

### Phase 3: Vertical Slices
Break the system into **vertical slices** (end-to-end features, not horizontal layers):

```
Slice 1 (Tracer Bullet): [minimal end-to-end path]
  → Proves architecture works, unblocks all other slices
  → Must include: API → Logic → Storage → Test

Slice 2: [next most valuable feature]
Slice 3: [next feature]
...
```

**Tracer bullet first**: The first slice must be a thin, complete path through all layers. This validates the architecture before building features.

### Phase 4: Phased Plan
Group slices into phases:

```markdown
## Phase 1: Foundation (Tracer Bullet)
- Slice 1: [description]
- Duration estimate: [relative, not absolute]
- Verification: [how to know it's done]

## Phase 2: Core Features
- Slice 2-4: [descriptions]
- Dependencies: Phase 1 complete

## Phase 3: Polish & Edge Cases
- Slice 5-N: [descriptions]
- Dependencies: Phase 2 complete
```

### Phase 5: Output

Write the implementation plan to `docs/specs/YYYY-MM-DD-<topic>-impl-plan.md` with:
1. **Summary** — one paragraph
2. **Architectural Decisions** — table of decisions with rationale
3. **Vertical Slices** — ordered list with tracer bullet first
4. **Phased Plan** — phases with slices, dependencies, verification
5. **Risks** — identified risks and mitigations
6. **Open Questions** — items needing user input

Then import to cc-flow:
```bash
cc-flow epic import --file docs/specs/YYYY-MM-DD-<topic>-impl-plan.md
```

## On Completion

When the implementation plan is written and imported:
```bash
cc-flow skill ctx save cc-prd --data '{"plan_doc": "<path>", "phases": 3, "slices": 8, "decisions": ["..."], "tracer_bullet": "..."}'
cc-flow skill next
```

## Key Principles

- **Vertical slices over horizontal layers** — "user can do X" not "backend is done"
- **Tracer bullet first** — prove the architecture before building features
- **Decisions are explicit** — every architectural choice documented with rationale
- **Reversibility matters** — flag decisions that are hard to change later
- **No time estimates** — use relative sizing (small/medium/large) not days/hours

## Related Skills

- **cc-brainstorming** — produces the design spec this skill consumes
- **cc-plan** — takes the phased plan and creates detailed tasks
- **cc-office-hours** — validates the idea before spec writing
- **cc-grill-me** — adversarial review of the plan
