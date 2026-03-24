---
name: cc-architecture
description: >
  Solutioning phase — document architectural decisions (ADRs) before implementation.
  Covers API style, data model, auth strategy, state management, testing strategy.
  Prevents multi-agent conflicts by establishing technical contracts upfront.
  TRIGGER: 'architecture', 'ADR', 'technical design', 'solutioning', 'design decisions',
  '架构设计', '技术方案', '架构决策'.
  NOT FOR: code review — use cc-review. NOT FOR: brainstorming — use cc-brainstorming.
  DEPENDS ON: cc-plan (plan before architecture).
  FLOWS INTO: cc-work (implement with clear contracts), cc-tdd (test against ADRs).
---

# Architecture Gate — Solutioning Phase

Document all major technical decisions **before writing code**. This prevents:
- Multi-agent style conflicts (one uses REST, another GraphQL)
- Rework from undocumented assumptions
- Architecture drift during long epics

## When to Use

- Multi-file features (>3 files affected)
- New subsystems or integrations
- Changes touching auth, data model, or API contracts
- Multi-epic projects

## Process

### Step 1: Review Plan Context

Load the plan and requirements:
```bash
cc-flow skill ctx load cc-plan
cc-flow skill ctx load cc-requirement-gate
```

### Step 2: Document ADRs

For each major decision, write an Architecture Decision Record:

```markdown
### ADR-001: [Decision Title]

**Status:** Accepted
**Context:** [Why this decision is needed]
**Options:**
  A. [Option] — pros: ..., cons: ...
  B. [Option] — pros: ..., cons: ...
**Decision:** [Chosen option] — because [rationale]
**Consequences:** [What this means for implementation]
**Reversibility:** high | medium | low
```

### Step 3: Cover These Domains

| Domain | Key Questions |
|--------|--------------|
| **API Design** | REST vs GraphQL? Versioning strategy? Error format? |
| **Data Model** | Entities, relationships, indexes? Migration strategy? |
| **Authentication** | JWT vs session? Token refresh? Permission model? |
| **State Management** | Server-side vs client? Cache strategy? |
| **Testing Strategy** | Unit/integration/e2e split? Mock boundaries? |
| **Error Handling** | Exception hierarchy? Retry policy? Circuit breaker? |
| **Deployment** | Blue/green? Canary? Rollback plan? |

### Step 4: Write Architecture Doc

Save to `docs/specs/YYYY-MM-DD-<topic>-architecture.md`:

```markdown
# Architecture: [Feature Name]

## Summary
[One paragraph — what we're building and how]

## ADRs
[List all decisions from Step 2]

## Component Diagram
[ASCII or Mermaid diagram of components and data flow]

## API Contracts
[Key endpoint specs with request/response shapes]

## Data Model
[Entity definitions with relationships]

## Security Considerations
[Auth, input validation, secrets management]

## Testing Plan
[What to test at each level, mock boundaries]
```

### Step 5: Validate

- [ ] All ADRs have rationale (not just "we chose X")
- [ ] No conflicting decisions
- [ ] API contracts match data model
- [ ] Testing plan covers critical paths
- [ ] Reversibility noted for risky decisions

## On Completion

```bash
cc-flow skill ctx save cc-architecture --data '{"architecture_doc": "<path>", "adrs": ["ADR-001", "ADR-002"], "domains_covered": ["api", "data_model", "auth", "testing"]}'
cc-flow skill next
```

## Related Skills

- **cc-plan** — creates the implementation plan this skill validates technically
- **cc-clean-architecture** — principles and patterns reference
- **cc-prd** — requirements that drive architectural decisions
- **cc-work** — implements against the architecture contracts
