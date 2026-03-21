---
description: "One-line goal → multi-step construction plan. Turns a brief objective into a phased implementation blueprint with dependency graph. TRIGGER: 'blueprint', 'build plan from scratch', 'how to build X', '蓝图', '从零开始规划'. Use for multi-PR/multi-session projects."
---

Turn a one-line objective into a complete construction blueprint.

## Process

### Step 1: Expand the objective
Take the user's one-liner and expand into:
- **Goal**: What does success look like?
- **Users**: Who benefits?
- **Scope**: What's in/out?

### Step 2: Run scouts (parallel)
- `/cc-scout practices` — best practices for this type of project
- `/cc-scout repo` — existing code to reuse
- `/cc-scout gaps` — edge cases and missing requirements

### Step 3: Design phases
Break into independently deployable phases:

```markdown
## Phase 1: Foundation [1-2 days]
- Task 1.1: [Setup] — [description]
- Task 1.2: [Core model] — [description]

## Phase 2: Core Feature [2-3 days]
- Task 2.1: [Main logic] — depends on 1.2
- Task 2.2: [API endpoint] — depends on 2.1

## Phase 3: Polish [1 day]
- Task 3.1: [Error handling] — depends on 2.2
- Task 3.2: [Documentation] — depends on 2.2
```

### Step 4: Dependency graph
```bash
cc-flow epic import --file blueprint.md --sequential
cc-flow graph --format ascii
```

### Step 5: Self-review
Before presenting, check:
- [ ] Each phase is independently mergeable?
- [ ] No task is bigger than XL (100+ lines)?
- [ ] Dependencies make sense (no circular)?
- [ ] Critical path is clear?
- [ ] First phase delivers user-visible value?

## Output Format

```markdown
# Blueprint: [Project Name]

## Objective
[Expanded from user's one-liner]

## Architecture
[2-3 sentences + simple diagram]

## Phases

### Phase 1: [Name] — [estimated effort]
Prerequisites: none
Tasks:
- [ ] 1.1 [Task] [S/M/L] — [1-line description]
- [ ] 1.2 [Task] [S/M/L] — depends on 1.1

### Phase 2: [Name] — [estimated effort]
Prerequisites: Phase 1 complete
Tasks:
- [ ] 2.1 [Task] [S/M/L] — depends on 1.2
...

## Dependency Graph
[Mermaid or ASCII]

## Risks
- [Risk]: [mitigation]

## Anti-Patterns to Avoid
[From cc-scout-practices findings]

## Next Steps
1. Review this blueprint
2. `/cc-interview` to refine any unclear requirements
3. `cc-flow epic import --file blueprint.md` to create tasks
4. `/cc-tdd` to start implementing Phase 1
```

## When NOT to use /cc-blueprint
- Task is small enough for a single PR → use `/cc-plan` instead
- Requirements are clear and detailed → use `/cc-plan` instead
- Just exploring ideas → use `/cc-brainstorm` instead
