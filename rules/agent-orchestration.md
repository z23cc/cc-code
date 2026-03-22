---
description: "Agent dispatch and coordination rules — when to use which agent, handoff protocol"
alwaysApply: true
---

# Agent Orchestration Rules

## When to Dispatch Team vs Solo Agent

- **Solo agent**: simple, single-concern task (< 30 lines, one file, no security surface)
- **Team (2-3 agents)**: complex task touching multiple concerns (auth + logic + tests)
- **Full team**: new feature or major refactor → use team template from `/cc-team`

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

## Scout Agents (Read-Only)

Scouts investigate but never modify code. 12 specialists:
- **External research**: scout-practices (has WebSearch), scout-docs (has WebSearch)
- **Local analysis**: scout-repo, scout-testing, scout-tooling, scout-build, scout-env, scout-observability, scout-context
- **Gap detection**: scout-gaps, scout-docs-gap, scout-security

## Handoff Protocol

1. Agent writes findings to `/tmp/cc-team-<role>.md`
2. Next agent reads previous agent's findings before starting
3. Never pass context verbally — always via filesystem
4. Each agent must re-anchor (re-read spec + current state) before work

## Rules

- NEVER dispatch more than 3 agents for a single task
- ALWAYS dispatch security-reviewer when touching: auth, user input, API endpoints, database queries
- ALWAYS use `model: inherit` — never hardcode a specific model in agent definitions
- Worker agents get fresh context (see cc-worker-protocol skill)
- Prefer parallel dispatch when agents are independent (e.g., python-reviewer + security-reviewer)
