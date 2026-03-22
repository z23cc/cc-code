"""cc-flow — task & workflow manager for cc-code plugin.

Usage:
    cc-flow <command>          (after pip install -e .)
    python -m cc_flow <command>

Package structure (19 modules, 68 subcommands):
  cc_flow/
    __init__.py      → VERSION
    __main__.py      → python -m cc_flow support
    entry.py         → lazy-loaded command dispatch (only imports needed module)
    cli.py           → argparse with 10 command categories
    core.py          → shared constants, utilities, error handling
    epic_task.py     → epic/task CRUD, templates, dep management
    views.py         → list, show, dashboard, progress, find, similar, export
    work.py          → start, done, block, rollback, reopen, diff, bulk
    route_learn.py   → route, learn, consolidate, rerank + embedding search
    auto.py          → autoimmune scan/run/test/full
    quality.py       → validate, scan, verify (auto-detect language)
    log_cmds.py      → log, summary, stats, standup, changelog, burndown, report, time
    config.py        → version, history, config, clean
    morph_cmds.py    → apply, search, embed, compact, github-search
    embeddings.py    → embedding cache, cosine similarity, semantic search
    workflow.py      → multi-step workflow pipelines (built-in + custom)
    session.py       → session save/restore/list
    graph.py         → mermaid, ascii, dot dependency graphs + critical path
    doctor.py        → 10+ health checks
  morph_client.py    → pure Python Morph API client (5 APIs)
  cc-flow.py         → backward-compatible shim
"""

VERSION = "4.0.0"
