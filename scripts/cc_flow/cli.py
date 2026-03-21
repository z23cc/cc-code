"""CLI argument parsing and command dispatch for cc-flow."""

import argparse

from cc_flow import VERSION


def build_parser():
    """Build the complete argparse parser."""
    parser = argparse.ArgumentParser(prog="cc-flow", description="cc-code task & workflow manager")
    parser.add_argument("-V", "--version", action="version", version=f"cc-flow {VERSION}")
    sub = parser.add_subparsers(dest="command")

    # Project
    sub.add_parser("init", help="Initialize .tasks/ directory")

    epic_p = sub.add_parser("epic", help="Epic management (create/close/import/reset)")
    epic_sub = epic_p.add_subparsers(dest="epic_cmd")
    ec = epic_sub.add_parser("create")
    ec.add_argument("--title", required=True)
    epic_close = epic_sub.add_parser("close")
    epic_close.add_argument("id")
    epic_import = epic_sub.add_parser("import")
    epic_import.add_argument("--file", required=True)
    epic_import.add_argument("--sequential", action="store_true", default=False)
    epic_reset = epic_sub.add_parser("reset")
    epic_reset.add_argument("id")

    tc = sub.add_parser("task", help="Task management (create/reset/set-spec)")
    task_sub = tc.add_subparsers(dest="task_cmd")
    tc_create = task_sub.add_parser("create")
    tc_create.add_argument("--epic", required=True)
    tc_create.add_argument("--title", required=True)
    tc_create.add_argument("--deps", default="")
    tc_create.add_argument("--size", choices=["XS", "S", "M", "L", "XL"], default="M")
    tc_create.add_argument("--tags", default="")
    tc_create.add_argument("--template", choices=["feature", "bugfix", "refactor", "security"], default="")
    task_reset = task_sub.add_parser("reset")
    task_reset.add_argument("id")
    task_set_spec = task_sub.add_parser("set-spec")
    task_set_spec.add_argument("id")
    task_set_spec.add_argument("--file", required=True)

    dep_p = sub.add_parser("dep", help="Dependency management")
    dep_sub = dep_p.add_subparsers(dest="dep_cmd")
    dep_add = dep_sub.add_parser("add")
    dep_add.add_argument("id")
    dep_add.add_argument("dep")

    # Views
    list_p = sub.add_parser("list", help="Show all epics + tasks")
    list_p.add_argument("--json", action="store_true", default=False)
    sub.add_parser("epics", help="List epics (JSON)")
    tasks_p = sub.add_parser("tasks", help="Filter tasks by epic/status/tag")
    tasks_p.add_argument("--epic", default="")
    tasks_p.add_argument("--status", default="")
    tasks_p.add_argument("--tag", default="")
    show_p = sub.add_parser("show", help="Show epic or task detail")
    show_p.add_argument("id")
    ready_p = sub.add_parser("ready", help="Tasks with all deps satisfied")
    ready_p.add_argument("--epic", default="")
    next_p = sub.add_parser("next", help="Smart next task (priority-aware)")
    next_p.add_argument("--epic", default="")
    progress_p = sub.add_parser("progress", help="Progress bars per epic")
    progress_p.add_argument("--epic", default="")
    progress_p.add_argument("--json", action="store_true", default=False)
    sub.add_parser("status", help="Global overview (JSON)")
    dash_p = sub.add_parser("dashboard", help="One-screen overview (--json for machine-readable)")
    dash_p.add_argument("--json", action="store_true", default=False)
    graph_p = sub.add_parser("graph", help="Dependency graph (mermaid/ascii/dot)")
    graph_p.add_argument("--epic", default="")
    graph_p.add_argument("--format", choices=["mermaid", "ascii", "dot"], default="mermaid")
    graph_p.add_argument("--json", action="store_true", default=False)
    sub.add_parser("history", help="Task completion timeline with velocity trends")

    # Work
    start_p = sub.add_parser("start", help="Start a task (checks deps)")
    start_p.add_argument("id")
    done_p = sub.add_parser("done", help="Complete a task")
    done_p.add_argument("id")
    done_p.add_argument("--summary", default="")
    block_p = sub.add_parser("block", help="Block a task with reason")
    block_p.add_argument("id")
    block_p.add_argument("--reason", required=True)
    rollback_p = sub.add_parser("rollback", help="Rollback failed task to git state")
    rollback_p.add_argument("id")
    rollback_p.add_argument("--confirm", action="store_true", default=False)

    # Quality
    sub.add_parser("validate", help="Check structure, deps, cycles")
    scan_p = sub.add_parser("scan", help="Auto-detect issues via ruff/mypy/bandit")
    scan_p.add_argument("--create-tasks", action="store_true", default=False)
    doctor_p = sub.add_parser("doctor", help="Health check — environment, tools, tasks")
    doctor_p.add_argument("--format", choices=["text", "json"], default="text")

    # Auto
    auto_p = sub.add_parser("auto", help="Autoimmune loop integrated with task system")
    auto_sub = auto_p.add_subparsers(dest="auto_cmd")
    auto_sub.add_parser("scan")
    auto_run = auto_sub.add_parser("run")
    auto_run.add_argument("--epic", default="")
    auto_run.add_argument("--max", type=int, default=20)
    auto_sub.add_parser("test")
    auto_sub.add_parser("full")
    auto_sub.add_parser("status")

    # Routing + Learning
    route_p = sub.add_parser("route", help="Smart router: analyze task → suggest command + team")
    route_p.add_argument("query", nargs="*")
    learn_p = sub.add_parser("learn", help="Record a learning for future routing")
    learn_p.add_argument("--task", required=True)
    learn_p.add_argument("--outcome", required=True, choices=["success", "partial", "failed"])
    learn_p.add_argument("--approach", required=True)
    learn_p.add_argument("--lesson", required=True)
    learn_p.add_argument("--score", type=int, default=3)
    learn_p.add_argument("--used-command", dest="used_command", default="")
    learnings_p = sub.add_parser("learnings", help="List/search past learnings")
    learnings_p.add_argument("--search", default="")
    learnings_p.add_argument("--last", type=int, default=10)
    sub.add_parser("consolidate", help="Merge similar learnings, promote patterns")

    # Session
    sess_p = sub.add_parser("session", help="Save/restore session state")
    sess_sub = sess_p.add_subparsers(dest="session_cmd")
    sess_save = sess_sub.add_parser("save")
    sess_save.add_argument("--name", default="")
    sess_save.add_argument("--notes", default="")
    sess_restore = sess_sub.add_parser("restore")
    sess_restore.add_argument("name", nargs="?", default="latest")
    sess_sub.add_parser("list")

    # Morph
    apply_p = sub.add_parser("apply", help="Fast Apply code changes via Morph (10,500+ tok/s)")
    apply_p.add_argument("--file", required=True, help="File to modify")
    apply_p.add_argument("--instruction", required=True, help="What to change")
    apply_p.add_argument("--update", default="", help="Code snippet (or stdin)")
    apply_p.add_argument("--model", default="auto", choices=["morph-v3-fast", "morph-v3-large", "auto"])

    search_p = sub.add_parser("search", help="Semantic code search (morph → grep fallback)")
    search_p.add_argument("query", nargs="*")
    search_p.add_argument("--dir", default=".")
    search_p.add_argument("--format", choices=["text", "json"], default="text")
    search_p.add_argument("--rerank", action="store_true", default=False)

    embed_p = sub.add_parser("embed", help="Generate code embeddings (1536 dims)")
    embed_p.add_argument("--input", default="", help="Text to embed")
    embed_p.add_argument("--file", default="", help="File to embed")

    compact_p = sub.add_parser("compact", help="Compress text via morph")
    compact_p.add_argument("--file", default="")
    compact_p.add_argument("--ratio", default="0.3")
    compact_p.add_argument("--output", default="")

    ghsearch_p = sub.add_parser("github-search", help="Search GitHub repos")
    ghsearch_p.add_argument("query", nargs="*")
    ghsearch_p.add_argument("--repo", default="")
    ghsearch_p.add_argument("--url", default="")

    # Misc
    log_p = sub.add_parser("log")
    log_p.add_argument("--show", type=int, default=0)
    log_p.add_argument("--iteration", type=int, default=None)
    log_p.add_argument("--mode", default="")
    log_p.add_argument("--area", default="")
    log_p.add_argument("--task-id", default="")
    log_p.add_argument("--description", default="")
    log_p.add_argument("--status", default="")
    log_p.add_argument("--files", type=int, default=None)
    log_p.add_argument("--diff-lines", type=int, default=None)
    log_p.add_argument("--duration", type=int, default=None)
    log_p.add_argument("--notes", default="")
    sub.add_parser("summary", help="Autoimmune session summary")
    sub.add_parser("archive", help="Show completed epics/tasks")
    sub.add_parser("stats", help="Productivity metrics")
    sub.add_parser("version", help="Print cc-flow version")
    config_p = sub.add_parser("config", help="View/set cc-flow configuration")
    config_p.add_argument("key", nargs="?", default="")
    config_p.add_argument("value", nargs="?", default="")

    return parser
