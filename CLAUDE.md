# cc-code

Development workflow toolkit with task management CLI. Language-agnostic core with Python language pack.

## Architecture

- `scripts/cc-flow.py` — Task & workflow CLI (35 subcommands: epic/task lifecycle, scan, graph, dashboard, doctor, route, learn, consolidate)
- `agents/` — 8 agents: researcher, architect, planner, code-reviewer, python-reviewer, security-reviewer, refactor-cleaner, build-fixer
- `skills/` — 35 skills (all prefixed `cc-` to avoid conflicts with other plugins):
  - **Core (23, language-agnostic):** cc-brainstorming, cc-plan, cc-tdd, cc-verification, cc-refinement, cc-code-review-loop, cc-worker-protocol, cc-task-tracking, cc-debugging, cc-research, cc-parallel-agents, cc-teams, cc-autoimmune, cc-readiness-audit, cc-search-strategy, cc-git-workflow, cc-prompt-engineering, cc-clean-architecture, cc-context-tips, cc-docs, cc-incident, cc-dependency-upgrade, cc-feedback-loop
  - **Python pack (12):** cc-python-patterns, cc-python-testing, cc-async-patterns, cc-database, cc-fastapi, cc-error-handling, cc-performance, cc-logging, cc-security-review, cc-scaffold, cc-deploy, cc-task-queues
- `commands/` — 20 slash commands (all prefixed `/cc-`)
- `tests/` — 85 pytest tests covering cc-flow lifecycle
- `rules/` — 5 always-on rules
- `hooks/` — 3 hooks: SessionStart + PreToolUse + PostToolUse

## Key Workflow

```
/cc-route → suggests → /cc-brainstorm → /cc-plan → /cc-tdd → /cc-refine → /cc-review → /cc-commit → cc-flow learn
                                          ↑
                          /cc-debug ──────┘ (when stuck)

/cc-autoimmune — autonomous improvement loop (scan/code/test/full)
/cc-team — assemble agent team (feature-dev/bug-fix/review/refactor/audit)
/cc-tasks — file-based task management via cc-flow CLI
/cc-audit — 8-pillar readiness assessment
```

## Language Detection

Core skills work with ANY language.
When commands need to run verification/lint/test, detect the project language:

| File Present | Language | Verify Command | Lint |
|-------------|----------|---------------|------|
| `pyproject.toml` / `setup.py` | Python | `ruff check . && mypy . && pytest` | ruff |
| `package.json` | JS/TS | `npm run lint && npm test` | eslint |
| `go.mod` | Go | `go vet ./... && go test ./...` | golangci-lint |
| `Cargo.toml` | Rust | `cargo check && cargo test` | clippy |
| `Makefile` | Any | `make verify` or `make test` | — |

## Development

- Source: `/Users/z23cc/Desktop/cc-code` (symlinked to plugin cache)
- Edit source → restart Claude Code → changes take effect
- `git push origin main` → other devices: `claude plugin update cc-code@cc-code`

### Adding Skills
1. All skills: `skills/cc-<name>/SKILL.md` — always use `cc-` prefix
2. Core skills: language-agnostic
3. Language-pack skills: `skills/cc-<lang>-<name>/SKILL.md`
4. Always add Related Skills section (reference `cc-` prefixed names)
5. Bump version in plugin.json
