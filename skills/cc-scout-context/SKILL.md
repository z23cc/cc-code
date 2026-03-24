---
name: cc-scout-context
description: >
  Token-efficient codebase exploration. Uses file trees, code structure views,
  and targeted reads instead of full file dumps. Minimizes context consumption.
  TRIGGER: 'quick overview', 'explore the codebase efficiently', 'save context',
  'minimal tokens', '快速了解', '省 token 探索', '高效探索'.
  NOT FOR: deep cross-file analysis — use cc-research or cc-rp builder.
  FLOWS INTO: cc-research.
---

# Context Scout — Efficient Codebase Exploration

## Purpose

Research-only. Explore a codebase using minimal tokens. Use file trees and structure views instead of reading full files.

## Strategy: Progressive Depth

```
Level 1: File tree (cheapest — ~200 tokens)
    ↓ Found interesting areas?
Level 2: Code structure — function/class signatures (~500 tokens)
    ↓ Found the right file?
Level 3: Targeted read — specific line ranges (~300 tokens per read)
    ↓ Need cross-references?
Level 4: Grep for usages (~200 tokens per search)
```

**Rule:** Never read a full file if you only need part of it.

## Commands by Level (prefer cc-flow morph + rp-cli)

### Level 1: File Tree

```bash
# BEST: rp-cli (80% fewer tokens)
rp -e 'tree'

# Fallback: built-in
find . -type d -not -path '*/\.*' -not -path '*/node_modules/*' | sort | head -30
```

Token cost: ~200 (rp-cli) / ~500 (find)

### Level 2: Code Structure (signatures only)

```bash
# BEST: rp-cli
rp -e 'structure src/core/'

# Fallback: Grep
# Python: class and function signatures
grep -rn "^class \|^def \|^async def " src/ --include="*.py" | head -30

# JS/TS: exports and function signatures
grep -rn "^export \|^function \|^const .* = " src/ --include="*.ts" | head -30
```

Token cost: ~500

### Level 3: Targeted Read

```bash
# Read ONLY the lines you need
Read file.py offset=40 limit=20    # Lines 40-60 only
```

Token cost: ~300 per read

### Level 4: Cross-Reference

```bash
# Find all usages of a function (cheap)
grep -rn "function_name(" src/ | head -10
```

Token cost: ~200 per search

## Token Budget Comparison

| Approach | Tokens | Information |
|----------|--------|------------|
| Read full 500-line file | ~7,500 | Everything (mostly irrelevant) |
| Structure + targeted read | ~800 | Exactly what you need |
| **Savings** | **~90%** | Same or better understanding |

## When to Use

| Situation | Use Context Scout | Use Full Read |
|-----------|------------------|---------------|
| "How is this project structured?" | YES | NO |
| "What does function X do?" | YES (structure → targeted) | NO |
| "I need to modify lines 50-70" | YES (targeted read) | NO |
| "Debug a complex 50-line function" | NO | YES (need full context) |
| "Review a small file (<100 lines)" | NO | YES (cheap enough) |

## E2E Example

```
Question: "How does authentication work in this project?"

Level 1 (200 tokens):
  $ find src/ -type f -name "*.py" | grep -i auth
  → src/auth/middleware.py, src/auth/token.py, src/auth/oauth.py

Level 2 (400 tokens):
  $ grep -n "^class \|^def " src/auth/middleware.py
  → class AuthMiddleware:10, def authenticate:25, def refresh:55

Level 3 (300 tokens):
  $ Read src/auth/middleware.py offset=25 limit=30  # Just authenticate()
  → Sees: JWT validation → user lookup → role check

Level 4 (200 tokens):
  $ grep -rn "AuthMiddleware" src/
  → Used in: src/main.py:15 (app.add_middleware)

Total: ~1,100 tokens (vs ~15,000 for reading all 3 files fully)
Result: Complete understanding of auth flow
```

## Related Skills

- **cc-research** — deeper investigation (uses more context but finds more)
- **cc-context-tips** — managing context in long sessions
- **cc-search-strategy** — choosing the right search tool
