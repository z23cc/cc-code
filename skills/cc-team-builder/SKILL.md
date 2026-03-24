---
name: cc-team-builder
description: >
  Dynamic team composition — analyze a task and recommend the optimal agent
  combination. Smarter than fixed templates: considers task type, codebase
  language, file types changed, and past team success rates.
  TRIGGER: 'build team', 'which agents', 'who should work on this',
  'team composition', 'optimal team', '组队', '用哪些agent', '最佳团队'.
  NOT FOR: dispatching an existing team — use cc-teams. NOT FOR: parallel execution — use cc-parallel-agents.
  FLOWS INTO: cc-teams (dispatch the recommended team), cc-work (execute with team).
---

# Team Builder — Dynamic Agent Composition

## Purpose

Fixed team templates (feature-dev, bug-fix, review) work for common cases. But for cross-domain tasks, you need a custom team. This skill analyzes the task and recommends the optimal agent combination.

## Process

### Step 1: Analyze the Task
Read the task description, affected files, and requirements to determine:

| Signal | Agents Triggered |
|--------|-----------------|
| `.py` files | python-reviewer |
| `.ts/.tsx` files | code-reviewer (typescript lens) |
| SQL/migrations | db-reviewer |
| Auth/secrets/input validation | security-reviewer |
| New API endpoints | code-reviewer + security-reviewer |
| Performance concerns | researcher (profiling) |
| UI/frontend | code-reviewer (UI lens) |
| Architecture changes | architect + code-reviewer |
| >50 files changed | parallel dispatch recommended |

### Step 2: Check Past Success
Query wisdom system for past team outcomes:
```bash
cc-flow wisdom search "team"
cc-flow chain stats
```

Boost teams that succeeded before on similar tasks.

### Step 3: Recommend Team

```markdown
## Recommended Team: [Task Name]

### Core (Required)
1. **researcher** — map affected code before changes
2. **python-reviewer** — Python code quality (detected: 12 .py files)

### Specialists (Recommended)
3. **security-reviewer** — auth changes detected (src/auth/*.py)
4. **db-reviewer** — migration files present

### Optional
5. **refactor-cleaner** — if code complexity > threshold

### Execution Mode
- **Sequential** (recommended for this task — dependencies between steps)
- Alternative: Parallel (researcher + security-reviewer can run together)

### Estimated Review Loops
- 2 loops (based on 45 files changed, medium complexity)
```

### Step 4: Output Dispatch Command

```bash
# Dispatch the recommended team:
/cc-team feature-dev --agents researcher,python-reviewer,security-reviewer,db-reviewer

# Or use parallel dispatch:
/cc-parallel-agents --agents researcher,security-reviewer --then python-reviewer,db-reviewer
```

## On Completion

```bash
cc-flow skill ctx save cc-team-builder --data '{"team": ["researcher", "python-reviewer", "security-reviewer"], "mode": "sequential", "reason": "auth + db changes detected"}'
cc-flow skill next
```

## Related Skills

- **cc-teams** — fixed team templates (dispatches teams)
- **cc-parallel-agents** — parallel agent execution
- **cc-work** — uses teams for task execution
