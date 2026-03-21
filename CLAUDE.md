# cc-code

Development workflow toolkit with task management CLI. Language-agnostic core with Python language pack.

## Architecture

- `scripts/cc-flow.py` — Task & workflow CLI (21 commands: epic/task lifecycle, scan, progress, validate)
- `agents/` — 8 agents: researcher, architect, planner, code-reviewer, python-reviewer, security-reviewer, refactor-cleaner, build-fixer
- `skills/` — 30 skills in 3 layers:
  - **Core (18, language-agnostic):** brainstorming, plan, tdd, verification, refinement, code-review-loop, worker-protocol, task-tracking, debugging, research, parallel-agents, teams, autoimmune, readiness-audit, search-strategy, git-workflow, prompt-engineering, clean-architecture
  - **Python pack (12):** python-patterns, python-testing, async-patterns, database, fastapi, error-handling, performance, logging, security-review, scaffold, deploy, task-queues
- `commands/` — 17 slash commands
- `rules/` — 4 always-on rules
- `hooks/` — SessionStart context injection

## Key Workflow

```
/brainstorm → /plan → /tdd → /refine → /review → /commit
                                    ↑
                    /debug ─────────┘ (when stuck)

/autoimmune — autonomous improvement loop (scan/code/test/full)
/team — assemble agent team (feature-dev/bug-fix/review/refactor/audit)
/tasks — file-based task management via cc-flow CLI
/audit — 8-pillar readiness assessment
```

## Language Detection

Core skills (brainstorming, plan, tdd, debugging, autoimmune, etc.) work with ANY language.
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
1. Core skills: `skills/<name>/SKILL.md` — language-agnostic
2. Language-pack skills: `skills/<lang>-<name>/SKILL.md` — prefix with language
3. Always add Related Skills section
4. Bump version in plugin.json + marketplace.json
