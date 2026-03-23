---
description: >
  Git worktree management — create, list, switch, remove, cleanup, status.
  TRIGGER: 'worktree', 'create worktree', 'list worktrees', 'parallel workspace',
  '工作树', '创建工作树', '并行工作区'.
---

Activate the cc-worktree skill. Parse the user's intent:

| Intent | Action |
|--------|--------|
| "create worktree X" / "new worktree for X" | `bash "$WORKTREE_SH" create <name> [base]` |
| "list worktrees" / "show worktrees" | `bash "$WORKTREE_SH" list` |
| "switch to worktree X" | `bash "$WORKTREE_SH" switch <name>` → print path |
| "remove worktree X" | `bash "$WORKTREE_SH" remove <name>` |
| "cleanup worktrees" | `bash "$WORKTREE_SH" cleanup` |
| "worktree status" | `bash "$WORKTREE_SH" status` |
| "copy env to X" | `bash "$WORKTREE_SH" copy-env <name>` |

Where: `WORKTREE_SH="${CLAUDE_PLUGIN_ROOT}/scripts/worktree.sh"`

## Steps

1. Set `WORKTREE_SH="${CLAUDE_PLUGIN_ROOT}/scripts/worktree.sh"`
2. Run the appropriate command based on user intent
3. Report the result

## For "create" — derive name from context

If user says "create a worktree for the auth feature":
- Name: `feature-auth` (use branch naming convention from cc-git-workflow)
- Base: default (main/master) unless user specifies

If user provides a task ID (e.g., `epic-1.2`):
- Name: the task ID or a slug derived from it
