---
description: "Tool selection: RP MCP → cc-flow CLI → Built-in"
alwaysApply: true
---

# Tool Priority: MCP → CLI → Built-in

## Editing
1. `mcp__RepoPrompt__apply_edits` — multi-edit, auto-repair whitespace
2. Built-in Edit — fallback

## Search
1. `mcp__RepoPrompt__file_search` — content + path, ~80% fewer tokens
2. `cc-flow search "query"` — Morph semantic search
3. Built-in Grep/Glob — exact patterns

## Understanding
1. `mcp__RepoPrompt__context_builder` — deep cross-file AI analysis (question/plan/review)
2. `mcp__RepoPrompt__get_code_structure` — signatures without full reads
3. `mcp__RepoPrompt__get_file_tree` — project overview
4. Built-in Read — fallback

## Review
1. RP MCP git + chat_send(mode="review") — full diff review
2. `/cc-review` — auto-selects best backend

## Git
1. `mcp__RepoPrompt__git` — read-only (status/diff/log/blame)
2. Bash `git` — writes (commit, push)

## CLI Fallback (Ralph, scripts)
`cc-flow rp builder/search/structure/edit` — same features via CLI
