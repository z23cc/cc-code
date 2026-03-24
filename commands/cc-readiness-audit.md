---
description: >
  8-pillar project readiness assessment. Checks agent readiness (can Claude work here?)
  and production readiness (is this deployable?). Auto-fixes agent issues, reports production issues.
  TRIGGER: 'audit project', 'is this ready', 'readiness check', 'project health'.
  FLOWS INTO: cc-deploy.
---

Activate the cc-readiness-audit skill.

## 8 Pillars

### Agent Readiness (auto-fix offered)
1. **Code Style & Validation** — ruff, black, eslint, prettier
2. **Build & Type Check** — py_compile, mypy, tsc, go build
3. **Testing** — pytest, npm test, go test (target 60%+ coverage)
4. **Documentation** — README.md, CLAUDE.md, pyproject.toml
5. **Dev Environment** — .gitignore, .env.example, venv

### Production Readiness (report only)
6. **Observability** — structured logging, health check, error tracking
7. **Security** — bandit, pip-audit, secrets, CORS
8. **CI/CD & Workflow** — CI pipeline, pre-commit hooks, Dockerfile

## Output

Agent Readiness Score: N/5 (with auto-fix option)
Production Readiness Score: N/3 (recommendations only)
