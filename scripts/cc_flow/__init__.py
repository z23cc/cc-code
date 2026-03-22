"""cc-flow — task & workflow manager for cc-code plugin.

Usage:
    cc-flow <command>          (after pip install -e .)
    python -m cc_flow <command>
    python scripts/cc-flow.py <command>  (legacy shim)

Package structure:
  cc_flow/
    __init__.py      → VERSION
    __main__.py      → python -m cc_flow support
    entry.py         → CLI entry point (main function)
    cli.py           → argparse (39 subcommands)
    core.py          → shared constants + utilities
    epic_task.py     → epic/task CRUD, templates
    views.py         → list, show, dashboard, progress
    work.py          → start, done, block, rollback, diff tracking
    route_learn.py   → route, learn, consolidate, rerank
    auto.py          → autoimmune scan/run/test/full, team patterns
    quality.py       → validate, scan
    log_cmds.py      → log, summary, archive, stats
    config.py        → version, history, config
    morph_cmds.py    → apply, search, embed, compact, github-search
    session.py       → session save/restore/list
    graph.py         → mermaid, ascii, dot dependency graphs
    doctor.py        → 10 health checks
  morph_client.py    → pure Python Morph API client (5 APIs)
  cc-flow.py         → backward-compatible shim
"""

VERSION = "3.12.0"
