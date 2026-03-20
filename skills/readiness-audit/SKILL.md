---
name: readiness-audit
description: >
  8-pillar project readiness assessment. Checks agent readiness (can Claude work
  here effectively?) and production readiness (is this deployable?).
  Fixes agent-readiness issues only; reports production issues without changing.
  TRIGGER: 'audit project', 'is this ready', 'readiness check', 'project health', '项目体检'.
---

# Readiness Audit — 8 Pillars

## Two-Tier Philosophy

- **Pillars 1-5 (Agent Readiness)**: Can Claude Code work effectively here? → **Auto-fix offered**
- **Pillars 6-8 (Production Readiness)**: Is this deployable? → **Report only, user decides**

## The 8 Pillars

### Pillar 1: Code Style & Validation ⚡ auto-fix

```bash
ruff check . && black --check . && isort --check .
```

| Check | Pass | Fail Action |
|-------|------|-------------|
| Linter clean | 0 errors | Run `ruff check --fix .` |
| Formatter clean | 0 diffs | Run `black .` |
| Import order | sorted | Run `isort .` |

### Pillar 2: Build & Type Check ⚡ auto-fix

```bash
python -m py_compile src/**/*.py && mypy src/
```

| Check | Pass | Fail Action |
|-------|------|-------------|
| Syntax valid | All compile | Fix syntax errors |
| Types clean | 0 mypy errors | Add type annotations |

### Pillar 3: Testing ⚡ auto-fix

```bash
pytest --tb=short -q && pytest --cov=src --cov-report=term-missing
```

| Check | Pass | Fail Action |
|-------|------|-------------|
| Tests pass | 0 failures | Fix failing tests |
| Coverage ≥ 60% | met | Add tests for uncovered code |
| conftest.py exists | yes | Create with common fixtures |

### Pillar 4: Documentation ⚡ auto-fix

| Check | Pass | Fail Action |
|-------|------|-------------|
| README.md exists | yes | Create minimal README |
| CLAUDE.md exists | yes | Create with project commands |
| pyproject.toml complete | has [tool.*] sections | Add ruff/mypy/pytest config |

### Pillar 5: Dev Environment ⚡ auto-fix

| Check | Pass | Fail Action |
|-------|------|-------------|
| .gitignore exists | yes | Create with Python patterns |
| .env.example exists | yes | Create from .env (redacted) |
| Virtual env | .venv/ or similar | Note in report |

### Pillar 6: Observability 📋 report only

| Check | Status |
|-------|--------|
| Structured logging configured | ✓/✗ |
| Health check endpoint | ✓/✗ |
| Error tracking (Sentry etc.) | ✓/✗ |

### Pillar 7: Security 📋 report only

| Check | Status |
|-------|--------|
| `bandit -r src/` clean | ✓/✗ (N issues) |
| `pip-audit` clean | ✓/✗ (N vulnerabilities) |
| No secrets in code | ✓/✗ |
| CORS configured | ✓/✗ |

### Pillar 8: CI/CD & Workflow 📋 report only

| Check | Status |
|-------|--------|
| CI pipeline exists | ✓/✗ |
| Pre-commit hooks | ✓/✗ |
| Branch protection | ✓/✗ |
| Dockerfile exists | ✓/✗ |

## Output Format

```markdown
## Readiness Audit Report

### Agent Readiness (Pillars 1-5)
| Pillar | Status | Issues | Auto-fixable |
|--------|--------|--------|-------------|
| 1. Code Style | ⚠️ | 3 ruff errors | YES |
| 2. Build/Types | ✅ | 0 | - |
| 3. Testing | ⚠️ | Coverage 45% | YES (add tests) |
| 4. Documentation | ❌ | No CLAUDE.md | YES |
| 5. Dev Environment | ✅ | 0 | - |

**Agent Readiness Score: 3/5**
Shall I fix the auto-fixable issues? (Pillars 1, 3, 4)

### Production Readiness (Pillars 6-8)
| Pillar | Status | Issues |
|--------|--------|--------|
| 6. Observability | ⚠️ | No health endpoint |
| 7. Security | ❌ | 2 bandit HIGH, 1 pip-audit vuln |
| 8. CI/CD | ❌ | No CI pipeline |

**Production Readiness Score: 0/3**
These require your judgment — see recommendations below.
```

## Bridge to Autoimmune

After running `/audit`, auto-fixable findings can feed directly into `/autoimmune`:

```bash
# Option 1: Generate improvement-program.md from audit findings
# After audit prints the report, ask Claude to:
# "Convert the audit findings into improvement-program.md for autoimmune"

# Option 2: Generate .tasks/ entries
TASKCTL="python3 ${CLAUDE_PLUGIN_ROOT}/scripts/taskctl.py"
$TASKCTL epic create --title "Audit fixes $(date +%Y-%m-%d)"
# For each Pillar 1-5 finding:
$TASKCTL task create --epic <epic-id> --title "[P1] Fix ruff: 3 unused imports"

# Option 3: Run autoimmune scan directly
# /autoimmune scan — does a similar scan + auto-generates the task list
```

## Related Skills

- **autoimmune** — audit findings feed into improvement loop (Mode D does similar scan)
- **scaffold** — generates a project that passes all 8 pillars from the start
- **security-review** — deep dive for Pillar 7 findings
- **deploy** — addresses Pillar 6 and 8 patterns
- **logging** — addresses Pillar 6 structured logging
