---
description: "Documentation sync — keep docs accurate after code changes"
alwaysApply: true
---

# Documentation Sync Rules

## What must stay in sync

| When you change... | Update these files |
|--------------------|--------------------|
| Add/remove CLI command | `entry.py` registry, `cli.py` parser, `__init__.py` module list, `repl.py` completions |
| Add/remove skill | `skills/*/SKILL.md`, README.md skill count, CLAUDE.md if in decision tree |
| Add/remove agent | `agents/*.md`, README.md agent count |
| Change CLI arguments | `cli.py` parser, skill SKILL.md if it references the command |
| Change tool priority | `rules/tool-priority.md` (single source of truth) |
| Bump version | `pyproject.toml` + `__init__.py` (both must match) |

## Format rules
- README.md architecture: `cc-flow CLI (N modules, M commands)` — keep counts accurate
- CLAUDE.md: concise reference only — detailed rules go in `rules/*.md`
- Skill descriptions: must include TRIGGER keywords (English + Chinese)

## Do NOT
- Create new documentation files unless explicitly asked
- Add comments or docstrings to code you didn't change
- Duplicate tool-priority content between CLAUDE.md and rules/tool-priority.md
