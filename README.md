# cc-code

Development workflow toolkit for Claude Code. Language-agnostic core with Python language pack.

## Install

```bash
# Add marketplace
claude plugin marketplace add z23cc/cc-code

# Install
claude plugin install cc-code@cc-code --scope user
```

## What's Inside

| Component | Count | Highlights |
|-----------|-------|-----------|
| **Skills** | 47 | 23 core + 12 Python pack + 12 scouts |
| **Commands** | 24 | `/cc-brainstorm` `/cc-plan` `/cc-tdd` `/cc-prime` `/cc-scout` `/cc-blueprint` |
| **Agents** | 11 | researcher, architect, planner, code-reviewer, python-reviewer, security-reviewer, refactor-cleaner, build-fixer, db-reviewer, doc-updater, e2e-runner |
| **CLI** | cc-flow | 39 subcommands: epic/task, graph, dashboard, doctor, session, apply, search, embed |
| **Rules** | 9 | python-style, testing, security, git, docs-sync, workflow, performance, agent-orchestration, tool-priority |
| **Hooks** | 5 | SessionStart, PreToolUse, PostToolUse, PreCompact, Stop |
| **Tests** | 114 | 99 cc-flow + 15 morph client |
| **Morph** | 5 APIs | apply, search (WarpGrep), embed, rerank, compact — pure Python client |

## Quick Start

```bash
# Don't know what command to use?
/cc-route describe your task here

# New feature (auto-integrated — each step chains to next)
/cc-brainstorm    # auto-runs scouts → interview → design spec
/cc-plan          # creates plan → auto-imports to cc-flow tasks
/cc-tdd           # TDD per task → auto-marks done → suggests next
/cc-refine        # coverage, complexity, security checks
/cc-review        # code review → auto-records learnings
/cc-commit        # conventional commit with pre-verification

# Big project from scratch
/cc-blueprint add user authentication    # one-liner → phased plan

# Fix a bug (auto-learns after fix)
/cc-debug → /cc-fix → /cc-commit

# Autonomous improvement
/cc-autoimmune scan    # detect issues → create tasks
/cc-autoimmune         # fix from task list (auto-learn + session save)
/cc-autoimmune full    # scan + fix + test

# Project assessment (runs all 12 scouts)
/cc-prime

# Deep requirements interview
/cc-interview
```

## Architecture

```
User input
    ↓
/cc-route → suggests command + team + confidence %
    ↓
/cc-brainstorm (auto-scouts) → /cc-plan (auto-import) → /cc-tdd (auto-done)
    ↓                                                          ↓
/cc-review (auto-learn) → /cc-commit ──────── cc-flow learn ───┘
    ↓
cc-flow consolidate → promoted patterns → smarter routing next time
```

### Skill Categories

| Category | Skills | Purpose |
|----------|--------|---------|
| **Core (23)** | cc-brainstorming, cc-plan, cc-tdd, cc-verification, cc-refinement, cc-code-review-loop, cc-worker-protocol, cc-debugging, cc-research, cc-teams, cc-autoimmune, cc-feedback-loop, ... | Language-agnostic workflows |
| **Python Pack (12)** | cc-python-patterns, cc-python-testing, cc-fastapi, cc-async-patterns, cc-database, cc-deploy, cc-security-review, ... | Python-specific patterns |
| **Scouts (12)** | cc-scout-practices, cc-scout-repo, cc-scout-docs, cc-scout-gaps, cc-scout-security, cc-scout-testing, cc-scout-tooling, cc-scout-build, cc-scout-env, cc-scout-observability, cc-scout-docs-gap, cc-scout-context | Research-only project analysis |

### 24 Commands

| Workflow | Commands |
|----------|----------|
| Feature dev | `/cc-brainstorm` → `/cc-plan` → `/cc-tdd` → `/cc-refine` → `/cc-review` → `/cc-commit` |
| Bug fix | `/cc-debug` → `/cc-fix` → `/cc-commit` |
| Big project | `/cc-blueprint` → `/cc-interview` → `/cc-plan` |
| Project health | `/cc-prime` → `/cc-audit` → `/cc-scout [type]` |
| Code quality | `/cc-review` → `/cc-simplify` → `/cc-perf` |
| Autonomous | `/cc-autoimmune` (scan/code/test/full) |
| Routing | `/cc-route` → smart recommendation |
| Team | `/cc-team` (feature-dev / bug-fix / review / refactor / audit) |
| Other | `/cc-research` `/cc-scaffold` `/cc-docs` `/cc-pr-review` `/cc-help` `/cc-tasks` |

