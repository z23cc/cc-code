---
description: "Tool selection priority — prefer MCP tools (morph, RepoPrompt) over built-in when available"
alwaysApply: true
---

# Tool Priority Rules

## File Editing
1. `edit_file` (morph MCP) — Fast Apply, 10x faster. Use for ALL single-file edits.
2. `rp apply_edits` (rp-cli) — Multi-file batch edits with auto-repair.
3. Built-in Edit/Write — Fallback if MCP tools fail.

## Code Search
1. `codebase_search` (morph MCP) — Semantic search. Use FIRST for broad exploration.
2. `file_search` (RepoPrompt) — Combined content + path + regex, 80% fewer tokens.
3. Built-in Grep/Glob — Use for exact regex patterns or targeted searches.

## Code Understanding
1. `context_builder` (rp-cli) — Deep cross-file AI analysis. Use for architecture Q&A.
2. `get_code_structure` (rp-cli) — Function/type signatures. Use for structure overview.
3. Built-in Read + Grep — Manual tracing. Fallback only.

## Code Review
1. `context_builder --response-type review` — AI-powered review with git diff context.
2. Agent dispatch (code-reviewer, python-reviewer) — Standard review pipeline.

## DO NOT
- Use Grep for "how does X work" questions (use codebase_search)
- Use codebase_search for exact string matching (use Grep)
- Read entire files when you only need signatures (use get_code_structure)
- Manually trace multi-file dependencies (use context_builder)
