---
name: cc-scout-docs
description: >
  Find the most relevant framework/library documentation for the requested change.
  Fetches version-specific docs, source code references, and known issues.
  TRIGGER: 'find docs for', 'what does the API say', 'check the docs', '查文档', '看看文档怎么说', '查API'.
  NOT FOR: checking if YOUR docs are stale — use cc-scout-docs-gap instead.
---

# Docs Scout — Find Relevant Documentation

## Purpose

Research-only. Locate official documentation, source code, and known issues for the frameworks and libraries involved in a change.

## Search Strategy

### 1. Identify Versions

```bash
# Python
grep -A5 "\[project\]" pyproject.toml      # Python version
grep "requires" pyproject.toml | head -10   # Dependencies + versions
pip show [package] 2>/dev/null | grep Version

# JS/TS
cat package.json | python3 -c "import sys,json; d=json.load(sys.stdin); [print(f'{k}: {v}') for k,v in {**d.get('dependencies',{}), **d.get('devDependencies',{})}.items()]" | head -10

# Go
grep -v "^$\|^module\|^go " go.mod | head -10
```

### 2. Fetch Official Docs

```bash
# WebFetch version-specific docs
WebFetch: https://docs.python.org/3.12/library/[module].html
WebFetch: https://fastapi.tiangolo.com/[feature]/
```

### 3. Source Code Dive (for undocumented behavior)

```bash
# Find actual implementation when docs are unclear
gh search code "def [function_name]" --owner [org] --language python -L 5
# Then read the source
gh api repos/[owner]/[repo]/contents/[path] --jq '.content' | base64 -d | head -50
```

### 4. Check Known Issues

```bash
# Search for gotchas
gh search issues "[feature] bug" --repo [framework/repo] --state open -L 5
```

## Output Format

```markdown
## Documentation for [Feature]

### Primary Framework
- [Framework] v[X.Y]: [doc URL]
- Key API: [function/class] — [what it does]

### Libraries
- [Library] v[X.Y]: [doc URL]

### API Quick Reference
- `function(param: type) -> return` — [one-line description]

### Known Issues
- [Issue title] — [workaround if any]

### Version Notes
- [Breaking change or deprecation relevant to this version]

### Sources
- [Official docs URL]
- [Source code URL]
```

## Rules

- Always check the EXACT version in use, not just "latest"
- Prefer official docs > source code > blog posts
- Flag version-specific gotchas prominently

## Related Skills

- **cc-scout-practices** — community best practices beyond official docs
- **cc-research** — deeper codebase investigation
- **cc-prompt-engineering** — docs for LLM/AI libraries
