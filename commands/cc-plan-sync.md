---
description: >
  Detect implementation drift and update downstream task specs after a task completes.
  Ensures later tasks reference the actual code state, not outdated assumptions.
  TRIGGER: 'sync plan', 'update downstream', 'plan drift', 'specs outdated', 'tasks out of date'.
---

Activate the cc-plan-sync skill.

## Usage

```bash
/cc-plan-sync epic-1               # Sync all remaining tasks in epic
/cc-plan-sync epic-1.3             # Sync one specific task
/cc-plan-sync epic-1 --dry-run     # Preview without modifying
```

## How It Works

1. **Detect drift** — compare completed task's changes vs what downstream tasks reference
2. **Identify affected tasks** — specs mentioning renamed files, functions, paths, endpoints
3. **Update specs** — dispatch research agent to rewrite stale references
4. **Report** — list updated tasks and what changed

## Auto Mode

```bash
cc-flow config set work.plan_sync true   # Enable auto-sync after each task in /cc-work
```
