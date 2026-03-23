---
name: cc-rp
description: >
  Unified RepoPrompt interface — auto-routes between rp-cli and MCP.
  Use for file selection, context builder, code review, chat, search,
  codemaps, git, and workspace management via RepoPrompt.
  TRIGGER: 'repoprompt', 'rp', 'builder', 'codemap', 'rp review',
  'context builder', 'repo prompt', '代码分析', '上下文构建'.
  NOT FOR: simple grep searches, single-file reads.
---

# RepoPrompt Integration — Dual Transport

cc-code wraps RepoPrompt via **two transports** with automatic routing:

| Transport | Best for | How it works |
|-----------|----------|-------------|
| **CLI** (`rp-cli`) | Scripts, Ralph, chaining, piping | Each call is independent, pass -w/-t every time |
| **MCP** (Claude Code native) | Interactive sessions, persistent binding | Bind once with select_tab, persists for session |

## Transport Selection

Auto-detected. Override with:

```bash
# Env var
CC_RP_TRANSPORT=cli   # Force CLI
CC_RP_TRANSPORT=mcp   # Force MCP

# Config
cc-flow config set rp.transport cli
cc-flow config set rp.transport mcp
```

**Auto rules:**
- Ralph mode (`CC_RALPH=1`) → CLI (needs chaining + timeout)
- Claude Code session → MCP (persistent binding)
- cc-flow CLI scripts → CLI (subprocess)
- Default → CLI

## Check What's Available

```bash
cc-flow rp check
```

Returns:
```json
{
  "transports": {
    "cli": {"available": true, "path": "/usr/local/bin/rp-cli"},
    "mcp": {"available": true}
  },
  "active_transport": "mcp"
}
```

## CLI Transport Usage

All operations go through `cc-flow rp <command>`:

```bash
# Explore
cc-flow rp windows                          # List windows
cc-flow rp tree -w 1                        # File tree
cc-flow rp structure -w 1 src/auth/         # Codemaps
cc-flow rp search "TODO" -w 1               # Search

# Selection (= context for chat)
cc-flow rp select set src/ -w 1             # Set selection
cc-flow rp select add lib/utils.py -w 1     # Add to selection
cc-flow rp select get -w 1                  # View selection

# Context Builder (auto-selects files)
cc-flow rp builder "find auth code" -w 1                    # Context only
cc-flow rp builder "explain auth" -w 1 --type question      # Build → answer
cc-flow rp builder "add logout" -w 1 --type plan            # Build → plan
cc-flow rp builder "review changes" -w 1 --type review      # Build → review

# Chat
cc-flow rp chat "How does auth work?" -w 1                  # Continue chat
cc-flow rp chat "New topic" -w 1 --new                      # New chat
cc-flow rp chat -w 1 --message-file /tmp/review-prompt.md --new  # From file

# Git via RP
cc-flow rp git status -w 1
cc-flow rp git diff -w 1 --detail patches --compare staged
cc-flow rp git log -w 1 --count 10

# Edit via RP
cc-flow rp edit src/main.py --search-text "old" --replace-text "new" -w 1

# Workspace management
cc-flow rp workspace list -w 1
cc-flow rp workspace create MyProject --folder-path /path --new-window

# Session (persist window/tab across calls)
cc-flow rp session show                     # View saved W/T
cc-flow rp session clear                    # Reset

# Export
cc-flow rp prompt export ~/context.md -w 1  # Full LLM context

# Raw passthrough
cc-flow rp run "select set src/ && context --all" -w 1  # Chain commands
```

## MCP Transport Usage (Preferred)

RP MCP is auto-connected via `discover-agent.json` — no manual config needed.
**Always prefer MCP tools over CLI when in Claude Code sessions.**

```
# These are Claude Code MCP tools — use directly, no cc-flow needed
mcp__RepoPrompt__file_search(pattern="auth", filter={"extensions": [".py"]})
mcp__RepoPrompt__context_builder(instructions="find auth code", response_type="question")
mcp__RepoPrompt__chat_send(message="How does this work?", new_chat=true)
mcp__RepoPrompt__read_file(path="src/main.py")
mcp__RepoPrompt__get_file_tree(max_depth=2)
mcp__RepoPrompt__get_code_structure(paths=["src/auth/"])
mcp__RepoPrompt__workspace_context(include=["prompt", "selection", "code"])
mcp__RepoPrompt__git(op="diff", compare="staged", detail="patches")
mcp__RepoPrompt__apply_edits(path="f.py", search="old", replace="new")
mcp__RepoPrompt__manage_selection(op="set", paths=["src/"])
```

