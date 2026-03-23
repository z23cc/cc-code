---
name: cc-scout-build
description: >
  Analyze build system, scripts, CI/CD configuration, and monorepo setup.
  Reports build health score.
  TRIGGER: 'check build', 'how does the build work', 'CI config', 'CI/CD', 'monorepo',
  '构建配置', 'CI 怎么设置的', '构建系统'.
  NOT FOR: fixing build errors — use cc-fix instead.
---

# Build Scout — Build System Audit

## Scan Checklist

### 1. Build Tool Detection

```bash
# Python
ls -la pyproject.toml setup.py setup.cfg Makefile 2>/dev/null
grep "\[build-system\]" pyproject.toml 2>/dev/null
grep "build-backend" pyproject.toml 2>/dev/null

# JS/TS
ls -la vite.config.* webpack.config.* next.config.* rollup.config.* 2>/dev/null
grep '"build"' package.json 2>/dev/null

# Go
ls -la go.mod Makefile 2>/dev/null
# Rust
ls -la Cargo.toml 2>/dev/null
```

### 2. Scripts

```bash
# Python (Makefile / pyproject scripts)
head -50 Makefile 2>/dev/null
grep "\[project.scripts\]\|\[tool.poetry.scripts\]" pyproject.toml 2>/dev/null

# JS/TS
python3 -c "import json; d=json.load(open('package.json')); [print(f'  {k}: {v}') for k,v in d.get('scripts',{}).items()]" 2>/dev/null
```

### 3. CI/CD

```bash
ls -la .github/workflows/*.yml 2>/dev/null
ls -la .gitlab-ci.yml Jenkinsfile .circleci/ 2>/dev/null
# Scan CI for build/test/deploy steps
grep -l "build\|test\|deploy" .github/workflows/*.yml 2>/dev/null
```

### 4. Output & Artifacts

```bash
ls -d dist/ build/ .next/ target/ 2>/dev/null
grep "dist\|build\|__pycache__" .gitignore 2>/dev/null
```

## Output Format

```markdown
## Build System

| Dimension | Status | Details |
|-----------|--------|---------|
| Language | [detected] | [version] |
| Build tool | [name] | [config file] |
| Build command | [cmd] | [output dir] |
| Dev command | [cmd] | [hot reload?] |
| CI/CD | OK/MISSING | [platform + workflows] |
| Artifacts gitignored | OK/WARN | [dist/ in .gitignore?] |

### Scripts Summary
| Script | Command |
|--------|---------|
| build | [command] |
| test | [command] |
| lint | [command] |
| dev | [command] |

### Build Health Score: X/5

### Recommendations
1. [Priority fix]
```

## Related Skills

- **cc-scout-tooling** — lint/format/type check tools
- **cc-scout-testing** — test commands and CI
- **cc-scout-env** — environment setup for builds
