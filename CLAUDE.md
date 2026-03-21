# cc-code

Development workflow toolkit with task management CLI. Language-agnostic core with Python language pack.

## Architecture

- `scripts/cc-flow.py` — Task & workflow CLI (36 subcommands: epic/task, graph, dashboard, doctor, session, route, learn, consolidate)
- `agents/` — 8 agents: researcher, architect, planner, code-reviewer, python-reviewer, security-reviewer, refactor-cleaner, build-fixer (all `model: inherit`)
- `skills/` — 47 skills (all prefixed `cc-` to avoid conflicts):
  - **Core (23):** cc-brainstorming, cc-plan, cc-tdd, cc-verification, cc-refinement, cc-code-review-loop, cc-worker-protocol, cc-task-tracking, cc-debugging, cc-research, cc-parallel-agents, cc-teams, cc-autoimmune, cc-readiness-audit, cc-search-strategy, cc-git-workflow, cc-prompt-engineering, cc-clean-architecture, cc-context-tips, cc-docs, cc-incident, cc-dependency-upgrade, cc-feedback-loop
  - **Python pack (12):** cc-python-patterns, cc-python-testing, cc-async-patterns, cc-database, cc-fastapi, cc-error-handling, cc-performance, cc-logging, cc-security-review, cc-scaffold, cc-deploy, cc-task-queues
  - **Scouts (12):** cc-scout-practices, cc-scout-repo, cc-scout-docs, cc-scout-docs-gap, cc-scout-security, cc-scout-testing, cc-scout-tooling, cc-scout-build, cc-scout-env, cc-scout-observability, cc-scout-gaps, cc-scout-context
- `commands/` — 24 slash commands (all prefixed `/cc-`)
- `tests/` — 88 pytest tests covering cc-flow lifecycle
- `rules/` — 5 always-on rules: python-style, testing, security, git, docs-sync
- `hooks/` — 3 hooks: SessionStart + PreToolUse + PostToolUse

## Key Workflow (auto-integrated)

```
/cc-route → suggests command + team + confidence %
    ↓
/cc-brainstorm (auto-scouts: repo, practices, gaps)
    ↓
/cc-plan (auto-imports to cc-flow tasks with tags + templates)
    ↓
/cc-tdd (auto-reads task spec, auto-marks done)
    ↓
/cc-review (auto-records learnings)
    ↓
/cc-commit → cc-flow learn → cc-flow consolidate → smarter routing
```

Alternative entry points:
- Big project: `/cc-blueprint` (one-liner → phased plan)
- Vague requirements: `/cc-interview` (5-phase extraction)
- Project assessment: `/cc-prime` (runs all 12 scouts)
- Bug: `/cc-debug` (auto-learns after fix)
- Autonomous: `/cc-autoimmune` (auto-session-save + auto-learn)

## Language Detection

Core skills work with ANY language. Auto-detect verification commands:

| File Present | Language | Verify | Lint |
|-------------|----------|--------|------|
| `pyproject.toml` | Python | `ruff check . && mypy . && pytest` | ruff |
| `package.json` | JS/TS | `npm run lint && npm test` | eslint |
| `go.mod` | Go | `go vet ./... && go test ./...` | golangci-lint |
| `Cargo.toml` | Rust | `cargo check && cargo test` | clippy |
| `Makefile` | Any | `make verify` or `make test` | — |

## cc-flow CLI Quick Reference

```bash
CCFLOW="python3 ${CLAUDE_PLUGIN_ROOT}/scripts/cc-flow.py"

# Task management
$CCFLOW init && $CCFLOW epic create --title "Feature"
$CCFLOW task create --epic <id> --title "Step 1" --template feature --tags "api,auth"
$CCFLOW start <task-id> && $CCFLOW done <task-id> --summary "..."

# Views
$CCFLOW dashboard          # one-screen overview
$CCFLOW graph --format ascii  # dependency tree
$CCFLOW progress           # progress bars
$CCFLOW doctor             # health check

# Learning
$CCFLOW route "fix auth bug"  # smart routing with confidence %
$CCFLOW learn --task "..." --outcome success --approach "..." --lesson "..."
$CCFLOW consolidate        # promote patterns

# Session
$CCFLOW session save --notes "context for tomorrow"
$CCFLOW session restore    # resume with full context
```

## Development

- Source: `/Users/z23cc/Desktop/cc-code` (symlinked to plugin cache)
- Edit source → restart Claude Code → changes take effect
- Tests: `python3 -m pytest tests/test_cc_flow.py -v`
- Lint: `ruff check scripts/cc-flow.py`
- Push: `git push origin main`

### Adding Skills
1. Create: `skills/cc-<name>/SKILL.md` (always `cc-` prefix)
2. Add Related Skills section (reference `cc-` prefixed names)
3. Bump version in `plugin.json`
