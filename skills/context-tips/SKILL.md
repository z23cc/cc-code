---
name: context-tips
description: >
  Context window management for long sessions. When to compact, how to
  preserve critical info, and how to structure work to avoid context overflow.
  TRIGGER: 'context full', 'running out of context', 'session too long',
  'compact', '上下文快满了'.
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

## Related Skills

- **worker-protocol** — fresh context per task
- **teams** — agent dispatch preserves orchestrator context
- **autoimmune** — built-in context-friendly loop design
- **task-tracking** — persist state to files, not memory
