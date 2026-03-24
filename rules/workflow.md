---
description: "Development workflow enforcement — required sequence for features, bugs, and reviews"
alwaysApply: true
---

# Workflow Rules

## Feature Development (required sequence)

```
/cc-brainstorm → /cc-plan → /cc-tdd → /cc-refine → /cc-review → /cc-commit
```

- DO NOT skip brainstorming for new features
- DO NOT write production code before a failing test
- DO NOT commit without verification (lint + type + test)
- DO NOT claim completion without evidence

## Bug Fix (required sequence)

```
/cc-debug (4 phases) → fix → test → /cc-commit
```

- DO NOT guess fixes — investigate root cause first
- DO NOT skip creating a regression test

## Code Review (required gates)

- SHIP: no critical/high issues → commit
- NEEDS_WORK: auto-fix → re-review (max 3 loops)
- MAJOR_RETHINK: stop → discuss with user

## Skill Context Protocol

After completing any skill that FLOWS INTO another, save context for the next skill:
```bash
cc-flow skill ctx save <skill-name> --data '{"key": "value", ...}'
```

Before starting a skill that DEPENDS ON another, load predecessor context:
```bash
cc-flow skill ctx load <predecessor-skill>
```

When working in a chain (`cc-flow chain run <name>`), after each step:
```bash
cc-flow chain advance --data '{"key": "value"}'
```

Query the flow graph to see what comes next:
```bash
cc-flow skill next                        # based on current active skill
cc-flow skill next --skill cc-brainstorm  # explicit skill name
cc-flow skill graph --for cc-plan         # see a skill's connections
```

## Auto-Learn

After completing any workflow, record the learning:
```bash
cc-flow learn --task "..." --outcome success --approach "..." --lesson "..."
```
