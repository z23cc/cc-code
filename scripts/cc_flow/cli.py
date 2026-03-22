"""CLI argument parsing and command dispatch for cc-flow."""

import argparse

from cc_flow import VERSION


def _add_project_commands(sub):
    """Add project management subcommands: init, epic, task, dep."""
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
    task_update = task_sub.add_parser("update", help="Update task attributes")
    task_update.add_argument("id")
    task_update.add_argument("--title", default="")
    task_update.add_argument("--priority", type=int, default=None)
    task_update.add_argument("--size", choices=["XS", "S", "M", "L", "XL"], default="")
    task_update.add_argument("--tags", default="")
    task_comment = task_sub.add_parser("comment", help="Add a note to a task")
    task_comment.add_argument("id")
    task_comment.add_argument("--text", required=True)

    dep_p = sub.add_parser("dep", help="Dependency management")
    dep_sub = dep_p.add_subparsers(dest="dep_cmd")
    dep_add = dep_sub.add_parser("add")
    dep_add.add_argument("id")
    dep_add.add_argument("dep")
    dep_show = dep_sub.add_parser("show", help="Show dependency chain for a task")
    dep_show.add_argument("id")

    _add_template_commands(sub)


def _add_plugin_commands(sub):
    """Add plugin management subcommands."""
    plug_p = sub.add_parser("plugin", help="Plugin management (list/enable/disable/create)")
    plug_sub = plug_p.add_subparsers(dest="plugin_cmd")
    plug_sub.add_parser("list", help="List installed plugins")
    plug_en = plug_sub.add_parser("enable", help="Enable a plugin")
    plug_en.add_argument("name")
    plug_dis = plug_sub.add_parser("disable", help="Disable a plugin")
    plug_dis.add_argument("name")
    plug_create = plug_sub.add_parser("create", help="Scaffold a new plugin")
    plug_create.add_argument("name")


def _add_gh_commands(sub):
    """Add GitHub integration subcommands."""
    gh_p = sub.add_parser("gh", help="GitHub integration (import/export/status)")
    gh_sub = gh_p.add_subparsers(dest="gh_cmd")
    gh_import = gh_sub.add_parser("import", help="Import GitHub issues as tasks")
    gh_import.add_argument("--epic", required=True)
    gh_import.add_argument("--label", default="")
    gh_import.add_argument("--limit", type=int, default=20)
    gh_export = gh_sub.add_parser("export", help="Create GitHub issues from tasks")
    gh_export.add_argument("--epic", default="")
    gh_export.add_argument("--dry-run", action="store_true", default=False)
    gh_sub.add_parser("status", help="Show GitHub repo + cc-flow sync status")


def _add_context_commands(sub):
    """Add context management subcommands."""
    ctx_p = sub.add_parser("context", help="Project context management")
    ctx_sub = ctx_p.add_subparsers(dest="context_cmd")
    ctx_save = ctx_sub.add_parser("save", help="Save current context snapshot")
    ctx_save.add_argument("--name", default="default")
    ctx_sub.add_parser("show", help="Show saved context")
    ctx_sub.add_parser("brief", help="One-paragraph project brief")


def _add_alias_commands(sub):
    """Add alias management subcommands."""
    alias_p = sub.add_parser("alias", help="Command aliases (shortcuts)")
    alias_sub = alias_p.add_subparsers(dest="alias_cmd")
    alias_sub.add_parser("list", help="List aliases")
    alias_set = alias_sub.add_parser("set", help="Set alias: alias set <name> <cmd...>")
    alias_set.add_argument("name")
    alias_set.add_argument("target", nargs="*", help="Command to alias")
    alias_rm = alias_sub.add_parser("remove", help="Remove an alias")
    alias_rm.add_argument("name")


def _add_workflow_commands(sub):
    """Add workflow subcommands."""
    wf_p = sub.add_parser("workflow", help="Multi-step workflow pipelines")
    wf_sub = wf_p.add_subparsers(dest="workflow_cmd")
    wf_sub.add_parser("list", help="List available workflows")
    wf_show = wf_sub.add_parser("show", help="Show workflow details")
    wf_show.add_argument("name")
    wf_run = wf_sub.add_parser("run", help="Execute a workflow")
    wf_run.add_argument("name")
    wf_run.add_argument("--dry-run", action="store_true", default=False)
    wf_create = wf_sub.add_parser("create", help="Create custom workflow")
    wf_create.add_argument("name")
    wf_create.add_argument("--steps", required=True, help="Comma-separated commands")
    wf_create.add_argument("--description", default="")


