---
name: cc-readiness-audit
description: >
  8-pillar project readiness assessment. Checks agent readiness (can Claude work
  here effectively?) and production readiness (is this deployable?).
  Fixes agent-readiness issues only; reports production issues without changing.
  TRIGGER: 'audit project', 'is this ready', 'readiness check', 'project health',
  '项目体检', '准备好了吗', '项目审计'.
  NOT FOR: code review — use cc-review. NOT FOR: security audit — use cc-scout-security.
---

# Readiness Audit — 8 Pillars

## Two-Tier Philosophy

- **Pillars 1-5 (Agent Readiness)**: Can Claude Code work effectively here? → **Auto-fix offered**
- **Pillars 6-8 (Production Readiness)**: Is this deployable? → **Report only, user decides**

## The 8 Pillars

### Pillar 1: Code Style & Validation ⚡ auto-fix

Auto-detect language and run appropriate linter:

| Language | Lint | Format | Fix |
|----------|------|--------|-----|
| Python | `ruff check .` | `black --check .` | `ruff check --fix .` |
| JS/TS | `npx eslint .` | `npx prettier --check .` | `npx eslint --fix .` |
| Go | `golangci-lint run` | `gofmt -l .` | `golangci-lint run --fix` |
| Rust | `cargo clippy` | `cargo fmt --check` | `cargo clippy --fix` |

### Pillar 2: Build & Type Check ⚡ auto-fix

| Language | Build | Types |
|----------|-------|-------|
| Python | `python -m py_compile` | `mypy .` |
| JS/TS | `npx tsc --noEmit` | built-in |
| Go | `go build ./...` | built-in |
| Rust | `cargo check` | built-in |

### Pillar 3: Testing ⚡ auto-fix

Auto-detect test framework:

| Language | Test | Coverage |
|----------|------|----------|
| Python | `pytest` | `pytest --cov` |
| JS/TS | `npm test` | `npx c8` or `jest --coverage` |
| Go | `go test ./...` | `go test -cover ./...` |
| Rust | `cargo test` | `cargo llvm-cov` |

| Check | Pass | Fail Action |
|-------|------|-------------|
| Tests pass | 0 failures | Fix failing tests |
| Coverage ≥ 60% | met | Add tests for uncovered code |

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
CCFLOW="python3 ${CLAUDE_PLUGIN_ROOT}/scripts/cc-flow.py"
$CCFLOW epic create --title "Audit fixes $(date +%Y-%m-%d)"
# For each Pillar 1-5 finding:
$CCFLOW task create --epic <epic-id> --title "[P1] Fix ruff: 3 unused imports"

# Option 3: Run autoimmune scan directly
# /autoimmune scan — does a similar scan + auto-generates the task list
```

## Related Skills

- **cc-autoimmune** — audit findings feed into improvement loop (Mode D does similar scan)
- **cc-scaffold** — generates a project that passes all 8 pillars from the start
- **cc-security-review** — deep dive for Pillar 7 findings
- **cc-deploy** — addresses Pillar 6 and 8 patterns
- **cc-logging** — addresses Pillar 6 structured logging
