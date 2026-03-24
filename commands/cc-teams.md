---
description: >
  Agent team composition and dispatch patterns. Defines which agents work
  together, in what order, and how they hand off context.
  TRIGGER: 'assemble team', 'dispatch team', 'run team', 'multi-agent', 'which agents'.
  NOT FOR: single-agent tasks — just use the agent directly.
  FLOWS INTO: cc-parallel-agents, cc-work.
---

Activate the cc-teams skill.

## Team Templates

| Task | Team | Agents (in order) |
|------|------|-------------------|
| New feature | Feature Dev | researcher -> architect -> planner -> workers -> reviewers |
| Bug fix | Bug Fix | researcher -> build-fixer -> code-reviewer |
| Large PR | Review | researcher -> parallel(reviewers) -> consolidate |
| Refactoring | Refactor | researcher -> architect -> refactor-cleaner -> code-reviewer |
| Improvement | Autoimmune | researcher -> fixer -> verify |
| Health check | Audit | researcher -> architect -> security-reviewer |

## Dispatch Rules

- **Sequential**: next agent needs previous agent's output (one Agent call per message)
- **Parallel**: agents work on independent data (multiple Agent calls in ONE message)
- **Handoff**: filesystem `/tmp/cc-team-*.md` for large context between agents
- **Isolation**: each agent gets fresh context with only what it needs
