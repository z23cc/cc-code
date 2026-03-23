---
description: "Tool selection priority — MCP first, then cc-flow CLI, then built-in tools"
alwaysApply: true
---

# Tool Priority Rules

Three tool tiers: **MCP** (in-process, fast) → **cc-flow CLI** (subprocess, rich features) → **Built-in** (fallback).
RepoPrompt MCP is auto-connected via discover-agent.json — no manual config needed.

## File Editing (highest → lowest)
1. `mcp__RepoPrompt__apply_edits` — Multi-edit transactions, auto-repair whitespace. Use for all edits when RP MCP is connected.
2. `cc-flow apply --file X --instruction Y` — Morph Fast Apply. Use for AI-guided single-file rewrites.
3. Built-in Edit — Precise, targeted edits. Fallback when MCP unavailable.
4. Built-in Write — New files or complete rewrites only.

## Code Search (highest → lowest)
1. `mcp__RepoPrompt__file_search` — Content + path + regex in one call, ~80% fewer tokens. Use FIRST.
2. `cc-flow search "query"` — Morph WarpGrep semantic search. Use for "how does X work" questions.
3. `cc-flow search "query" --rerank` — Grep + Morph Rerank for relevance sorting.
4. Built-in Grep — Exact regex patterns or targeted lookups.
5. Built-in Glob — Finding files by name pattern.

## Code Understanding (highest → lowest)
1. `mcp__RepoPrompt__context_builder` — Deep cross-file AI analysis. Auto-selects relevant files, builds optimal context. Supports response_type: question/plan/review. Use before complex changes.
2. `mcp__RepoPrompt__get_code_structure` — Function/type signatures without reading full files.
3. `mcp__RepoPrompt__get_file_tree` — Project overview with ~80% fewer tokens than `ls`.
4. `cc-flow rp builder "question"` — Same as context_builder via CLI transport. Use in scripts/Ralph.
5. Built-in Read + Grep — Fallback.

## Code Review
1. `mcp__RepoPrompt__git(op="diff", artifacts=true)` + `mcp__RepoPrompt__chat_send(mode="review")` — Full review with git diff context.
2. `/cc-review --backend=rp` — Orchestrated review pipeline (auto-selects MCP or CLI transport).
3. `/cc-review --backend=agent` — Built-in parallel reviewer agents (no RP needed).

## Git Operations
1. `mcp__RepoPrompt__git` — status/diff/log/blame with `@main:<branch>` worktree targeting.
2. Built-in Bash `git` — For commits, push, branch operations (RP git is read-only).

## Workspace & Selection
1. `mcp__RepoPrompt__manage_selection` — Curate file context for chat/review.
2. `mcp__RepoPrompt__manage_workspaces` — Tab binding, worktree workspace management.
3. `cc-flow rp select/workspace` — CLI equivalents for scripts.

## Code Embedding
1. `cc-flow embed --input "code"` — Morph 1536-dim vectors for similarity search.

## Text Compression
1. `cc-flow compact --file X` — Morph-powered intelligent compression.

## When MCP is Unavailable (Ralph, scripts, CI)
Fall back to cc-flow CLI equivalents:
- `cc-flow rp builder` instead of `context_builder`
- `cc-flow rp search` instead of `file_search`
- `cc-flow rp structure` instead of `get_code_structure`
- `cc-flow rp edit` instead of `apply_edits`

## DO NOT
- Use Grep for "how does X work" → use `file_search` or `context_builder`
- Read entire files when you only need signatures → use `get_code_structure`
- Manually trace multi-file dependencies → use `context_builder`
- Read entire files when you only need a few lines → use `read_file` with start_line/limit
- Call `rp-cli` directly via Bash → use MCP tools or `cc-flow rp` commands
