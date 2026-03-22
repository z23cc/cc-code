"""cc-flow — task & workflow manager for cc-code plugin.

Usage:
    cc-flow <command>          (after pip install -e .)
    python -m cc_flow <command>

Package structure (23 modules, 76+ subcommands):
  cc_flow/
    __init__.py      → VERSION
    __main__.py      → python -m cc_flow support
    entry.py         → lazy-loaded command dispatch (only imports needed module)
    cli.py           → argparse with 10 command categories
    core.py          → shared constants, atomic writes, cross-platform file locking
    epic_task.py     → epic/task CRUD, templates, dep management
    views.py         → list, show, dashboard, progress, find, similar, export, dedupe, suggest
    work.py          → start, done, block, rollback, reopen, diff, bulk + plugin hooks
    route_learn.py   → route, learn, consolidate, rerank + embedding search
    auto.py          → OODA-loop autoimmune (observe/orient/decide/act/learn)
    quality.py       → validate, scan, verify (auto-detect language)
    log_cmds.py      → log, summary, stats, standup, changelog, burndown, report, time
    config.py        → version, history, config, clean, profiles
    morph_cmds.py    → apply, search, embed, compact, github-search
    embeddings.py    → embedding cache, cosine similarity, semantic search, dedup
    workflow.py      → multi-step workflow pipelines (built-in + custom)
    plugins.py       → plugin system (discover, load, lifecycle hooks)
    scanner.py       → smart scanners (architecture, tests, docs, duplication, deps)
    qrouter.py       → Q-learning adaptive command routing
    perf.py          → command performance tracking (PerfTimer + analytics)
    session.py       → session save/restore/list
    graph.py         → mermaid, ascii, dot dependency graphs + critical path
    doctor.py        → 10+ health checks
  morph_client.py    → pure Python Morph API client (5 APIs)
  cc-flow.py         → backward-compatible shim
"""

VERSION = "4.3.0"
