---
name: cc-context-tips
description: "Context window management for long sessions — when to compact, preserve critical info, avoid overflow. TRIGGER: 'context full', 'running out of context', 'session too long', 'compact', 'context overflow', '上下文快满了', '会话太长', '怎么压缩上下文'. NOT FOR: session save/restore (use cc-flow session), task tracking (use cc-flow)."
---

# Context Window Management

## The Problem

Long sessions accumulate context until Claude can't hold it all. Auto-compaction is unpredictable and may discard important information.

## Prevention Strategies

### 1. Use Fresh Agents for Isolated Tasks

```
Instead of: doing 10 tasks in one session
Do: dispatch worker agents per task (see worker-protocol)
```

Each agent gets a clean context with only what it needs. The orchestrator stays light.

### 2. Use cc-flow for State, Not Memory

```
Instead of: "remember we decided to use JWT"
Do: write it to the task spec → cc-flow show <task-id>
```

Filesystem is infinite. Context window is not.

### 3. Write Findings to Files

```
Instead of: accumulating research in the conversation
Do: write to /tmp/cc-team-research.md → read when needed
```

### 4. Compact at Natural Breakpoints

When you notice the session is getting long, compact at these points:
- After completing a task (before starting the next)
- After a research phase (findings already written to file)
- After a review cycle (verdict already recorded)

**Before compacting**, ensure:
- Current task spec is in `.tasks/` or `improvement-program.md`
- Findings are written to files (not just in conversation)
- Git state is clean (committed or stashed)

### 5. Keep Prompts Focused

```
Instead of: "look at the entire codebase and find all issues"
Do: "check src/api/ for N+1 query patterns"
```

Narrow scope = less context consumed = higher quality output.

## Recovery After Compaction

If context was compacted mid-task:

1. `cc-flow show <task-id>` — re-read task spec
2. `git diff --stat` — see what's changed
3. `git log --oneline -5` — recent commits
4. Read any `/tmp/cc-team-*.md` handoff files

## Autoimmune + Context

The autoimmune skill is context-friendly by design:
- Each iteration is self-contained (SELECT → PLAN → IMPLEMENT → VERIFY)
- Task source is re-read every iteration (never cached)
- Failures are logged to TSV (persistent, not in context)
- Churn detection auto-stops before context exhaustion

## Team Agents + Context

Team dispatch is the best context management strategy:
- Each agent gets **fresh context** with only its input
- Handoffs via filesystem, not conversation history
- Orchestrator context stays minimal

## Checkpoint Protocol (Save Game)

Before long-running work, save state:

```bash

# Save checkpoint (records git SHA, in-progress tasks, progress)
cc-flow checkpoint save --name "before-auth-refactor"

# After compaction or session restart:
cc-flow checkpoint restore latest
# → Prints: branch, SHA, in-progress tasks, progress
```

**What to checkpoint:**
| When | What to Save | Where |
|------|-------------|-------|
| Before risky refactor | `cc-flow checkpoint save` | .tasks/.checkpoints/ |
| Research findings | Write to file | /tmp/cc-team-research.md |
| Design decisions | Task spec or epic spec | .tasks/tasks/*.md |
| Current approach | cc-flow learn | .tasks/learnings/ |

## Token Budget Estimation

| Action | Estimated Tokens |
|--------|-----------------|
| Read a 200-line file | ~3,000 |
| Grep results (20 matches) | ~1,000 |
| Agent dispatch (full cycle) | ~5,000-15,000 |
| Autoimmune iteration | ~8,000-20,000 |
| Research phase (4 layers) | ~10,000-25,000 |

**Rule:** If remaining context < 30%, compact or dispatch to subagent.

## Recovery Playbook (After Compaction)

```
1. Re-orient:
   $ cc-flow dashboard              # Where am I?
   $ cc-flow show <current-task>     # What was I doing?
   $ git log --oneline -5            # What did I just commit?
   $ git diff --stat                 # Uncommitted changes?

2. Restore context:
   $ cc-flow checkpoint restore latest   # Resume point
   $ cat /tmp/cc-team-*.md 2>/dev/null   # Handoff files

3. Continue:
   $ cc-flow next                    # What's next?
```


## On Completion

When done:
```bash
cc-flow skill ctx save cc-context-tips --data '{"done": true}'
cc-flow skill next
```

## Related Skills

- **cc-worker-protocol** — fresh context per task
- **cc-teams** — agent dispatch preserves orchestrator context
- **cc-autoimmune** — built-in context-friendly loop design
- **cc-task-tracking** — persist state to files, not memory
