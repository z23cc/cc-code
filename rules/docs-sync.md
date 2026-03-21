---
description: "Documentation sync — keep docs accurate after code changes"
alwaysApply: true
---

# Documentation Sync Rules

- After adding/removing a command, skill, or agent: update README.md component counts
- After adding cc-flow subcommands: update the docstring at the top of cc-flow.py
- After changing a skill's behavior: update its SKILL.md description
- After changing CLI arguments: update help text and CLAUDE.md
- Do NOT create new documentation files unless explicitly asked
- Do NOT add comments or docstrings to code you didn't change
- Changelog entries go in commit messages, not separate files
