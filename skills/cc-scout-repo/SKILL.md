---
name: cc-scout-repo
description: >
  Scan repo to find existing patterns, conventions, and related code paths
  BEFORE making changes. Prevents reinventing existing abstractions.
  TRIGGER: 'what patterns exist', 'scan the repo', 'find conventions',
  '扫描仓库', '已有什么模式'.
---

# Repo Scout — Find Existing Patterns

## Purpose

Research-only. Scan the current codebase to find patterns, conventions, and reusable code that the implementation should follow. Prevents duplicate code and convention violations.

## Tool Priority

**Use morph/rp-cli when available, Grep as fallback:**
```
morph search --query "naming conventions"    ← semantic (broad)
rp -e 'structure src/'                       ← code structure (signatures)
Grep "^class \|^def " src/                   ← exact patterns (fallback)
```

## Search Checklist

### 1. Project Conventions

```bash
# BEST: semantic search for patterns
morph search --query "naming conventions and code patterns"
rp -e 'structure src/'    # Function/class signatures

# Fallback: grep
grep -rn "^class " src/ | head -10  # Class naming convention
grep -rn "^def " src/ | head -10    # Function naming convention

# Config patterns
ls *.toml *.yaml *.json .env*     # Configuration style
```

### 2. Related Code (DO NOT DUPLICATE)

```bash
# Find similar features already implemented
grep -rn "[feature_keyword]" src/
grep -rn "class.*Service\|class.*Repository\|class.*Handler" src/

# Find reusable utilities
ls src/utils/ src/helpers/ src/common/ src/shared/ 2>/dev/null
grep -rn "def.*validate\|def.*format\|def.*parse" src/
```

### 3. Test Patterns

```bash
# How are tests organized?
find tests/ -name "*.py" | head -10
grep -rn "^class Test\|^def test_" tests/ | head -10

# Fixtures and patterns used
grep -rn "@pytest.fixture\|setUp\|tearDown" tests/ | head -5
```

### 4. Error Handling Patterns

```bash
# Custom exceptions
grep -rn "class.*Error\|class.*Exception" src/
# How errors are handled in existing code
grep -rn "except\|raise\|try:" src/ | head -10
```

## Output Format

```markdown
## Repo Scan: [Feature Area]

### Project Conventions
- Naming: [snake_case/camelCase, observed pattern]
- Structure: [how code is organized]
- Imports: [style observed]

### Related Code (REUSE THESE)
- `src/path/file.py:42` — [existing function/class that does similar work]
- `src/path/other.py:15` — [utility that should be reused]

### DO NOT DUPLICATE
- [existing abstraction] already handles [X] — use it

### Test Patterns
- Framework: [pytest/unittest]
- Style: [class-based/function-based]
- Fixtures: [what's available]

### Gotchas
- [Convention that's easy to miss]
- [Non-obvious project rule]
```

## Rules

- READ-ONLY — never modify files
- Focus on patterns the implementer needs to follow
- Flag reusable code prominently (prevent duplication)
- Note anything non-obvious about the project structure

## Related Skills

- **cc-scout-practices** — community best practices (external)
- **cc-research** — deeper investigation when scout finds complexity
- **cc-scout-testing** — detailed test infrastructure analysis
- **cc-clean-architecture** — validate found patterns against architecture rules