**MCP advantages over CLI:**
- **Zero latency** — in-process, no subprocess spawn
- **Tab binding** — `manage_workspaces(action="select_tab")` once, all calls auto-target
- **Structured JSON** — native responses, no text parsing
- **Worktree targeting** — `git(op="status", repo_root="@main:<branch>")` without workspace switch

**MCP tool names:**

| Shorthand | MCP Tool | Best for |
|-----------|----------|----------|
| search | `file_search` | Code search (~80% fewer tokens than Grep) |
| builder | `context_builder` | Deep cross-file AI analysis |
| chat | `chat_send` | Conversational AI (plan/edit/review/chat modes) |
| read | `read_file` | Read with line ranges |
| tree | `get_file_tree` | Project overview |
| structure | `get_code_structure` | Function/type signatures |
| edit | `apply_edits` | Multi-edit transactions |
| select | `manage_selection` | Curate file context |
| git | `git` | Read-only git with worktree targeting |
| context | `workspace_context` | Snapshot of workspace state |
| prompt | `prompt` | Get/set/export prompt |
| chats | `chats` | Chat history |
| models | `list_models` | Available AI presets |
| file | `file_actions` | Create/delete/move files |
| workspace | `manage_workspaces` | Workspace + tab management |
| windows | `list_windows` | Window discovery |

## Key Concept: Selection = Context

The tab's file selection IS the context for chat. The AI only sees selected files.

```
# Manual: curate selection yourself
cc-flow rp select set src/auth/ src/api/
cc-flow rp chat "How does auth work?"

# Auto: let context_builder pick files
cc-flow rp builder "How does auth work?" --type question
```

## Review Flow (CLI Transport)

```bash
# 1. Setup: pick window + run builder (ONCE)
cc-flow rp setup-review --summary "Review auth changes"
# Saves W/T to session — subsequent calls auto-use them

# 2. Add changed files
CHANGED=$(git diff main..HEAD --name-only)
for f in $CHANGED; do
  cc-flow rp select add "$f"
done

# 3. Get builder context
cc-flow rp prompt get > /tmp/handoff.md

# 4. Send review (with criteria + verdict tag requirement)
cc-flow rp chat --message-file /tmp/review-prompt.md --new --chat-name "Review: feature-auth"

# 5. Re-review (NO --new, keep context)
cc-flow rp chat --message-file /tmp/re-review.md
```

## Worktree Integration

### MCP: Query worktrees without switching workspace

```
# Status by branch name (no workspace switch needed)
mcp__RepoPrompt__git(op="status", repo_root="@main:feature-auth")

# Diff vs trunk
mcp__RepoPrompt__git(op="diff", repo_root="@main:feature-auth", compare="main", detail="files")

# Main checkout status
mcp__RepoPrompt__git(op="status", repo_root="@main")
```

### CLI: Workspace per worktree

```bash
# Create workspace for worktree
cc-flow rp worktree-setup .claude/worktrees/feature-auth

# Query by branch (no workspace switch)
cc-flow rp worktree-status feature-auth
cc-flow rp worktree-diff feature-auth --detail patches

# Clean up when worktree removed
cc-flow rp worktree-cleanup .claude/worktrees/feature-auth
```

### Worktree Boundary Guard

When `CC_WORKTREE_PATH` is set (by `/cc-work --branch=worktree`), the
`worktree-guard.sh` hook **blocks** Edit/Write operations targeting files
outside the assigned worktree. Shared state dirs (`.tasks/`, `.flow/`) are allowed.

Session state (window/tab binding) is stored in `.git/cc-flow-state/rp-session.json`,
shared across all worktrees in the same repo.

## Related Skills

- **cc-review-backend** — multi-backend review routing (agent/rp/codex/export)
- **cc-worktree** — worktree management + boundary enforcement
- **cc-work** — execution pipeline uses RP for review when backend=rp
- **cc-ralph** — autonomous loop uses RP via CLI transport
- **cc-worker-protocol** — documents CC_WORKTREE_PATH boundary guard
