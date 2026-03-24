---
name: cc-deps
description: >
  Epic/task dependency graph — blocking chains, parallel phases, critical path,
  ready-to-start tasks. Answers "what should I work on next?" instantly.
  TRIGGER: 'dependencies', 'what blocks what', 'critical path', 'what to work on next',
  'execution order', 'parallel phases', '依赖关系', '什么先做', '关键路径', '阻塞'.
  NOT FOR: code dependency analysis — use cc-research. NOT FOR: task creation — use cc-plan.
  FLOWS INTO: cc-work (start the next ready task).
---

# Dependency Graph — What to Work on Next

## Usage

```bash
cc-flow graph --format ascii    # visual dependency tree
cc-flow critical-path           # longest blocking chain
cc-flow ready                   # tasks ready to start now
cc-flow dep show <task-id>      # full dependency chain for a task
```

## Process

### Step 1: Load Current State
```bash
cc-flow status       # overview: in_progress, blocked, todo, done
cc-flow list         # all tasks with status
```

### Step 2: Compute Dependency Graph

Group tasks into **parallel execution phases**:

```
Phase 1 (no dependencies — start now):
  ├── task-1.1: Set up database schema
  └── task-1.2: Configure auth provider

Phase 2 (depends on Phase 1):
  ├── task-2.1: API endpoints (blocked by 1.1)
  └── task-2.2: Auth middleware (blocked by 1.2)

Phase 3 (depends on Phase 2):
  └── task-3.1: Integration tests (blocked by 2.1 + 2.2)
```

### Step 3: Identify Critical Path

The **longest chain** determines minimum completion time:
```
1.1 → 2.1 → 3.1 = 3 phases (critical path)
1.2 → 2.2 → 3.1 = 3 phases (also critical)
```

Slack = phases where a task can be delayed without affecting overall completion.

### Step 4: Recommend Next Actions

```markdown
## Dependency Analysis

### Ready Now (no blockers)
1. task-1.1 — Set up database schema
2. task-1.2 — Configure auth provider

### Blocked (waiting on)
- task-2.1 ← blocked by task-1.1
- task-2.2 ← blocked by task-1.2

### Critical Path
1.1 → 2.1 → 3.1 (3 phases, 0 slack)

### Recommended
Start task-1.1 first (on critical path, unblocks most downstream work).
If parallel: start both 1.1 and 1.2 simultaneously.
```

## On Completion

```bash
cc-flow skill ctx save cc-deps --data '{"ready_tasks": ["1.1", "1.2"], "critical_path": ["1.1", "2.1", "3.1"], "phases": 3}'
cc-flow skill next
```

## Related Skills

- **cc-work** — execute the next ready task
- **cc-plan** — creates the tasks with dependencies
- **cc-task-tracking** — task lifecycle management
