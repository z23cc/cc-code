# cc-code

Personal Claude Code plugin for Python-focused development.

## Architecture

- `agents/` — 6 specialized agents (python-reviewer, code-reviewer, security-reviewer, refactor-cleaner, planner, build-fixer)
- `skills/` — 8 workflow skills (brainstorming, plan, tdd, verification, debugging, parallel-agents, python-patterns, python-testing, security-review)
- `commands/` — 5 slash commands (/review, /plan, /simplify, /tdd, /fix)

## Development

To test changes locally, the plugin is installed from the local directory.

## Adding New Skills

1. Create `skills/<name>/SKILL.md` with YAML frontmatter (name, description)
2. Write the skill content
3. Bump version in `.claude-plugin/plugin.json`

## Adding New Agents

1. Create `agents/<name>.md` with YAML frontmatter (name, description, tools, model)
2. Add the path to `plugin.json` agents array
3. Bump version
