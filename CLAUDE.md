# cc-code

Personal Claude Code plugin for Python-focused development.

## Architecture

- `agents/` — 6 specialized agents (python-reviewer, code-reviewer, security-reviewer, refactor-cleaner, planner, build-fixer) — all `model: inherit` (uses your global model setting)
- `skills/` — 19 workflow skills:
  - **Flow**: brainstorming, plan, tdd, verification, refinement, code-review-loop, worker-protocol, debugging, research, parallel-agents, autoimmune, readiness-audit
  - **Python**: python-patterns, python-testing, async-patterns, database, fastapi, error-handling, performance, logging, security-review
  - **Infra**: git-workflow, scaffold, deploy, search-strategy
- `commands/` — 11 slash commands (with trigger phrases): `/review`, `/pr-review`, `/plan`, `/simplify`, `/tdd`, `/fix`, `/commit`, `/scaffold`, `/perf`, `/autoimmune`, `/audit`
- `rules/` — 4 always-on rules: python-style, testing, security, git
- `hooks/` — SessionStart context injection

## Key Workflow

```
brainstorming → plan → tdd → refinement → code-review-loop → verification → commit
                                    ↑
                    debugging ──────┘ (when stuck)

/autoimmune — autonomous improvement loop:
  Mode A: improvement-program.md → implement → verify → commit/revert
  Mode B: pytest failures → fix → verify → commit/revert
  Mode C: A then B
```

## Development

### Adding New Skills
1. Create `skills/<name>/SKILL.md` with YAML frontmatter (name, description)
2. Write content with Related Skills section
3. Bump version in `.claude-plugin/plugin.json` and `marketplace.json`

### Adding New Agents
1. Create `agents/<name>.md` with YAML frontmatter (name, description, tools, model)
2. Add the path to `plugin.json` agents array
3. All agents use `model: inherit` — they follow your global model setting

### Adding New Rules
1. Create `rules/<name>.md` with YAML frontmatter (description, alwaysApply: true)
2. Keep rules concise — they're injected into every conversation
