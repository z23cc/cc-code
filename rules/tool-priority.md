---
description: "Tool selection priority — prefer MCP tools and cc-flow over built-in tools"
alwaysApply: true
---

# Tool Priority Rules

## File Editing (highest → lowest)
1. `edit_file` (Morph MCP) — Fast Apply, accepts partial snippets, 10x faster. Use for ALL single-file edits.
2. `cc-flow apply --file X --instruction Y` — CLI wrapper for Morph Apply. Use when MCP unavailable.
3. `rp apply_edits` (rp-cli) — Multi-file batch edits with auto-repair.
4. Built-in Edit/Write — Fallback only.

## Code Search (highest → lowest)
1. `codebase_search` (Morph MCP) — Semantic search subagent. Use FIRST for broad exploration ("how does X work").
2. `cc-flow search "query" --rerank` — CLI search with Morph Rerank for relevance sorting.
3. `file_search` (RepoPrompt MCP) — Combined content + path + regex, ~80% fewer tokens.
4. Built-in Grep/Glob — Use for exact regex patterns or targeted file lookups.

## Code Understanding
1. `context_builder` (RepoPrompt MCP) — Deep cross-file AI analysis. Use before complex changes.
2. `get_code_structure` (RepoPrompt MCP) — Function/type signatures overview.
3. Built-in Read + Grep — Fallback.

## Code Embedding
1. `cc-flow embed --input "code"` — Morph 1536-dim vectors for similarity search.

## Text Compression
1. `cc-flow compact --file X` — Morph-powered intelligent compression.

## DO NOT
- Use Grep for "how does X work" questions → use `codebase_search` or `cc-flow search`
- Use Edit for single-file changes when `edit_file` MCP is available
- Read entire files when you only need signatures → use `get_code_structure`
- Manually trace multi-file dependencies → use `context_builder`
- Spawn sub-agents for research when `context_builder` can do it in one call
