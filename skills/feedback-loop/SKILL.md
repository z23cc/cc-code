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

## Learning Quality Gates

Record a learning **only if**:
- Approach was non-obvious (not already in skills documentation)
- Score ≥ 3/5 (actually useful)
- Likely to recur in this project
- Outcome: success or hard-won partial (learned something)

**Don't record** if:
- Routine/obvious fix ("added missing import")
- One-off issue unlikely to recur
- Outcome: failed with no insight gained yet
- Already covered by existing skill (e.g., "use TDD")

## Consolidation Lifecycle

```
Raw learnings (.tasks/learnings/*.json)
    ↓ cc-flow consolidate (when count ≥ 10)
Group by task similarity (first 3 words)
    ↓
avg_score ≥ 4 AND success_count ≥ 2?
    ├─ YES → Promote to pattern (.tasks/patterns/*.json)
    │         Pattern includes: approach, success_rate, occurrences
    └─ NO  → Keep as raw learning
    ↓
Deduplicate: keep top 3 per group, delete oldest
```

## Route Stats & Confidence

Each `cc-flow learn --used-command /debug` updates `.tasks/route_stats.json`:
```json
{"/debug": {"success": 12, "failure": 2}}
```

Routing confidence = 70% keyword match + 30% historical success rate.
When `cc-flow route` runs, it shows:
- `confidence: 85` — blended score
- `route_history: {uses: 14, success_rate: 86}` — command track record
- `alternatives: [...]` — runner-up commands

## The Flywheel

```
More tasks completed
    → More learnings recorded (cc-flow learn)
        → cc-flow consolidate → promotes patterns
            → Better routing suggestions (higher confidence)
                → Faster task completion
                    → More tasks completed
```

## E2E Example

```bash
# 1. Route a task
$ cc-flow route "fix the broken auth endpoint"
# → {"command": "/debug", "team": "bug-fix", "confidence": 75,
#    "past_learning": {"approach": "check middleware first", "score": 5}}

# 2. Execute
$ /debug   # ... investigates, finds bug in middleware, fixes

# 3. Record learning
$ cc-flow learn \
    --task "fix auth endpoint 401 error" \
    --outcome success \
    --approach "researcher traced to expired token validation in middleware" \
    --lesson "auth 401s usually come from middleware token validation" \
    --score 5 \
    --used-command /debug

# 4. Next time
$ cc-flow route "auth returning 403"
# → {"command": "/debug", "confidence": 92,
#    "past_learning": {"lesson": "auth 401s usually come from middleware..."}}
# Confidence jumped from 75 → 92 because of the recorded learning
```

## Related Skills

- **teams** — router suggests the right team template
- **autoimmune** — learning from improvement session outcomes
- **debugging** — hard-won debugging lessons feed the loop
- **context-tips** — learnings persist to files, surviving context compaction
- **task-tracking** — learnings integrate with .tasks/ structure
