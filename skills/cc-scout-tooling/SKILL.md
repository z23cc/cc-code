---
name: cc-scout-tooling
description: >
  Check linting, formatting, type checking, and pre-commit hook configuration.
  Reports tooling completeness score.
  TRIGGER: 'check tooling', 'lint config', 'what linters are set up', 'pre-commit hooks',
  'formatter', '检查工具链', 'lint 配置', '代码格式化'.
  NOT FOR: fixing lint errors — use cc-fix instead.
  FLOWS INTO: cc-readiness-audit.
---

# Tooling Scout — Lint/Format/Type Check Audit

## Scan Checklist

### 1. Linting

```bash
# Python
ls -la .ruff.toml ruff.toml 2>/dev/null
grep "\[tool.ruff\]" pyproject.toml 2>/dev/null
grep "ruff\|flake8\|pylint" pyproject.toml 2>/dev/null

# JS/TS
ls -la .eslintrc* eslint.config.* 2>/dev/null
grep "eslint\|biome" package.json 2>/dev/null
```

### 2. Formatting

```bash
# Python
grep "ruff format\|black\|autopep8" pyproject.toml 2>/dev/null
# JS/TS
ls -la .prettierrc* prettier.config.* 2>/dev/null
```

### 3. Type Checking

```bash
# Python
grep "\[tool.mypy\]\|mypy" pyproject.toml 2>/dev/null
grep "strict" pyproject.toml 2>/dev/null  # strict mode?
# JS/TS
ls -la tsconfig*.json 2>/dev/null
grep "\"strict\"" tsconfig.json 2>/dev/null
```

### 4. Pre-commit Hooks

```bash
ls -la .pre-commit-config.yaml .husky/ 2>/dev/null
grep -A10 "repos:" .pre-commit-config.yaml 2>/dev/null | head -15
```

## Output Format

```markdown
## Tooling Audit

| Tool | Status | Config | Command |
|------|--------|--------|---------|
| Linter | OK/MISSING | [file] | [command] |
| Formatter | OK/MISSING | [file] | [command] |
| Type checker | OK/MISSING | [file] | [command] |
| Pre-commit | OK/MISSING | [file] | [hooks] |

### Tooling Score: X/4

### Recommendations
1. [Priority 1 — most impactful]
2. [Priority 2]
```

## Related Skills

- **cc-scout-build** — build system analysis
- **cc-scout-testing** — test framework analysis
- **cc-refinement** — quality thresholds that tools enforce
