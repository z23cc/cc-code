---
name: search-strategy
description: >
  Multi-tool search strategy — choose the right search tool for each task.
  Combines rg (exact), semantic search (meaning), symbol search (definitions),
  and AST matching (structure) for maximum efficiency.
  TRIGGER: searching codebase, exploring code, finding where X is used,
  understanding architecture, refactoring, security audit, '搜索', '查找'.
---

# Search Strategy — Right Tool for the Job

## Decision Framework

```
Do you know the exact text/pattern?
├─ YES → rg / Grep (fastest, ~20ms)
└─ NO → What are you looking for?
         ├─ Meaning/concept → Semantic search (grepai / codebase_search)
         ├─ Function/class definition → Symbol search (Serena / get_code_structure)
         ├─ Code structure/pattern → AST matching (ast-grep)
         └─ Dependency chain → Trace tools (grepai trace / call graph)
```

## Tool Matrix

| Task | Best Tool | Speed | When to Use |
|------|-----------|-------|-------------|
| Find exact string | `rg` / Grep | ~20ms | You know the text: class name, error message, config key |
| Find by meaning | Semantic search | ~500ms | "Where is auth handled?", "How does billing work?" |
| Find definitions | Symbol search | ~100ms | "Where is UserService defined?", function signatures |
| Find code patterns | AST grep | ~200ms | "All async functions that call X", structural refactoring |
| Trace dependencies | Call graph | ~2s | "What calls this function?", impact analysis |
| Find files by name | Glob | instant | "Find all test files", "Where is config.py?" |

## Available Tools (Priority Order)

### 1. rg / Built-in Grep — Always Available
```
Grep: exact regex patterns, keyword matches
Glob: file name patterns
```
**Use for:** Error messages, import statements, config values, string literals, TODO markers.

### 2. Morph codebase_search — Semantic (if MCP available)
```
codebase_search: natural language queries about code meaning
```
**Use for:** "How does the auth flow work?", "Where is payment processing?", broad exploration.
**NOT for:** Exact keyword matching (use Grep instead — faster and precise).

### 3. RepoPrompt — Structure & Deep Analysis (if MCP available)
```
file_search: combines content + path + regex in one call
get_code_structure: function/type signatures for a file
context_builder: deep cross-file AI analysis
```
**Use for:** Architecture understanding, code review, planning changes.

### 4. ast-grep — Structural Patterns (if installed)
```bash
ast-grep --pattern 'async def $FUNC($$$ARGS)' --lang python
ast-grep --pattern 'except: pass' --lang python  # Find bare excepts
```
**Use for:** Large-scale refactoring, finding anti-patterns, structural code search.

## Workflow Recipes

### Recipe 1: Codebase Exploration (new to the project)

```
Step 1: Semantic discovery — "How does X work?"
  → codebase_search / context_builder

Step 2: Structure overview — function signatures, class hierarchy
  → get_code_structure / Grep for class definitions

Step 3: Dependency mapping — what depends on what?
  → Grep for imports, call sites

Step 4: Exact details — specific implementation
  → Grep / Read specific files
```

### Recipe 2: Refactoring Safely

```
Step 1: Find all usages — who calls this function?
  → Grep for function name across codebase

Step 2: Understand call patterns — how is it called?
  → Read each call site, check argument patterns

Step 3: Find structural matches — similar patterns to change
  → ast-grep for code structure (if available)
  → Grep with regex for simpler patterns

Step 4: Verify impact — what tests cover this?
  → Grep for function name in tests/
```

### Recipe 3: Security Audit

```
Step 1: Semantic scan — "Where is user input handled?"
  → codebase_search

Step 2: Pattern scan — known vulnerability patterns
  → Grep: "shell=True", "yaml.load(", ".format(" in SQL context
  → ast-grep: subprocess with shell=True (if available)

Step 3: Trace data flow — input → processing → output
  → Grep for variable names through the chain

Step 4: Check boundaries — validation at entry points
  → Grep in API routes/views for validation decorators
```

### Recipe 4: Performance Investigation

```
Step 1: Find hotspot — which function is slow?
  → Profile first (see performance skill), then search

Step 2: Find N+1 patterns
  → Grep for queries inside loops
  → Grep: "for .* in .*:" near "query\|select\|fetch"

Step 3: Find blocking calls in async
  → Grep: "time.sleep\|requests\.\|open(" in async functions

Step 4: Check caching opportunities
  → Grep for repeated identical calls, missing @lru_cache
```

## Common Pitfalls

| Mistake | Why It's Wrong | Do Instead |
|---------|---------------|------------|
| Semantic search for exact string | Slow + imprecise for known text | Use Grep |
| Regex for "how does X work" | Too literal, misses concepts | Use semantic search |
| Refactoring without checking call sites | Breaking changes | Grep for all usages first |
| Reading entire files to find one function | Wastes context window | Use Grep or symbol search |
| Only using one tool | Misses results other tools would find | Layer tools: broad → narrow |

## Speed vs. Token Cost

| Tool | Speed (500k lines) | Tokens Used | Best For |
|------|-------------------|-------------|----------|
| rg / Grep | ~0.2s | ~500 | 90% of searches |
| Symbol search | ~1.5s | ~1000 | Definition lookup |
| Semantic search | ~2.5s | ~2000 | Exploration |
| AST grep | ~3.0s | ~1500 | Structural patterns |

**Rule of thumb:** Start with the fastest tool that could work. Escalate to slower tools only when the fast one doesn't find what you need.

## Example Outputs

**Grep** — exact matches with context:
```
src/auth/middleware.py:45:    if not token.is_valid():
src/auth/middleware.py:46:        raise AuthError("Token expired")
src/api/users.py:12:    token = request.headers.get("Authorization")
```

**Semantic search** — conceptual matches:
```
Found 3 relevant results for "how is authentication handled":
1. src/auth/middleware.py — AuthMiddleware class, validates JWT tokens
2. src/auth/oauth.py — OAuth2 flow implementation
3. src/config/security.py — AUTH_SECRET and token expiry settings
```

**Symbol search** — definitions:
```
class AuthMiddleware     src/auth/middleware.py:10
  def authenticate()     src/auth/middleware.py:25
  def refresh_token()    src/auth/middleware.py:55
class OAuthProvider      src/auth/oauth.py:8
```

## Related Skills

- **debugging** — use search strategy during Phase 1 (root cause investigation)
- **performance** — Recipe 4 for performance investigation
- **security-review** — Recipe 3 for security audits
- **python-patterns** — what patterns to search for
