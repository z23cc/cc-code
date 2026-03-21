---
description: "Agent dispatch and coordination rules — when to use which agent, handoff protocol"
alwaysApply: true
---

# Agent Orchestration Rules

## Agent Selection

| Task Type | Primary Agent | Support Agent | Skip If |
|-----------|--------------|---------------|---------|
| Unknown code | researcher | — | Already familiar |
| System design | architect | researcher | Small change < 20 lines |
| Implementation plan | planner | architect | Single task |
| Python code review | python-reviewer | security-reviewer | Non-Python files |
| General code review | code-reviewer | security-reviewer | — |
| Security concern | security-reviewer | researcher | No auth/input/API |
| Build/lint error | build-fixer | — | Already auto-fixed |
| Dead code/cleanup | refactor-cleaner | code-reviewer | < 5 lines change |
| Database change | db-reviewer | security-reviewer | No schema/query changes |
| Documentation sync | doc-updater | — | No user-facing changes |
| E2E testing | e2e-runner | — | No UI changes |

## Handoff Protocol

- Agent writes findings to `/tmp/cc-team-<role>.md`
- Next agent reads previous agent's findings before starting
- Never pass context verbally — always via filesystem

## Rules

- NEVER dispatch more than 3 agents for a single task
- ALWAYS dispatch security-reviewer when touching: auth, user input, API endpoints, database queries
- Use `model: inherit` — never hardcode a specific model
- Worker agents get fresh context (see cc-worker-protocol skill)
