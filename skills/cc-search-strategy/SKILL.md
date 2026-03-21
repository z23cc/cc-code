---
name: cc-search-strategy
description: >
  Multi-tool search strategy — prioritizes morph MCP and rp-cli when available,
  falls back to built-in Grep/Glob. Choose the right tool for each task.
  TRIGGER: searching codebase, exploring code, finding where X is used,
  understanding architecture, refactoring, security audit, '搜索', '查找'.
---

# Search Strategy — Tool Priority Chain

## Priority Rule

**Always prefer MCP tools when available. Fall back to built-in tools only if MCP fails.**

```
Search Priority:
1. morph codebase_search → semantic search (broad exploration)
2. RepoPrompt file_search → combined content + path + regex
3. Built-in Grep/Glob → exact patterns (always available)

Edit Priority:
1. morph edit_file → fast apply, accepts partial snippets
2. Built-in Edit/Write → fallback

Deep Analysis Priority:
1. rp-cli context_builder → AI-powered cross-file analysis
2. rp-cli structure → function/type signatures
3. Built-in Read + Grep → manual tracing
```

## Decision Framework

```
Do you know the exact text/pattern?
├─ YES → Grep (fastest, ~20ms, always works)
└─ NO → What are you looking for?
         ├─ Meaning/concept → morph codebase_search
         ├─ Function/class definition → rp-cli get_code_structure
         ├─ Cross-file understanding → rp-cli context_builder
         ├─ Code structure/pattern → AST matching (ast-grep)
         └─ Dependency chain → Grep for imports + call sites
```

## Tool Matrix

| Task | Best Tool | Fallback | Speed |
|------|-----------|----------|-------|
| Broad exploration | `codebase_search` (morph) | Grep + Read | ~500ms |
| Exact string match | Grep (built-in) | — | ~20ms |
| File name search | `file_search` (RepoPrompt) | Glob | ~100ms |
| Code structure | `get_code_structure` (rp-cli) | Grep for def/class | ~200ms |
| Deep Q&A | `context_builder` (rp-cli) | Agent dispatch | ~3s |
| Architecture plan | `context_builder` + response_type="plan" | Manual research | ~5s |
| Code review | `context_builder` + response_type="review" | Agent dispatch | ~5s |
| Find files | Glob (built-in) | `file_search` | instant |
| AST pattern | ast-grep (if installed) | Grep regex | ~200ms |

## morph MCP Usage

```bash
# Semantic search — "how does X work?"
codebase_search: "how does the auth middleware validate tokens"
# NOT for: exact string matching (use Grep)

# Fast edit — accepts partial code snippets
edit_file: path + new content
# 10x faster than built-in Edit

# GitHub code search (no cloning needed)
github_codebase_search: "FastAPI rate limiting" in owner/repo
```

## rp-cli Usage

```bash
# Deep cross-file Q&A (AI reasoning across files)
rp -e 'builder "how does the payment system work?" --response-type question'

# Code structure overview (function/type signatures)
rp -e 'structure src/'

# Architecture planning
rp -e 'plan "Design user permissions system"'

# Code review with git diff context
rp -e 'review "What changed and is it safe?"'

# File tree (80% fewer tokens than ls/find)
rp -e 'tree'

# Search with file filter
rp -e 'search "TODO" --extensions .py'

# Read specific lines (targeted, saves tokens)
rp -e 'read src/main.py 100 50'
```

## When to Use What

| Scenario | Use morph | Use rp-cli | Use built-in |
|----------|-----------|------------|-------------|
| "How does X work?" | `codebase_search` | `context_builder` (deeper) | — |
| "Find all usages of X" | — | `file_search` | Grep |
| "What functions are in X?" | — | `get_code_structure` | Grep "def " |
| "Is this change safe?" | — | `context_builder --review` | Agent dispatch |
| "Plan how to build X" | — | `context_builder --plan` | /cc-plan |
| Quick file edit | `edit_file` | — | Edit |
| Multi-file batch edit | — | `rp apply_edits` | — |
| "Find pattern in GitHub" | `github_codebase_search` | — | `gh search code` |

## Workflow Recipes

### Recipe 1: Explore New Codebase
```
Step 1: rp -e 'tree'                              # File structure
Step 2: codebase_search "how does the main flow work"  # Broad understanding
Step 3: rp -e 'structure src/core/'                # Key signatures
Step 4: Grep for specific symbols as needed         # Details
```

### Recipe 2: Refactoring Safely
```
Step 1: Grep "function_name" src/                  # All usages (exact)
Step 2: rp -e 'builder "what depends on function_name?"'  # Impact analysis
Step 3: Apply changes with morph edit_file         # Fast edit
Step 4: Grep for function_name in tests/           # Verify test coverage
```

### Recipe 3: Security Audit
```
Step 1: codebase_search "where is user input handled"  # Semantic scan
Step 2: Grep "shell=True\|yaml.load\|\.format.*sql"    # Known patterns
Step 3: rp -e 'builder "trace user input flow"'         # Data flow analysis
```

### Recipe 4: Code Review
```
Step 1: rp -e 'review "What changed and any concerns?"'  # AI review
Step 2: Grep for patterns in the diff                      # Specific checks
```

## Common Pitfalls

| Mistake | Fix |
|---------|-----|
| Using Grep for "how does X work" | Use `codebase_search` (semantic) |
| Using `codebase_search` for exact string | Use Grep (faster, precise) |
| Reading entire files for one function | Use `get_code_structure` or targeted Read |
| Manual multi-file analysis | Use `context_builder` (AI-powered) |
| Not using morph edit_file | 10x faster than built-in Edit |

## Related Skills

- **cc-debugging** — use search strategy during Phase 1 (root cause investigation)
- **cc-performance** — Recipe 4 for performance investigation
- **cc-security-review** — Recipe 3 for security audits
- **cc-scout-context** — token-efficient exploration techniques
- **cc-research** — full 4-layer research methodology
