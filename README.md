# cc-code

Development workflow toolkit for Claude Code — task management, smart routing, OODA autoimmune loop, embedding-powered search, and skills marketplace integration.

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
cc-flow                                # Interactive REPL (tab completion + typo correction!)
cc-flow init                           # Initialize project
cc-flow epic create --title "Feature"  # Create an epic
cc-flow task create --epic epic-1 --title "Step 1"  # Shorthand epic ID works
cc-flow start epic-1.1                 # Shorthand task ID works too
cc-flow verify                         # Lint + test (auto-detect language)
cc-flow done epic-1.1                  # Complete task
cc-flow dashboard                      # Visual overview
```

## Key Features

| Feature | Command | Description |
|---------|---------|-------------|
| **REPL** | `cc-flow` | Interactive shell with tab completion + "did you mean?" |
| **Dashboard** | `cc-flow dashboard` | Colored one-screen project overview |
| **Smart Router** | `cc-flow route "fix bug"` | Q-learning command suggestions (中文 supported) |
| **Verify** | `cc-flow verify --fix` | Auto-detect language + npm scripts |
| **Deep Scan** | `cc-flow auto deep` | OODA: architecture + tests + docs + deps |
| **Semantic Search** | `cc-flow find --semantic "auth"` | Morph embedding-powered task search |
| **Health Score** | `cc-flow health` | 0-100 composite grade (A-F) |
| **Forecast** | `cc-flow forecast` | ETA from velocity |
| **GitHub Sync** | `cc-flow gh import/export` | Sync with GitHub Issues |
| **Workflows** | `cc-flow workflow run release` | Multi-step pipelines |
| **Plugins** | `cc-flow plugin create my-tool` | Extensible plugin system |
| **Skills Store** | `cc-flow skills find "react"` | Browse skills.sh marketplace |
| **Eval** | `cc-flow eval run` | Automated capability testing |
| **Context** | `cc-flow context brief` | One-paragraph session primer |

## Architecture

```
cc-flow CLI (35 modules, 90+ subcommands)
├── Core: init, epic/task CRUD, deps, templates (atomic writes, cross-platform locks)
├── Views: list, dashboard, progress, graph, export
├── Work: start, done, block, reopen, diff, bulk (race-safe task IDs)
├── Search: find, similar, dedupe, suggest, index (Morph embed)
├── Quality: verify, scan, doctor, health, auto deep (OODA loop)
├── Analytics: stats, standup, changelog, burndown, report, forecast, evolve
├── Routing: route (Q-learning + embedding + rerank), learn, consolidate
├── Integration: gh sync, context, session, workflow, plugins, skills.sh
├── Eval: self-test (100/100), cross-project (100/100), health (100/100)
└── UX: REPL with tab completion, colored skin, "did you mean?" typo correction
```

## Eval Scores

```bash
cc-flow eval run              # Self: 100/100 (A)
cc-flow eval cross --limit 10 # Cross: 100/100 (7 projects)
cc-flow health                # Health: 100/100 (A)
```

## Plugin System

```bash
cc-flow plugin create my-notifier    # Scaffold
# Edit .tasks/plugins/my-notifier.py
cc-flow plugin list                  # See installed
cc-flow my-notifier --example hi     # Run plugin command
```

See `examples/plugins/` for notify and timer plugins.

## Skills Marketplace

```bash
cc-flow skills find "code review"    # Search skills.sh
cc-flow skills add owner/repo@skill  # Install a community skill
cc-flow skills list                  # Show installed
```

### Integrated Community Skills

| Skill | Description | Source |
|-------|-------------|--------|
| `cc-web-design` | Web Interface Guidelines review | [vercel-labs/agent-skills](https://skills.sh/vercel-labs/agent-skills/web-design-guidelines) |
| `cc-ui-ux` | 50+ styles, 161 palettes, 57 font pairings, 99 UX guidelines | [nextlevelbuilder/ui-ux-pro-max-skill](https://skills.sh/nextlevelbuilder/ui-ux-pro-max-skill/ui-ux-pro-max) |
| `cc-browser` | Browser automation — navigate, forms, screenshots, E2E testing | [vercel-labs/agent-browser](https://skills.sh/vercel-labs/agent-browser/agent-browser) |

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
- Optional: `npx skills` (skills.sh marketplace)

## License

MIT
