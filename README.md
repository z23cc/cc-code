# cc-code

Development workflow toolkit for Claude Code — task management, smart routing, OODA autoimmune loop, and embedding-powered search.

## Install

```bash
# As Claude Code plugin
claude plugin add z23cc/cc-code

# Or standalone CLI
pip install -e .
cc-flow dashboard
```

## Quick Start

```bash
cc-flow                                # Interactive REPL (tab completion!)
cc-flow init                           # Initialize project
cc-flow epic create --title "Feature"  # Create an epic
cc-flow task create --epic epic-1-feature --title "Step 1"
cc-flow start epic-1-feature.1         # Start task
cc-flow verify                         # Lint + test (auto-detect language)
cc-flow done epic-1-feature.1          # Complete task
cc-flow dashboard                      # Visual overview
```

## Key Features

| Feature | Command | Description |
|---------|---------|-------------|
| **REPL** | `cc-flow` | Interactive shell with tab completion |
| **Dashboard** | `cc-flow dashboard` | Colored one-screen project overview |
| **Smart Router** | `cc-flow route "fix bug"` | Q-learning command suggestions |
| **Verify** | `cc-flow verify --fix` | Auto-detect language, lint + test |
| **Deep Scan** | `cc-flow auto deep` | OODA: architecture + tests + docs + deps |
| **Semantic Search** | `cc-flow find --semantic "auth"` | Morph embedding-powered task search |
| **Health Score** | `cc-flow health` | 0-100 composite grade (A-F) |
| **Forecast** | `cc-flow forecast` | ETA from velocity |
| **GitHub Sync** | `cc-flow gh import/export` | Sync with GitHub Issues |
| **Workflows** | `cc-flow workflow run release` | Multi-step pipelines |
| **Plugins** | `cc-flow plugin create my-tool` | Extensible plugin system |
| **Eval** | `cc-flow eval run` | Automated capability testing |

## Architecture

```
cc-flow CLI (34 modules, 88+ subcommands)
├── Core: init, epic/task CRUD, deps, templates
├── Views: list, dashboard, progress, graph, export
├── Work: start, done, block, reopen, diff, bulk
├── Search: find, similar, dedupe, suggest, index (Morph embed)
├── Quality: verify, scan, doctor, health, auto deep (OODA)
├── Analytics: stats, standup, changelog, burndown, report, forecast
├── Routing: route (Q-learning), learn, consolidate
├── Integration: gh sync, context, session, workflow, plugins
└── Eval: self-test (98/100), cross-project (100/100)
```

## Eval Scores

```bash
cc-flow eval run              # Self: 98/100 (A)
cc-flow eval cross --limit 10 # Cross: 100/100 (7 projects)
cc-flow health                # Health: 93/100 (A)
```

## Plugin System

```bash
cc-flow plugin create my-notifier    # Scaffold
# Edit .tasks/plugins/my-notifier.py
cc-flow plugin list                  # See installed
cc-flow my-notifier --example hi     # Run plugin command
```

See `examples/plugins/` for notify and timer plugins.

## Claude Code Integration

```
/cc-route "describe task" → suggests command + team
/cc-brainstorm → /cc-plan → /cc-tdd → /cc-review → /cc-commit
/cc-autoimmune → autonomous improvement loop
```

## Requirements

- Python 3.9+
- Optional: `prompt_toolkit` (REPL tab completion)
- Optional: `MORPH_API_KEY` (semantic search, embeddings)

## License

MIT