def _add_template_commands(sub):
    """Add template management subcommands."""
    tmpl_p = sub.add_parser("template", help="Task template management")
    tmpl_sub = tmpl_p.add_subparsers(dest="template_cmd")
    tmpl_sub.add_parser("list", help="List available templates")
    tmpl_show = tmpl_sub.add_parser("show", help="Show template details")
    tmpl_show.add_argument("name")
    tmpl_create = tmpl_sub.add_parser("create", help="Create custom template")
    tmpl_create.add_argument("name")
    tmpl_create.add_argument("--steps", required=True, help="Comma-separated step names")
    tmpl_create.add_argument("--spec", default="", help="Spec content (or auto-generated)")


def _add_view_commands(sub):
    """Add view/query subcommands: list, epics, tasks, show, ready, next, progress, etc."""
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
    cp_p = sub.add_parser("critical-path", help="Find longest dependency chain")
    cp_p.add_argument("--epic", default="")
    export_p = sub.add_parser("export", help="Export epic as markdown report")
    export_p.add_argument("id")
    export_p.add_argument("--output", default="", help="Output file path (default: stdout)")
    find_p = sub.add_parser("find", help="Search across task titles and specs")
    find_p.add_argument("query", nargs="*")
    find_p.add_argument("--semantic", action="store_true", default=False, help="Use embedding-based search")
    priority_p = sub.add_parser("priority", help="Tasks sorted by priority (ready first)")
    priority_p.add_argument("--status", default="", help="Filter by status")
    similar_p = sub.add_parser("similar", help="Find tasks similar to a given task (embedding)")
    similar_p.add_argument("id")
    similar_p.add_argument("--top", type=int, default=5)
    sub.add_parser("index", help="Pre-build embedding index for all tasks")
    dedupe_p = sub.add_parser("dedupe", help="Detect near-duplicate tasks (embedding)")
    dedupe_p.add_argument("--threshold", type=float, default=0.85, help="Similarity threshold (default: 0.85)")
    suggest_p = sub.add_parser("suggest", help="Suggest approach based on similar completed tasks")
    suggest_p.add_argument("id")


def _add_work_commands(sub):
    """Add work lifecycle subcommands: start, done, block, rollback."""
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
    reopen_p = sub.add_parser("reopen", help="Reopen a done/blocked task")
    reopen_p.add_argument("id")
    reopen_p.add_argument("--reason", default="")
    diff_p = sub.add_parser("diff", help="Show git changes since task started")
    diff_p.add_argument("id")
    diff_p.add_argument("--stat", action="store_true", default=False, help="Show stat only")
    diff_p.add_argument("--json", action="store_true", default=False)
    bulk_p = sub.add_parser("bulk", help="Batch status change (done/todo/blocked)")
    bulk_p.add_argument("action", choices=["done", "todo", "blocked"])
    bulk_p.add_argument("ids", nargs="*", help="Task IDs (or use --epic)")
    bulk_p.add_argument("--epic", default="", help="Apply to all tasks in epic")


def _add_quality_commands(sub):
    """Add quality/auto subcommands: validate, scan, verify, doctor, auto."""
    sub.add_parser("validate", help="Check structure, deps, cycles")
    scan_p = sub.add_parser("scan", help="Auto-detect issues via ruff/mypy/bandit")
    scan_p.add_argument("--create-tasks", action="store_true", default=False)
    verify_p = sub.add_parser("verify", help="Run lint + test (auto-detects language)")
    verify_p.add_argument("--fix", action="store_true", default=False, help="Auto-fix lint issues first")
    doctor_p = sub.add_parser("doctor", help="Health check — environment, tools, tasks")
    doctor_p.add_argument("--format", choices=["text", "json"], default="text")

    auto_p = sub.add_parser("auto", help="Autoimmune loop integrated with task system")
    auto_sub = auto_p.add_subparsers(dest="auto_cmd")
    auto_sub.add_parser("scan")
    auto_run = auto_sub.add_parser("run")
    auto_run.add_argument("--epic", default="")
    auto_run.add_argument("--max", type=int, default=20)
    auto_sub.add_parser("test")
    auto_sub.add_parser("full")
    auto_sub.add_parser("deep", help="Multi-dimensional scan (architecture+tests+docs+deps)")
    auto_sub.add_parser("status")


def _add_route_learn_commands(sub):
    """Add routing and learning subcommands: route, learn, learnings, consolidate."""
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


def _add_session_commands(sub):
    """Add session management subcommands: session save/restore/list."""
    sess_p = sub.add_parser("session", help="Save/restore session state")
    sess_sub = sess_p.add_subparsers(dest="session_cmd")
    sess_save = sess_sub.add_parser("save")
    sess_save.add_argument("--name", default="")
    sess_save.add_argument("--notes", default="")
    sess_restore = sess_sub.add_parser("restore")
    sess_restore.add_argument("name", nargs="?", default="latest")
    sess_sub.add_parser("list")


