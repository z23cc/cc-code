---
description: "Tool selection priority — prefer cc-flow CLI and rp-cli over built-in tools"
alwaysApply: true
---

# Tool Priority Rules

## File Editing (highest → lowest)
1. `cc-flow apply --file X --instruction Y` — Morph Fast Apply, 10x faster. Use for single-file edits.
2. `rp apply_edits` (rp-cli) — Multi-file batch edits with auto-repair.
3. Built-in Edit — Use for precise, targeted edits.
4. Built-in Write — Use only for new files or full rewrites.

## Code Search (highest → lowest)
1. `cc-flow search "query"` — Morph WarpGrep semantic search. Use FIRST for broad exploration.
2. `cc-flow search "query" --rerank` — Grep + Morph Rerank for relevance sorting.
3. `rp search "pattern"` (rp-cli) — Combined content + path + regex search.
4. Built-in Grep — Use for exact regex patterns or targeted lookups.
5. Built-in Glob — Use for finding files by name pattern.

## Code Understanding
1. `rp builder "question"` (rp-cli) — Deep cross-file AI analysis. Use before complex changes.
2. `rp structure src/` (rp-cli) — Function/type signatures overview.
3. Built-in Read + Grep — Fallback.

## Code Embedding
1. `cc-flow embed --input "code"` — Morph 1536-dim vectors for similarity search.

## Text Compression
1. `cc-flow compact --file X` — Morph-powered intelligent compression.

## DO NOT
- Use Grep for "how does X work" questions → use `cc-flow search` or `rp builder`
- Read entire files when you only need signatures → use `rp structure`
- Manually trace multi-file dependencies → use `rp builder`
- Read entire files when you only need a few lines → use Read with offset/limit
