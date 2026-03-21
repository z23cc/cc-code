---
description: "Show cc-code quick start guide. TRIGGER: 'help', 'how to use', 'getting started', '帮助', '怎么用', 'cc-code help'."
---

# cc-code Quick Start

**Don't know which command to use? → `/route your task description`**

## Common Workflows

| I want to... | Command |
|--------------|---------|
| Build a new feature | `/brainstorm` → `/plan` → `/tdd` → `/commit` |
| Fix a bug | `/debug` → `/fix` → `/commit` |
| Review code | `/review` (local) or `/pr-review #123` (GitHub) |
| Auto-improve code | `/autoimmune scan` → `/autoimmune` |
| Manage tasks | `/tasks` (uses cc-flow CLI) |
| Start a new project | `/scaffold` |
| Check project health | `/audit` |
| Update documentation | `/docs` |
| Dispatch agent team | `/team` |

## All 19 Commands

**Workflow:** `/brainstorm` `/plan` `/tdd` `/refine` `/review` `/commit`
**Debug:** `/debug` `/fix`
**Review:** `/review` `/pr-review`
**Autonomous:** `/autoimmune` `/route`
**Project:** `/scaffold` `/audit` `/docs` `/tasks` `/team`
**Utility:** `/perf` `/simplify` `/research` `/help`

## cc-flow CLI (task manager)

```bash
cc-flow init                    # Start task tracking
cc-flow epic create --title "X" # Create an epic
cc-flow task create --epic X --title "Y" --size S  # Add task
cc-flow next                    # What to work on
cc-flow progress                # Visual progress bars
cc-flow route "your task"       # Smart routing
cc-flow learn --task "X" --outcome success --lesson "Y"  # Record learning
```

## Tips

- Always `/brainstorm` before coding a new feature
- `/commit` auto-runs lint+typecheck before committing
- `/autoimmune full` = scan + fix + test (hands-free)
- `/route` gets smarter over time as you record learnings
