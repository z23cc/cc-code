## cc-code v5.24 — One Command Does Everything

**`cc-flow go "describe your goal"`** — auto-routes to chain/ralph/auto mode.

### Quick Reference

| Goal | Command |
|------|---------|
| **Anything** | `cc-flow go "your goal"` |
| New feature | `/cc-brainstorm` → `/cc-plan` → `/cc-work` |
| Fix a bug | `/cc-debug` → `/cc-tdd` → `/cc-commit` |
| Quick fix | `/cc-fix` or `cc-flow go "fix typo"` |
| Code review | `/cc-review` |
| Deploy | `/cc-ship` or `cc-flow go "deploy"` |
| Understand code | `/cc-research` |
| Project health | `/cc-audit` or `/cc-prime` (12 scouts) |
| Not sure | `/cc-route "describe task"` |

### 39 Workflow Chains

`cc-flow chain suggest "your task"` — finds the best chain.
`cc-flow chain list` — shows all 39 chains.

Top chains: feature, bugfix, hotfix, deploy, security-audit, performance, testing, refactor, idea-to-ship, ci-cd, architecture, prd-to-ship.

### Tools

- `cc-flow verify` — lint + test
- `cc-flow dashboard` — project overview
- `cc-flow doctor` — health check
- `cc-flow help` — full command list
