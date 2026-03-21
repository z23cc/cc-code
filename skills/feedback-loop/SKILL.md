---
name: feedback-loop
description: >
  Closed-loop development with routing, execution, and learning.
  Route tasks to the right command/team, execute, record outcomes,
  and use past learnings to improve future routing.
  TRIGGER: 'route this', 'what should I use', 'learn from this',
  '路由', '应该用什么命令', '记录经验'.
---

# Feedback Loop — Route → Execute → Learn

## Architecture

```
User input
    ↓
cc-flow route "task description"
    ↓ suggests command + team + past learnings
Execute (via suggested /command)
    ↓
Outcome (success/partial/failed)
    ↓
cc-flow learn --task "..." --outcome "..." --lesson "..."
    ↓ stored in .tasks/learnings/
Future routing reads learnings
    ↓
Better suggestions over time
```

## The Three Components

### 1. Router (`cc-flow route`)

Analyzes user input and suggests the best command + team:

```bash
CCFLOW="python3 ${CLAUDE_PLUGIN_ROOT}/scripts/cc-flow.py"

$CCFLOW route "add a new payment feature"
# → {"command": "/brainstorm", "team": "feature-dev", "reason": "New feature → brainstorm first"}

$CCFLOW route "fix the broken login"
# → {"command": "/debug", "team": "bug-fix", "past_learning": {...}}
```

The router checks:
1. Keyword matching against 15 route patterns
2. Past learnings for similar tasks (keyword overlap + score ≥ 3)
3. Returns both the suggestion and any relevant past experience

### 2. Execution

Use the suggested command:
- `/brainstorm` → `/plan` → `/tdd` → `/refine` → `/commit`
- `/debug` → `/fix` → `/commit`
- `/team` for complex multi-agent tasks
- etc.

### 3. Learning (`cc-flow learn`)

After completing a task, record what worked:

```bash
$CCFLOW learn \
  --task "fix auth middleware bug" \
  --outcome success \
  --approach "researcher agent found the issue in middleware.py, build-fixer applied the fix" \
  --lesson "auth issues usually trace back to middleware — check there first" \
  --score 5
```

Fields:
- `--task`: what you were trying to do
- `--outcome`: success / partial / failed
- `--approach`: what commands/agents/strategies you used
- `--lesson`: what you'd tell your future self
- `--score`: 1-5 how useful was this approach

### 4. Search Learnings

```bash
$CCFLOW learnings                  # Show recent 10
$CCFLOW learnings --search "auth"  # Search by keyword
$CCFLOW learnings --last 20        # Show more
```

## When to Learn

Record a learning when:
- A non-obvious approach solved the problem
- You discovered a project-specific pattern
- An initial approach failed and you found a better one
- The debugging skill escalated to L2+ (the fix was hard-won)

Don't record:
- Routine, obvious tasks
- Learnings that are already in skills (e.g., "use TDD")
- One-off issues that won't recur

## Integration with Other Skills

| Skill | Integration |
|-------|------------|
| **autoimmune** | After session, record kept/discarded ratio + what worked |
| **debugging** | After L2+ escalation, record the root cause pattern |
| **teams** | Record which team composition worked for which task type |
| **worker-protocol** | Record per-worker outcomes for future task sizing |

## The Flywheel

```
More tasks completed
    → More learnings recorded
        → Better routing suggestions
            → Faster task completion
                → More tasks completed
```

Over time, `cc-flow route` becomes increasingly accurate because it draws on your project's specific history.

## Related Skills

- **teams** — router suggests the right team template
- **autoimmune** — learning from improvement session outcomes
- **debugging** — hard-won debugging lessons feed the loop
- **context-tips** — learnings persist to files, surviving context compaction
