---
description: "One-click project assessment — runs all scouts in parallel, generates comprehensive report. TRIGGER: 'project assessment', 'full scan', 'prime', '全面检查', '项目评估'. Use on new projects or before major changes."
---

Run a comprehensive project assessment using **parallel scout dispatch**.

```bash
CCFLOW="python3 ${CLAUDE_PLUGIN_ROOT}/scripts/cc-flow.py"
```

## Execution: PARALLEL(all scouts) → synthesize

### Phase 1: Dispatch ALL scouts in PARALLEL

**IMPORTANT: Launch all scouts simultaneously using multiple Agent tool calls in a single message. Do NOT run them sequentially.**

Dispatch in one message:
1. **cc-scout-build** — Build system, scripts, CI/CD
2. **cc-scout-tooling** — Lint, format, type check, pre-commit
3. **cc-scout-env** — Environment, Docker, runtime pinning
4. **cc-scout-testing** — Test framework, coverage, CI
5. **cc-scout-security** — Branch protection, secrets, dependency audit
6. **cc-scout-observability** — Logging, tracing, metrics, health
7. **cc-scout-repo** — Existing patterns, conventions

Each scout is an independent Agent call — they don't depend on each other.

Also run `$CCFLOW doctor --format json` for environment health.

### Phase 2: Synthesize (after all scouts complete)

Combine all health scores:

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

## Ready for Development: YES/NO
```

After the report, suggest:
- Score < 50%: "Fix infrastructure first with /cc-fix"
- Score 50-80%: "Good foundation, proceed with /cc-brainstorm"
- Score > 80%: "Ready to go! Start with /cc-route"
