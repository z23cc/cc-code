---
name: cc-scout-env
description: >
  Scan environment setup — .env templates, Docker, devcontainer, setup scripts,
  runtime version pinning. Reports reproducibility score.
  TRIGGER: 'check env setup', 'environment config', 'how to set up', 'docker config',
  'devcontainer', '环境配置', '怎么搭建环境', '开发环境'.
  NOT FOR: runtime debugging — use cc-debug instead.
---

# Env Scout — Environment Setup Audit

## Scan Checklist

### 1. Environment Variables

```bash
# Template exists?
ls -la .env.example .env.template .env.sample 2>/dev/null

# .env in .gitignore?
grep "^\.env$\|^\.env\.\|\.env\.local" .gitignore 2>/dev/null

# How many vars are expected?
wc -l .env.example 2>/dev/null

# Vars used in code
grep -rn "os\.environ\|os\.getenv\|process\.env\." src/ --include="*.py" --include="*.ts" --include="*.js" 2>/dev/null | wc -l
```

### 2. Containerization

```bash
ls -la Dockerfile docker-compose.yml docker-compose.yaml 2>/dev/null
ls -la .devcontainer/devcontainer.json 2>/dev/null
```

### 3. Runtime Version Pinning

```bash
ls -la .python-version .nvmrc .node-version .tool-versions .ruby-version 2>/dev/null
grep "requires-python\|python_requires" pyproject.toml 2>/dev/null
grep '"engines"' package.json 2>/dev/null
```

### 4. Setup Process

```bash
ls -la setup.sh install.sh bootstrap.sh Makefile 2>/dev/null
grep -i "setup\|install\|getting started" README.md 2>/dev/null | head -5
```

### 5. Dependencies

```bash
# Lock files
ls -la poetry.lock requirements.txt package-lock.json yarn.lock pnpm-lock.yaml Cargo.lock go.sum 2>/dev/null
```

## Output Format

```markdown
## Environment Setup

| Check | Status | Details |
|-------|--------|---------|
| .env template | OK/MISSING | [file, N vars] |
| .env in .gitignore | OK/WARN | [covered?] |
| Docker | OK/MISSING | [Dockerfile?] |
| Devcontainer | OK/MISSING | [config?] |
| Runtime pinned | OK/MISSING | [file, version] |
| Lock file | OK/MISSING | [which one] |
| Setup docs | OK/MISSING | [README section?] |
| Setup script | OK/MISSING | [script file?] |

### Reproducibility Score: X/5
- 5: Docker + .env template + lock file + version pinning + setup docs
- 3: Some setup docs + lock file
- 1: No .env template, no lock file

### New Developer Setup Steps
1. [Inferred from existing config]
2. [Or "MISSING — recommend adding to README"]

### Recommendations
1. [Most impactful fix]
```

## Related Skills

- **cc-scout-build** — build system analysis
- **cc-scout-security** — .env secrets management
- **cc-scaffold** — project bootstrapping with proper env setup
