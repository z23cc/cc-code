---
description: "Tool selection priority — prefer cc-flow morph commands and rp-cli over built-in tools"
alwaysApply: true
---

# Tool Priority Rules

## File Editing
1. `cc-flow apply --file X --instruction Y` — Morph Fast Apply, 10x faster. Use for single-file edits.
2. `rp apply_edits` (rp-cli) — Multi-file batch edits with auto-repair.
3. Built-in Edit/Write — Fallback.

## Code Search
1. `cc-flow search "query"` — Morph WarpGrep semantic search. Use FIRST for broad exploration.
2. `cc-flow search "query" --rerank` — Grep + Morph Rerank for relevance sorting.
3. `file_search` (RepoPrompt) — Combined content + path + regex.
4. Built-in Grep/Glob — Use for exact regex patterns.

## Code Understanding
1. `context_builder` (rp-cli) — Deep cross-file AI analysis.
2. `get_code_structure` (rp-cli) — Function/type signatures.
3. Built-in Read + Grep — Fallback.

## Code Embedding
1. `cc-flow embed --input "code"` — Morph 1536-dim vectors for similarity.

## Text Compression
1. `cc-flow compact --file X` — Morph-powered intelligent compression.

## DO NOT
- Use Grep for "how does X work" questions (use `cc-flow search`)
- Read entire files when you only need signatures (use `rp structure`)
- Manually trace multi-file dependencies (use `rp context_builder`)
