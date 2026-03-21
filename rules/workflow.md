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

## Auto-Learn

After completing any workflow, record the learning:
```bash
cc-flow learn --task "..." --outcome success --approach "..." --lesson "..."
```
