"""cc-flow — task & workflow manager for cc-code plugin.

Package structure:
  cc-flow.py         → thin shim (90 lines, imports + dispatch)
  cc_flow/
    __init__.py      → VERSION
    cli.py           → argparse (39 subcommands)
    core.py          → shared constants + utilities
    epic_task.py     → epic/task CRUD, templates
    views.py         → list, show, dashboard, progress
    work.py          → start, done, block, rollback, diff tracking
    route_learn.py   → route, learn, consolidate, rerank
    auto.py          → autoimmune scan/run/test/full, team patterns
    misc.py          → validate, scan, log, stats, config
    morph_cmds.py    → apply, search, embed, compact, github-search
    session.py       → session save/restore/list
    graph.py         → mermaid, ascii, dot dependency graphs
    doctor.py        → 10 health checks
  morph_client.py    → pure Python Morph API client (5 APIs)
"""

VERSION = "3.8.0"
