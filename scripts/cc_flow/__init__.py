"""cc-flow — task & workflow manager for cc-code plugin.

Usage:
    cc-flow <command>          (after pip install -e .)
    python -m cc_flow <command>

Package structure (53 modules, 145 commands):
  cc_flow/
    __init__.py      → VERSION
    __main__.py      → python -m cc_flow support
    entry.py         → lazy-loaded command dispatch (only imports needed module)
    cli.py           → argparse with 11+ command categories
    core.py          → shared constants, atomic writes, cross-platform locks, ID resolution
    epic_task.py     → epic/task CRUD, dep management (race-safe O_EXCL)
    views.py         → list, show, ready, next, status + shared helpers
    views_dashboard.py → dashboard, progress (colored skin output)
    views_search.py  → find, similar, export, priority, index, dedupe, suggest
    work.py          → start, done, block, rollback, reopen, diff, bulk + plugin hooks
    route_learn.py   → routing logic, ROUTE_TABLE, cmd_route
    learning.py      → learn, learnings, consolidate, pattern search
    auto.py          → OODA-loop autoimmune (observe/orient/decide/act/learn)
    quality.py       → validate, scan, verify (auto-detect language + npm scripts)
    log_cmds.py      → log, summary, archive
    analytics.py     → stats, standup, changelog, burndown, report, time
    config.py        → version, history, config, clean, profiles
    morph_cmds.py    → apply, search, embed, compact, github-search
    embeddings.py    → embedding cache, cosine similarity, semantic search, dedup
    templates.py     → TASK_TEMPLATES, _generate_spec, template CRUD
    workflow.py      → multi-step workflow pipelines (built-in + custom)
    plugins.py       → plugin system (discover, load, lifecycle hooks)
    skill_store.py   → skills.sh marketplace (find, add, list)
    scanner.py       → smart scanners (architecture, tests, docs, duplication, deps)
    qrouter.py       → Q-learning adaptive command routing (lr=0.25)
    perf.py          → command performance tracking (PerfTimer + analytics)
    insights.py      → forecast, evolve, health score (0-100)
    eval_harness.py  → automated capability evaluation (4 dimensions)
    cross_project_eval.py → cross-project testing
    session.py       → session save/restore/list
    graph.py         → mermaid, ascii, dot dependency graphs + critical path
    doctor.py        → 10+ health checks (colored skin output)
    context.py       → project context management (save/show/brief)
    aliases.py       → command aliases (shortcuts)
    gh_sync.py       → GitHub Issues import/export
    repl.py          → interactive REPL (tab completion + "did you mean?")
    skin.py          → terminal output (colors, tables, progress bars)
    bridge.py        → Morph × RP × Supermemory collaboration (4 feedback loops)
    rp.py            → RepoPrompt dual-transport SDK (CLI + MCP auto-routing)
    rp_commands.py   → cc-flow rp <subcommand> (24 subcommands)
    review_setup.py  → multi-backend review detection and configuration
    worktree_state.py → cross-worktree state management
    skill_flow.py    → skill flow graph, context protocol, next-skill queries
    go.py            → unified entry point (route → decide mode → execute)
    wf_executor.py   → cc-wf-studio workflow executor (run/list/export/show)
  morph_client.py    → pure Python Morph API client (5 APIs)
  cc-flow.py         → backward-compatible shim
"""

VERSION = "5.21.0"
