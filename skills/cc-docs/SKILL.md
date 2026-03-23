---
name: cc-docs
description: "Documentation generation and maintenance — README, CHANGELOG, API docs, CLAUDE.md. Keeps docs in sync with code. TRIGGER: 'update docs', 'write README', 'changelog', 'document this', 'sync docs', 'API docs', '更新文档', '写文档', '同步文档'. NOT FOR: code comments (inline), architecture design (use cc-clean-architecture)."
---

# Documentation Skill

## When to Use

- After shipping a feature or PR
- README is stale or missing
- CHANGELOG needs updating
- API docs are out of date
- CLAUDE.md doesn't match project state

## Documentation Types

### README.md

```markdown
# Project Name

One-sentence description.

## Quick Start
[3-5 commands to get running]

## Usage
[Core API / CLI examples]

## Development
[How to contribute: setup, test, lint]

## License
[License type]
```

**Rules:**
- Quick Start must work on a fresh clone
- Usage examples must be copy-pasteable
- Keep under 200 lines (link to detailed docs)

### CHANGELOG.md

```markdown
# Changelog

## [Unreleased]

### Added
- New feature X (#123)

### Changed
- Updated behavior of Y

### Fixed
- Bug in Z (#456)

### Removed
- Deprecated API endpoint
```

**Rules:**
- Follow [Keep a Changelog](https://keepachangelog.com) format
- Group by Added/Changed/Fixed/Removed
- Include PR/issue numbers
- Most recent version at top

### CLAUDE.md

```markdown
# Project Name

## Commands
- `make test` — run tests
- `make lint` — run linter

## Architecture
[Key directories and what they contain]

## Conventions
[Coding style, naming, patterns]
```

**Rules:**
- Only include what helps Claude Code work effectively
- Commands must be exact and runnable
- Keep under 100 lines

### API Documentation

For API projects, maintain:
- Route list with methods, params, response codes
- Request/response examples
- Authentication requirements
- Error format

## Workflow: Post-Ship Doc Update

1. `git log --oneline <last-release>..HEAD` — what changed
2. Update CHANGELOG.md with new entries
3. Update README.md if usage/setup changed
4. Update CLAUDE.md if commands/conventions changed
5. Verify all code examples still work
6. Commit: `docs: update documentation for vX.Y.Z`

## Related Skills

- **cc-git-workflow** — conventional commits feed CHANGELOG
- **cc-scaffold** — initial docs generated during project setup
- **cc-readiness-audit** — Pillar 4 checks documentation completeness
