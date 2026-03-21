---
description: "Show cc-code quick start guide. TRIGGER: 'help', 'how to use', 'getting started', '帮助', '怎么用', 'cc-code help'."
---

# cc-code Quick Start

**Don't know which command to use? → `/cc-route your task description`**

## Common Workflows

| I want to... | Command |
|--------------|---------|
| Build a new feature | `/cc-brainstorm` → `/cc-plan` → `/cc-tdd` → `/cc-commit` |
| Fix a bug | `/cc-debug` → `/cc-commit` |
| Review code | `/cc-review` (local) or `/cc-pr-review #123` (GitHub) |
| Big project | `/cc-blueprint` or `/cc-interview` → `/cc-plan` |
| Auto-improve code | `/cc-autoimmune scan` → `/cc-autoimmune` |
| Project assessment | `/cc-prime` (runs all 12 scouts) |
| Manage tasks | `/cc-tasks` (uses cc-flow CLI) |
| Start a new project | `/cc-scaffold` |
| Check project health | `/cc-audit` |
| Dispatch agent team | `/cc-team` |
| Search codebase | `/cc-scout [type]` or `cc-flow search "query"` |

## All 24 Commands

**Workflow:** `/cc-brainstorm` `/cc-plan` `/cc-tdd` `/cc-refine` `/cc-review` `/cc-commit`
**Debug:** `/cc-debug` `/cc-fix`
**Review:** `/cc-review` `/cc-pr-review`
**Scouts:** `/cc-scout` `/cc-prime`
**Planning:** `/cc-blueprint` `/cc-interview`
**Autonomous:** `/cc-autoimmune` `/cc-route`
**Project:** `/cc-scaffold` `/cc-audit` `/cc-docs` `/cc-tasks` `/cc-team`
**Utility:** `/cc-perf` `/cc-simplify` `/cc-research` `/cc-help`

## cc-flow CLI

```bash
cc-flow dashboard                   # One-screen overview
cc-flow search "auth flow" --rerank # Semantic search
cc-flow route "your task"           # Smart routing
cc-flow session save/restore        # Persist work across sessions
cc-flow graph --format ascii        # Dependency tree
cc-flow doctor                      # Health check
```

## Tips

- All commands default to team dispatch (researcher → specialist → reviewer)
- `/cc-brainstorm` auto-runs scouts before the interview
- `/cc-plan` auto-imports tasks into cc-flow
- `/cc-route` gets smarter over time via morph rerank + learnings
- `cc-flow session save` auto-runs before context compaction
