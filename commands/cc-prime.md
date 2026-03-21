---
description: "One-click project assessment — runs all scouts, generates comprehensive report with health scores. TRIGGER: 'project assessment', 'full scan', 'prime', '全面检查', '项目评估'. Use on new projects or before major changes."
---

Run a comprehensive project assessment using all cc-scout-* skills.

## Execution Order

Run these scouts in parallel where possible, then synthesize:

### Phase 1: Infrastructure (parallel)
1. **cc-scout-build** — Build system, scripts, CI/CD
2. **cc-scout-tooling** — Lint, format, type check, pre-commit
3. **cc-scout-env** — Environment, Docker, runtime pinning
4. **cc-scout-testing** — Test framework, coverage, CI

### Phase 2: Quality (parallel)
5. **cc-scout-security** — Branch protection, secrets, dependency audit
6. **cc-scout-observability** — Logging, tracing, metrics, health
7. **cc-scout-repo** — Existing patterns, conventions

### Phase 3: Synthesis
8. Combine all health scores into a dashboard

## Output Format

```markdown
# Project Assessment Report

## Health Dashboard

| Pillar | Score | Status |
|--------|-------|--------|
| Build | X/5 | [status] |
| Tooling | X/4 | [status] |
| Environment | X/5 | [status] |
| Testing | X/5 | [status] |
| Security | X/8 | [status] |
| Observability | X/6 | [status] |

## Overall: X/33 ([percentage]%)

## Top 5 Recommendations (priority order)
1. [Most critical]
2. ...

## Project Conventions Found
- [Key patterns to follow]

## Ready for Development: YES/NO
- [Blockers if any]
```

Also run `cc-flow doctor` for environment health.

After the report, suggest:
- If score < 50%: "Fix infrastructure issues first with /cc-fix"
- If score 50-80%: "Good foundation, proceed with /cc-brainstorm"
- If score > 80%: "Ready to go! Start with /cc-route"
