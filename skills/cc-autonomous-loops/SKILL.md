---
name: cc-autonomous-loops
description: >
  Reference for autonomous execution loop patterns: simple pipeline, Ralph loop,
  worktree parallel, continuous PR, and OODA deep. Includes safety patterns.
  TRIGGER: 'autonomous', 'loop', 'unattended', 'continuous', '自治循环', '无人值守', '连续执行'.
  NOT FOR: single tasks — just do them directly.
  DEPENDS ON: cc-work (task execution), cc-ralph (autonomous harness).
---

# Autonomous Loop Patterns

Five patterns for unattended execution, ordered by complexity.

## Pattern 1: Simple Pipeline

`cc-flow auto run --epic $EPIC_ID --max-iterations 10`

Sequential scan-fix-verify in a single session. Simple but context grows over time.

## Pattern 2: Ralph Loop

`bash scripts/ralph/ralph.sh`

Fresh Claude session per iteration with receipt-based quality gates:
1. Pick next work item via `cc-flow next`
2. Spawn `claude -p` with rendered prompt template
3. Worker executes, writes receipt JSON (proof-of-work)
4. Validate receipt before advancing; retry or auto-block on failure

See **cc-ralph** skill for full details.

## Pattern 3: Worktree Parallel

`/cc-work --branch=worktree epic-1`

Multiple workers in isolated git worktrees:
1. Create worktree per task: `worktree.sh create <task-id>`
2. Spawn worker agent scoped to worktree; guard hook enforces boundary
3. On completion, merge back and remove worktree

## Pattern 4: Continuous PR

Loop: pick task, feature branch, review, PR, merge, next. Human gate per PR.

```bash
while TASK=$(cc-flow ready --epic $EPIC_ID | head -1); do
    git checkout -b "task/$TASK"
    # worker → verify → push → gh pr create → merge → cc-flow done
    git checkout main && git pull
done
```

## Pattern 5: OODA Deep

`cc-flow auto deep --max-iterations 20` — Observe (12 scouts) → Orient (rank) →
Decide (auto-create tasks) → Act (work through them) → Loop (re-scan).

## Safety Patterns

All autonomous loops MUST implement these safeguards:

### Max Iterations
```bash
MAX_ITERATIONS=20  # Hard ceiling, prevents runaway loops
```

### Receipt-Based Quality Gates
Workers produce proof-of-work JSON before the loop advances. No receipt = no progress.

### Worktree Boundary Guards
`CC_WORKTREE_PATH` + `worktree-guard` hook blocks edits outside assigned worktree.

### Careful / Freeze / Guard Modes
- `cc-flow careful` — confirm before destructive ops
- `cc-flow freeze` — read-only audit mode
- `cc-flow guard --pattern "*.env"` — block edits to matching files

### Sentinel Files (Ralph)
- `touch .../PAUSE` — pause at next iteration boundary
- `touch .../STOP` — stop gracefully

## Choosing a Pattern

| Situation | Pattern |
|-----------|---------|
| Quick batch fix | Simple Pipeline |
| Full epic, unattended | Ralph Loop |
| Independent tasks | Worktree Parallel |
| Human review per change | Continuous PR |
| Exploratory improvement | OODA Deep |

## Related Skills

- **cc-ralph** — Ralph autonomous harness (Pattern 2)
- **cc-work** — task execution pipeline (used by all patterns)
- **cc-worktree** — worktree management (Pattern 3)
- **cc-autoimmune** — scan-fix loop (Pattern 1 basis)
- **cc-parallel-agents** — parallel worker dispatch
