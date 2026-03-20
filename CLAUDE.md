# cc-code

Personal Claude Code plugin for Python-focused development.

## Architecture

- `agents/` — 6 specialized agents (python-reviewer, code-reviewer, security-reviewer, refactor-cleaner, planner, build-fixer)
- `skills/` — 13 workflow skills:
  - **Flow**: brainstorming, plan, tdd, verification, debugging, parallel-agents
  - **Python**: python-patterns, python-testing, performance, security-review
  - **Infra**: git-workflow, scaffold, deploy
- `commands/` — 8 slash commands: `/review`, `/plan`, `/simplify`, `/tdd`, `/fix`, `/commit`, `/scaffold`, `/perf`

## Development

To test changes locally, the plugin is installed from the local directory.

## Adding New Skills

1. Create `skills/<name>/SKILL.md` with YAML frontmatter (name, description)
2. Write the skill content
3. Bump version in `.claude-plugin/plugin.json` and `marketplace.json`

## Adding New Agents

1. Create `agents/<name>.md` with YAML frontmatter (name, description, tools, model)
2. Add the path to `plugin.json` agents array
3. Bump version
