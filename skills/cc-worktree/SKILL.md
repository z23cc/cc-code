---
name: cc-worktree
description: >
  Git worktree management for parallel isolated work. Create, list, switch,
  remove, and clean up worktrees. Use for parallel workers, isolated reviews,
  or any task that needs a separate working copy.
  TRIGGER: 'worktree', 'parallel work', 'isolated branch', 'create worktree',
  '工作树', '并行开发', '隔离分支'.
  NOT FOR: simple branching — use git directly.
---

# Worktree Management

Worktree is the **default isolation mode** for `/cc-work` and Ralph. Every task
gets its own worktree under `.claude/worktrees/<task-id>/`. The worktree-guard
hook auto-detects worktree context and blocks edits outside it — no configuration needed.

## Script

All worktree operations go through the manager script:

```bash
WORKTREE_SH="${CLAUDE_PLUGIN_ROOT}/scripts/worktree.sh"

bash "$WORKTREE_SH" create <name> [base]   # Create worktree + branch + copy .env
bash "$WORKTREE_SH" list                    # Show all worktrees
bash "$WORKTREE_SH" switch <name>           # Print worktree path (for cd)
bash "$WORKTREE_SH" remove <name>           # Remove one worktree (must be clean)
bash "$WORKTREE_SH" cleanup                 # Remove all managed worktrees
bash "$WORKTREE_SH" copy-env <name>         # Copy .env* files to worktree
bash "$WORKTREE_SH" status                  # Show clean/dirty state per worktree
```

## When to Use Worktrees

| Situation | Use worktree? | Why |
|-----------|--------------|-----|
| Parallel workers on different files | **Yes** | True isolation, no conflicts |
| Quick fix while feature WIP | **Yes** | Don't stash/switch, keep both |
| Code review of another branch | **Yes** | Read-only checkout alongside main |
| Sequential tasks with deps | No | Same branch, sequential commits |
| Single small change | No | Overkill |

## Worktree + Worker Protocol

For parallel task execution, combine worktrees with the worker protocol:

```
Orchestrator (main worktree)
  ├─ Worker A → .claude/worktrees/feature-auth/    (task 1)
  ├─ Worker B → .claude/worktrees/feature-billing/ (task 2)
  └─ Worker C → .claude/worktrees/feature-api/     (task 3)
```

### Setup

```bash
WORKTREE_SH="${CLAUDE_PLUGIN_ROOT}/scripts/worktree.sh"
BASE_COMMIT=$(git rev-parse HEAD)

# Create worktrees for parallel tasks
bash "$WORKTREE_SH" create feature-auth
bash "$WORKTREE_SH" create feature-billing
bash "$WORKTREE_SH" create feature-api
```

### Dispatch Workers

Each worker gets `isolation: "worktree"` or runs in its worktree path:

```
Agent(
  prompt: "Implement auth. Work in .claude/worktrees/feature-auth/. TDD. Commit when done.",
  isolation: "worktree"
)
```

Or use the built-in Agent `isolation` parameter which auto-creates a worktree.

### Merge Back

After all workers finish:

```bash
# From main worktree
git merge feature-auth
git merge feature-billing
git merge feature-api

# Clean up
bash "$WORKTREE_SH" cleanup
```

## Worktree + Parallel Agents

When dispatching parallel agents for independent tasks:

```python
# 1. Create worktrees
bash "$WORKTREE_SH" create fix-tests
bash "$WORKTREE_SH" create fix-lint

# 2. Dispatch agents in parallel (single message, multiple Agent calls)
Agent("Fix test failures. Working dir: .claude/worktrees/fix-tests/")
Agent("Fix lint errors. Working dir: .claude/worktrees/fix-lint/")

# 3. After both complete, merge results
git merge fix-tests
git merge fix-lint

# 4. Cleanup
bash "$WORKTREE_SH" cleanup
```

## Worktree + Autoimmune

Autoimmune can use worktrees for safe experimentation:

```
Autoimmune Orchestrator
  ├─ bash worktree.sh create auto/improve-20260323
  ├─ Worker (in worktree):
  │   ├─ Implement improvement
  │   ├─ Verify: ruff + mypy + pytest
  │   └─ Commit
  ├─ PASS → merge back to main
  └─ FAIL → bash worktree.sh remove auto/improve-20260323
```

## Safety Notes

- `create` does NOT switch your current branch
- `remove` fails if worktree has uncommitted changes (safe by default)
- `cleanup` removes all managed worktrees under `.claude/worktrees/`, skips dirty ones
- `.env*` files auto-copied on create (no overwrite, symlinks skipped)
- Refuses to operate if `.claude/worktrees/` or path components are symlinks
- Worktrees live under `.claude/worktrees/` — add to `.gitignore`

## .gitignore

Add to project `.gitignore`:

```
.claude/worktrees/
```

## Related Skills

- **cc-worker-protocol** — task isolation pattern, worktree enables parallel workers
- **cc-parallel-agents** — dispatch multiple agents, each in its own worktree
- **cc-autoimmune** — autonomous improvement loop, worktree for safe experimentation
- **cc-git-workflow** — branching conventions, worktree branches follow same rules