def _add_morph_commands(sub):
    """Add Morph API subcommands: apply, search, embed, compact, github-search."""
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


def _add_eval_commands(sub):
    """Add evaluation harness subcommands."""
    ev_p = sub.add_parser("eval", help="Coding capability evaluation")
    ev_sub = ev_p.add_subparsers(dest="eval_cmd")
    ev_run = ev_sub.add_parser("run", help="Run evaluation suite")
    ev_run.add_argument("--dimensions", default="", help="Comma-separated: route,search,speed,health")
    ev_detail = ev_sub.add_parser("detail", help="Detailed results for one dimension")
    ev_detail.add_argument("dimension")
    ev_sub.add_parser("history", help="Score history and trends")


def _add_misc_commands(sub):
    """Add misc subcommands: log, summary, archive, stats, perf, insights, version, config."""
    perf_p = sub.add_parser("perf", help="Command performance analytics")
    perf_p.add_argument("--top", type=int, default=10)
    forecast_p = sub.add_parser("forecast", help="Predict epic completion date from velocity")
    forecast_p.add_argument("--epic", default="")
    sub.add_parser("evolve", help="Meta-learning: recommend next improvement focus")
    sub.add_parser("health", help="Composite project health score (0-100)")
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
    standup_p = sub.add_parser("standup", help="Daily standup report (done/active/blocked/next)")
    standup_p.add_argument("--hours", type=int, default=24, help="Lookback period (default: 24h)")
    changelog_p = sub.add_parser("changelog", help="Generate changelog from completed tasks")
    changelog_p.add_argument("--json", action="store_true", default=False)
    burndown_p = sub.add_parser("burndown", help="Epic burndown data (remaining tasks over time)")
    burndown_p.add_argument("--epic", required=True)
    report_p = sub.add_parser("report", help="Comprehensive project report (markdown)")
    report_p.add_argument("--output", default="", help="Save to file")
    time_p = sub.add_parser("time", help="Time tracking report (duration per task, averages)")
    time_p.add_argument("--epic", default="")
    sub.add_parser("version", help="Print cc-flow version")
    config_p = sub.add_parser("config", help="View/set cc-flow configuration")
    config_p.add_argument("key", nargs="?", default="")
    config_p.add_argument("value", nargs="?", default="")
    clean_p = sub.add_parser("clean", help="Remove old sessions and archived data")
    clean_p.add_argument("--days", type=int, default=30, help="Max age in days (default: 30)")
    clean_p.add_argument("--dry-run", action="store_true", default=False, help="Preview without deleting")
    profile_p = sub.add_parser("profile", help="Apply a configuration profile")
    profile_p.add_argument("action", nargs="?", default="list", choices=["list", "apply"])
    profile_p.add_argument("name", nargs="?", default="")


_HELP_CATEGORIES = """
Command categories:
  Project:    init, epic, task, dep, template
  Views:      list, epics, tasks, show, ready, next, progress, status,
              dashboard, graph, export, find, similar, priority, critical-path
  Work:       start, done, block, rollback, reopen, diff, bulk
  Quality:    validate, scan, verify, doctor, auto
  Search:     search, find --semantic, similar, index, dedupe, suggest
  Analytics:  stats, standup, changelog, burndown, report, time, history
  Routing:    route, learn, learnings, consolidate
  Session:    session save/restore/list
  Morph API:  apply, search, embed, compact, github-search
  Config:     config, clean, version
"""


def build_parser():
    """Build the complete argparse parser."""
    parser = argparse.ArgumentParser(
        prog="cc-flow",
        description="cc-code task & workflow manager",
        epilog=_HELP_CATEGORIES,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("-V", "--version", action="version", version=f"cc-flow {VERSION}")
    sub = parser.add_subparsers(dest="command")

    _add_project_commands(sub)
    _add_view_commands(sub)
    _add_work_commands(sub)
    _add_quality_commands(sub)
    _add_route_learn_commands(sub)
    _add_session_commands(sub)
    _add_morph_commands(sub)
    _add_workflow_commands(sub)
    _add_plugin_commands(sub)
    _add_gh_commands(sub)
    _add_context_commands(sub)
    _add_alias_commands(sub)
    _add_eval_commands(sub)
    _add_misc_commands(sub)

    # Let plugins register their own commands
    try:
        from cc_flow.plugins import register_plugin_commands
        register_plugin_commands(sub)
    except ImportError:
        pass

    return parser
