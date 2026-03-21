---
name: cc-search-strategy
description: >
  Multi-tool search strategy — uses cc-flow morph commands and rp-cli,
  falls back to built-in Grep/Glob. Choose the right tool for each task.
  TRIGGER: searching codebase, exploring code, finding where X is used,
  understanding architecture, refactoring, security audit, '搜索', '查找'.
---

# Search Strategy — Tool Priority Chain

## Priority Rule

**Use cc-flow morph commands first. Fall back to rp-cli, then built-in tools.**

```
Search:  cc-flow search "query"      → rp file_search → Grep
Edit:    cc-flow apply --file X      → rp apply_edits → Edit
Embed:   cc-flow embed --input X     → (no fallback)
Rerank:  cc-flow search --rerank     → (no fallback)
Compact: cc-flow compact --file X    → (no fallback)
Deep:    rp context_builder          → Read + Grep
```

## Decision Framework

```
Do you know the exact text/pattern?
├─ YES → Grep (fastest, ~20ms)
└─ NO → What are you looking for?
         ├─ Meaning/concept → cc-flow search "query"
         ├─ Function/class definition → rp structure src/
         ├─ Cross-file understanding → rp context_builder
         ├─ Relevance ranking → cc-flow search "query" --rerank
         └─ Dependency chain → Grep for imports + call sites
```

## Tool Matrix

| Task | Best Tool | Fallback | Speed |
|------|-----------|----------|-------|
| Broad exploration | `cc-flow search` | Grep + Read | ~2s |
| Exact string match | Grep (built-in) | — | ~20ms |
| File name search | Glob / `rp file_search` | — | instant |
| Code structure | `rp structure src/` | Grep def/class | ~200ms |
| Deep Q&A | `rp context_builder` | Agent dispatch | ~3s |
| Quick file edit | `cc-flow apply` | Built-in Edit | ~1s |
| Multi-file edit | `rp apply_edits` | Sequential Edit | ~2s |
| Similarity | `cc-flow embed` | — | ~500ms |
| Relevance sort | `cc-flow search --rerank` | — | ~1s |
| Text compression | `cc-flow compact` | — | ~2s |

## cc-flow Morph Commands

```bash
# Semantic search (WarpGrep — multi-turn agent)
cc-flow search "how does the auth middleware work"
cc-flow search "authentication" --rerank    # grep + relevance sorting

# Fast edit (10,500+ tok/s)
cc-flow apply --file src/app.py --instruction "add input validation" --update "snippet"

# Code embedding (1536 dims)
cc-flow embed --input "def authenticate(token): ..."

# Text compression
cc-flow compact --file long-context.txt --ratio 0.3

# GitHub search
cc-flow github-search "rate limiting" --repo fastapi/fastapi
```

## rp-cli Commands

```bash
rp -e 'tree'                                  # File tree (saves tokens)
rp -e 'structure src/'                        # Function/type signatures
rp -e 'builder "how does auth work?"'         # Deep cross-file AI analysis
rp -e 'review "What changed?"'               # AI code review
rp -e 'search "TODO" --extensions .py'        # Search with filter
rp -e 'read src/main.py 100 50'              # Targeted read
```

## When to Use What

| Scenario | Use cc-flow | Use rp-cli | Use built-in |
|----------|-------------|------------|-------------|
| "How does X work?" | `search "X"` | `context_builder` (deeper) | — |
| "Find all usages of X" | — | `file_search` | Grep |
| "What functions are in X?" | — | `structure` | Grep "def " |
| "Is this change safe?" | — | `context_builder --review` | Agent dispatch |
| Quick file edit | `apply --file X` | — | Edit |
| Similarity between code | `embed --input` | — | — |
| Rank search results | `search --rerank` | — | — |
| "Find pattern in GitHub" | `github-search` | — | `gh search code` |

## Workflow Recipes

### Recipe 1: Explore New Codebase
```
Step 1: rp -e 'tree'                          # File structure
Step 2: cc-flow search "how does the main flow work"  # Broad understanding
Step 3: rp -e 'structure src/core/'            # Key signatures
Step 4: Grep for specific symbols              # Details
```

### Recipe 2: Refactoring Safely
```
Step 1: Grep "function_name" src/              # All usages (exact)
Step 2: rp -e 'builder "what depends on function_name?"'  # Impact
Step 3: cc-flow apply --file X --instruction "rename Y"  # Fast edit
Step 4: Grep function_name in tests/           # Verify coverage
```

### Recipe 3: Security Audit
```
Step 1: cc-flow search "where is user input handled"  # Semantic scan
Step 2: Grep "shell=True\|yaml.load" src/              # Known patterns
Step 3: rp -e 'builder "trace user input flow"'        # Data flow
```

## Common Pitfalls

| Mistake | Fix |
|---------|-----|
| Grep for "how does X work" | Use `cc-flow search` (semantic) |
| Reading entire files | Use `rp structure` or targeted Read |
| Manual multi-file analysis | Use `rp context_builder` |
| Slow manual edits | Use `cc-flow apply` (10x faster) |

## Related Skills

- **cc-debugging** — use search during Phase 1 (root cause)
- **cc-performance** — search for performance anti-patterns
- **cc-security-review** — Recipe 3 for security audits
- **cc-scout-context** — token-efficient exploration
- **cc-research** — full 4-layer research methodology