### cc-flow CLI (39 subcommands)

```
Project:     init, epic (create/close/import/reset), task (create/reset/set-spec), dep add
View:        list, epics, tasks, show, ready, next, progress, status, graph, history, dashboard
Work:        start, done, block, rollback
Quality:     validate, scan, doctor
Auto:        auto (scan/run/test/full/status)
Routing:     route, learn, learnings, consolidate
Session:     session (save/restore/list)
Morph:       apply, search, embed, compact, github-search
Stats:       log, summary, archive, stats
Config:      config, version
```

### 11 Agents

| Agent | Role |
|-------|------|
| researcher | Investigate code, understand context |
| architect | System design, architecture decisions |
| planner | Break down tasks, create plans |
| code-reviewer | General code review |
| python-reviewer | Python-specific review (PEP 8, type hints) |
| security-reviewer | Security audit |
| refactor-cleaner | Refactoring, dead code removal |
| build-fixer | Fix lint/type/build errors |
| db-reviewer | Database queries, schema, migrations |
| doc-updater | Documentation sync after changes |
| e2e-runner | Playwright E2E testing |

## Key Features

### Smart Routing with Learning
```bash
cc-flow route "fix auth returning 403"
# → {"command": "/cc-debug", "confidence": 87, "past_learning": {...}}

# After fixing:
cc-flow learn --task "auth 403" --outcome success --approach "check middleware" \
  --lesson "auth issues trace to middleware" --score 5 --used-command /cc-debug

# Next time, routing is smarter
```

### Dependency Graph
```bash
cc-flow graph --format ascii
# 📋 User Auth
# └── ● Task 1: DB Model [S]
#     └── ○ Task 2: JWT Service [M]
#         ├── ○ Task 3: OAuth [L]
#         └── ○ Task 4: Tests [M]

cc-flow graph --format mermaid    # For GitHub/docs
cc-flow graph --format dot        # For Graphviz
```

### Dashboard
```bash
cc-flow dashboard
# ╔══════════════════════════════════════════╗
# ║  Progress: ██████░░░░░░░░░░░░░░  33%   ║
# ║  ● 3 done  ◐ 1 active  ○ 5 todo       ║
# ║  Velocity: 2.1 tasks/hour               ║
# ╠══════════════════════════════════════════╣
# ║  Epics: ███░░░░░░░  33% User Auth       ║
# ║  Learning: 12 entries, 3 patterns        ║
# ║  Routing: 15 routes, 87% success rate    ║
# ╚══════════════════════════════════════════╝
```

### Health Check
```bash
cc-flow doctor
# ✓ Python: 3.12.0
# ✓ Git: branch main
# ✓ ruff: available
# ⚠ mypy: not installed → pip install mypy
# ✓ Task integrity: 8 tasks, all clean
# 8/10 checks passed
```

### Task Templates
```bash
cc-flow task create --epic my-epic --title "Add login" \
  --template feature --tags "auth,api" --size M
# Generates structured spec with steps: Research → Design → Implement → Test → Review
```

### Session Persistence
```bash
cc-flow session save --notes "working on JWT auth, stuck on refresh token"
# Next day:
cc-flow session restore
# → Shows: branch, SHA, in-progress tasks, recent learnings, notes
```

## Language Detection

Core skills work with ANY language. Verification commands auto-detect:

| File | Language | Verify | Lint |
|------|----------|--------|------|
| `pyproject.toml` | Python | `ruff check . && mypy . && pytest` | ruff |
| `package.json` | JS/TS | `npm run lint && npm test` | eslint |
| `go.mod` | Go | `go vet ./... && go test ./...` | golangci-lint |
| `Cargo.toml` | Rust | `cargo check && cargo test` | clippy |

## Development

```bash
# Live development (symlink to source)
mv ~/.claude/plugins/cache/cc-code/cc-code/X.Y.Z ~/.claude/plugins/cache/cc-code/cc-code/X.Y.Z.bak
ln -s /path/to/cc-code ~/.claude/plugins/cache/cc-code/cc-code/X.Y.Z

# Run tests
python3 -m pytest tests/test_cc_flow.py -v

# Lint
ruff check scripts/cc-flow.py

# Push updates
git push origin main
# Other devices: claude plugin update cc-code@cc-code
```

## License

MIT
