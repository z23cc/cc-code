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

    # Skills marketplace (skills.sh)
    skills_p = sub.add_parser("skills", help="Search/install skills from skills.sh marketplace")
    skills_sub = skills_p.add_subparsers(dest="skills_cmd")
    sk_find = skills_sub.add_parser("find", help="Search for skills by keyword")
    sk_find.add_argument("query", nargs="*")
    sk_add = skills_sub.add_parser("add", help="Install a skill package")
    sk_add.add_argument("package")
    sk_add.add_argument("-g", "--global", dest="global_install", action="store_true", default=False)
    skills_sub.add_parser("list", help="List installed skills")


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
    wf_chain = wf_sub.add_parser("chain", help="Run ad-hoc command chain: 'verify,scan,health'")
    wf_chain.add_argument("chain", help="Comma-separated commands")

    # Pipelines (context-aware skill orchestration)
    pipe_p = sub.add_parser("pipeline", help="Skill orchestration with context passing")
    pipe_sub = pipe_p.add_subparsers(dest="pipeline_cmd")
    pipe_sub.add_parser("list", help="List available pipelines")
    pipe_run = pipe_sub.add_parser("run", help="Execute a pipeline")
    pipe_run.add_argument("name")
    pipe_create = pipe_sub.add_parser("create", help="Create custom pipeline")
    pipe_create.add_argument("name")
    pipe_create.add_argument("--steps", required=True, help="Comma-separated commands")
    pipe_create.add_argument("--description", default="")

    # Memory (Supermemory integration)
    mem_p = sub.add_parser("memory", help="Persistent knowledge via Supermemory")
    mem_sub = mem_p.add_subparsers(dest="memory_cmd")
    mem_save = mem_sub.add_parser("save", help="Save knowledge to Supermemory")
    mem_save.add_argument("--content", required=True)
    mem_save.add_argument("--tags", default="")
    mem_search = mem_sub.add_parser("search", help="Search knowledge (semantic + rerank)")
    mem_search.add_argument("query", nargs="*")
    mem_search.add_argument("--limit", type=int, default=5)
    mem_sub.add_parser("sync", help="Sync local learnings to Supermemory")
    mem_forget = mem_sub.add_parser("forget", help="Remove outdated knowledge")
    mem_forget.add_argument("--content", required=True, help="What to forget")
    mem_forget.add_argument("--reason", default="outdated")
    mem_recall = mem_sub.add_parser("recall", help="Search learnings for routing")
    mem_recall.add_argument("query", nargs="*")

    # Skill chains
    chain_p = sub.add_parser("chain", help="Multi-skill workflows (predefined chains)")
    chain_sub = chain_p.add_subparsers(dest="chain_cmd")
    chain_sub.add_parser("list", help="List skill chains")
    chain_show = chain_sub.add_parser("show", help="Show chain details")
    chain_show.add_argument("name")
    chain_suggest = chain_sub.add_parser("suggest", help="Suggest best chain for a task")
    chain_suggest.add_argument("query", nargs="*")
    chain_run = chain_sub.add_parser("run", help="Execute a skill chain")
    chain_run.add_argument("name")
    chain_run.add_argument("--required-only", action="store_true", default=False)
    chain_advance = chain_sub.add_parser("advance", help="Advance chain to next step")
    chain_advance.add_argument("--data", default="{}", help="JSON context from completed step")
    chain_sub.add_parser("stats", help="Show chain execution metrics")


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


def _add_worktree_commands(sub):
    """Add worktree management subcommands."""
    wt_p = sub.add_parser("worktree", help="Worktree management (create/list/switch/remove/status/info)")
    wt_sub = wt_p.add_subparsers(dest="wt_cmd")

    wt_create = wt_sub.add_parser("create", help="Create a new worktree")
    wt_create.add_argument("name", help="Worktree name (becomes branch name)")
    wt_create.add_argument("--base", default="", help="Base branch (default: main)")

    wt_sub.add_parser("list", help="List all worktrees with branch and status")

    wt_switch = wt_sub.add_parser("switch", help="Print worktree path (for cd)")
    wt_switch.add_argument("name")

    wt_remove = wt_sub.add_parser("remove", help="Remove a worktree")
    wt_remove.add_argument("name")

    wt_sub.add_parser("cleanup", help="Remove all managed worktrees")
    wt_sub.add_parser("status", help="Show dirty/clean status of all worktrees")
    wt_sub.add_parser("info", help="Show current worktree context (or main checkout)")


def _add_quality_commands(sub):
    """Add quality/auto subcommands: validate, scan, verify, doctor, auto."""
    sub.add_parser("validate", help="Check structure, deps, cycles")
    scan_p = sub.add_parser("scan", help="Auto-detect issues via ruff/mypy/bandit")
    scan_p.add_argument("--create-tasks", action="store_true", default=False)
    verify_p = sub.add_parser("verify", help="Run lint + test (auto-detects language)")
    verify_p.add_argument("--fix", action="store_true", default=False, help="Auto-fix lint issues first")
    doctor_p = sub.add_parser("doctor", help="Health check — environment, tools, tasks")
    doctor_p.add_argument("--format", choices=["text", "json"], default="text")

    sub.add_parser("validate-skills", help="Validate all SKILL.md files (frontmatter, triggers, quality)")

    ralph_p = sub.add_parser("ralph", help="Autonomous execution (one command, unattended)")
    ralph_p.add_argument("--goal", default="", help="Goal to achieve (enables goal-driven mode)")
    ralph_p.add_argument("--max", type=int, default=25, help="Max iterations (default: 25)")
    ralph_p.add_argument("--no-yolo", action="store_true", default=False, help="Require permission prompts")
    ralph_p.add_argument("--watch", action="store_true", default=False, help="Watch mode (stream output)")

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


def _add_bridge_commands(sub):
    """Add bridge commands (Morph × RP × Supermemory collaboration)."""
    ds_p = sub.add_parser("deep-search", help="Morph search → RP select → RP builder (deep understanding)")
    ds_p.add_argument("query", nargs="*")
    ds_p.add_argument("--type", choices=["question", "plan", "review", "clarify"], default="question")

    sc_p = sub.add_parser("smart-chat", help="Memory-enhanced RP chat (recall → inject → chat)")
    sc_p.add_argument("message")
    sc_p.add_argument("--mode", choices=["chat", "plan", "review", "edit"], default="chat")
    sc_p.add_argument("--new", action="store_true", default=True)

    es_p = sub.add_parser("embed-structure", help="RP code structure → Morph embed (similarity search)")
    es_p.add_argument("paths", nargs="*", default=["."])

    rr_p = sub.add_parser("recall-review", help="Recall past review findings from Supermemory")
    rr_p.add_argument("query", nargs="*")

    sub.add_parser("bridge-status", help="Show Morph × RP × Supermemory connection status")


def _add_eval_commands(sub):
    """Add evaluation harness subcommands."""
    ev_p = sub.add_parser("eval", help="Coding capability evaluation")
    ev_sub = ev_p.add_subparsers(dest="eval_cmd")
    ev_run = ev_sub.add_parser("run", help="Run evaluation suite")
    ev_run.add_argument("--dimensions", default="", help="Comma-separated: route,search,speed,health")
    ev_detail = ev_sub.add_parser("detail", help="Detailed results for one dimension")
    ev_detail.add_argument("dimension")
    ev_sub.add_parser("history", help="Score history and trends")
    ev_cross = ev_sub.add_parser("cross", help="Test cc-flow across multiple real projects")
    ev_cross.add_argument("--dir", default="", help="Directory containing projects")
    ev_cross.add_argument("--limit", type=int, default=5)


def _add_rp_commands(sub):
    """Add RepoPrompt (rp-cli) integration subcommands."""
    # Parent parser with shared rp options (inherited by all rp subcommands)
    rp_parent = argparse.ArgumentParser(add_help=False)
    rp_parent.add_argument("-w", "--window", type=int, default=None, help="Target RP window ID")
    rp_parent.add_argument("-t", "--tab", default=None, help="Target RP tab name/UUID")
    rp_parent.add_argument("--json", action="store_true", default=False, help="JSON output")

    rp_p = sub.add_parser("rp", help="RepoPrompt integration (rp-cli wrapper)")
    rp_sub = rp_p.add_subparsers(dest="rp_cmd")

    P = [rp_parent]  # Shorthand for parents kwarg

    # check
    rp_sub.add_parser("check", help="Check if rp-cli is available")

    # windows
    rp_sub.add_parser("windows", help="List RepoPrompt windows", parents=P)

    # workspace
    ws_p = rp_sub.add_parser("workspace", help="Manage workspaces", parents=P)
    ws_p.add_argument("action", choices=["list", "switch", "create", "delete", "tabs"], default="list", nargs="?")
    ws_p.add_argument("name", nargs="?", default="")
    ws_p.add_argument("--folder-path", default="")
    ws_p.add_argument("--new-window", action="store_true", default=False)
    ws_p.add_argument("--close-window", action="store_true", default=False)

    # tabs
    tabs_p = rp_sub.add_parser("tabs", help="Manage compose tabs", parents=P)
    tabs_p.add_argument("action", choices=["list", "create", "close"], default="list", nargs="?")
    tabs_p.add_argument("name", nargs="?", default="")
    tabs_p.add_argument("--allow-active", action="store_true", default=False)

    # select
    sel_p = rp_sub.add_parser("select", help="Manage file selection", parents=P)
    sel_p.add_argument("op", choices=["get", "set", "add", "remove", "clear"], default="get", nargs="?")
    sel_p.add_argument("paths", nargs="*", default=[])

    # builder
    bld_p = rp_sub.add_parser("builder", help="Context builder", parents=P)
    bld_p.add_argument("instructions")
    bld_p.add_argument("--type", choices=["clarify", "question", "plan", "review"], default=None)

    # plan (shorthand for chat --mode plan)
    plan_p = rp_sub.add_parser("plan", help="Architecture plan request (new chat)", parents=P)
    plan_p.add_argument("message")

    # review (shorthand for chat --mode review)
    rev_p = rp_sub.add_parser("review", help="Code review request (new chat)", parents=P)
    rev_p.add_argument("message", nargs="?", default="")

    # chat
    chat_p = rp_sub.add_parser("chat", help="Send chat message", parents=P)
    chat_p.add_argument("message", nargs="?", default="")
    chat_p.add_argument("--message-file", default="")
    chat_p.add_argument("--new", action="store_true", default=False)
    chat_p.add_argument("--chat-name", default="")

    # read
    read_p = rp_sub.add_parser("read", help="Read file", parents=P)
    read_p.add_argument("path")
    read_p.add_argument("start_line", type=int, nargs="?", default=None)
    read_p.add_argument("limit_n", type=int, nargs="?", default=None)

    # search
    srch_p = rp_sub.add_parser("search", help="Search files", parents=P)
    srch_p.add_argument("pattern")
    srch_p.add_argument("--extensions", default="")
    srch_p.add_argument("--context-lines", type=int, default=None)

    # tree
    tree_p = rp_sub.add_parser("tree", help="File tree", parents=P)
    tree_p.add_argument("--mode", choices=["full", "folders", "selected"], default=None)
    tree_p.add_argument("--max-depth", type=int, default=None)
    tree_p.add_argument("path", nargs="?", default="")

    # structure
    struct_p = rp_sub.add_parser("structure", help="Code structure (codemaps)", parents=P)
    struct_p.add_argument("paths", nargs="+")

    # context
    ctx_p = rp_sub.add_parser("context", help="Workspace context snapshot", parents=P)
    ctx_p.add_argument("--all", action="store_true", default=False)

    # prompt
    prm_p = rp_sub.add_parser("prompt", help="Prompt management", parents=P)
    prm_p.add_argument("op", choices=["get", "set", "export"], default="get", nargs="?")
    prm_p.add_argument("--text", default="")
    prm_p.add_argument("--export-path", default="")

    # chats
    chats_p = rp_sub.add_parser("chats", help="Chat history", parents=P)
    chats_p.add_argument("action", choices=["list", "log"], default="list", nargs="?")
    chats_p.add_argument("--scope", choices=["workspace", "tab"], default="workspace")
    chats_p.add_argument("--chat-id", default="")
    chats_p.add_argument("--limit-n", type=int, default=None)

    # models
    rp_sub.add_parser("models", help="List AI model presets", parents=P)

    # git
    git_p = rp_sub.add_parser("git", help="Git operations via RP", parents=P)
    git_p.add_argument("op", choices=["status", "diff", "log", "show", "blame"], default="status", nargs="?")
    git_p.add_argument("--compare", default=None)
    git_p.add_argument("--detail", choices=["files", "patches", "full"], default=None)
    git_p.add_argument("--count", type=int, default=None)
    git_p.add_argument("--artifacts", action="store_true", default=False)

    # edit (apply_edits)
    edit_p = rp_sub.add_parser("edit", help="Apply file edits", parents=P)
    edit_p.add_argument("path")
    edit_p.add_argument("--search-text", required=True)
    edit_p.add_argument("--replace-text", required=True)

    # file (file_actions)
    file_p = rp_sub.add_parser("file", help="File actions (create/delete/move)", parents=P)
    file_p.add_argument("action", choices=["create", "delete", "move"])
    file_p.add_argument("path")
    file_p.add_argument("--content", default=None)
    file_p.add_argument("--new-path", default=None)

    # setup-review (composite)
    sr_p = rp_sub.add_parser("setup-review", help="Atomic: pick window + builder for review", parents=P)
    sr_p.add_argument("--summary", default="Review recent changes")
    sr_p.add_argument("--repo-root", default=None)
    sr_p.add_argument("--type", choices=["clarify", "question", "plan", "review"], default=None)

    # session
    sess_p = rp_sub.add_parser("session", help="RP session state (window/tab binding)")
    sess_p.add_argument("action", choices=["show", "clear"], default="show", nargs="?")

    # worktree-setup
    wts_p = rp_sub.add_parser("worktree-setup", help="Create RP workspace for a worktree", parents=P)
    wts_p.add_argument("worktree_path")

    # worktree-cleanup
    wtc_p = rp_sub.add_parser("worktree-cleanup", help="Remove RP workspace for a worktree", parents=P)
    wtc_p.add_argument("worktree_path")

    # worktree-status (query by branch, no workspace switch)
    wt_status_p = rp_sub.add_parser("worktree-status", help="Git status for a worktree branch (@main:<branch>)", parents=P)
    wt_status_p.add_argument("branch", help="Branch name of the worktree")

    # worktree-diff (query by branch, no workspace switch)
    wt_diff_p = rp_sub.add_parser("worktree-diff", help="Git diff for a worktree branch vs trunk", parents=P)
    wt_diff_p.add_argument("branch", help="Branch name of the worktree")
    wt_diff_p.add_argument("--compare", default="main", help="Compare target (default: main)")
    wt_diff_p.add_argument("--detail", choices=["summary", "files", "patches", "full"], default="files")

    # run (raw passthrough)
    run_p = rp_sub.add_parser("run", help="Run raw rp-cli -e command", parents=P)
    run_p.add_argument("command")


def _add_checkpoint_commands(sub):
    """Add checkpoint subcommands: create/verify/compare/list."""
    cp_p = sub.add_parser("checkpoint", help="Workflow state snapshots (create/verify/compare/list)")
    cp_sub = cp_p.add_subparsers(dest="checkpoint_cmd")
    cp_create = cp_sub.add_parser("create", help="Save a checkpoint snapshot")
    cp_create.add_argument("name", help="Checkpoint name (e.g. core-done)")
    cp_verify = cp_sub.add_parser("verify", help="Compare current state vs checkpoint")
    cp_verify.add_argument("name", help="Checkpoint name to verify against")
    cp_compare = cp_sub.add_parser("compare", help="Diff two checkpoints")
    cp_compare.add_argument("name1", help="First checkpoint name")
    cp_compare.add_argument("name2", help="Second checkpoint name")
    cp_sub.add_parser("list", help="List all checkpoints")

    # Context budget (standalone command)
    sub.add_parser("context-budget", help="Analyze token overhead from plugins, rules, skills")


def _add_skill_flow_commands(sub):
    """Add skill flow graph and context subcommands."""
    skill_p = sub.add_parser("skill", help="Skill flow graph and context protocol")
    skill_sub = skill_p.add_subparsers(dest="skill_cmd")

    # skill next [--skill name]
    skill_next = skill_sub.add_parser("next", help="Suggest next skill based on flow graph")
    skill_next.add_argument("--skill", default="", help="Which skill just completed")

    # skill graph [--for name]
    skill_graph = skill_sub.add_parser("graph", help="Show skill flow graph")
    skill_graph.add_argument("--for", dest="for_skill", default="", help="Show graph for a specific skill")

    # skill graph-build
    skill_sub.add_parser("graph-build", help="Force rebuild the skill flow graph cache")

    # skill ctx {save|load|current|clear}
    skill_ctx = skill_sub.add_parser("ctx", help="Skill context operations")
    ctx_sub = skill_ctx.add_subparsers(dest="ctx_cmd")

    ctx_save = ctx_sub.add_parser("save", help="Save skill output context")
    ctx_save.add_argument("name", help="Skill name")
    ctx_save.add_argument("--data", required=True, help="JSON context data")

    ctx_load = ctx_sub.add_parser("load", help="Load skill context")
    ctx_load.add_argument("name", help="Skill name")

    ctx_sub.add_parser("current", help="Show current active skill")
    ctx_clear = ctx_sub.add_parser("clear", help="Clear skill context")
    ctx_clear.add_argument("--all", action="store_true", default=False, help="Clear all context, not just current")

    # skill check-deps [--skill name]
    check_deps = skill_sub.add_parser("check-deps", help="Check if skill dependencies are satisfied")
    check_deps.add_argument("--skill", default="", help="Skill to check")


def _add_go_command(sub):
    """Add the unified 'go' entry point."""
    go_p = sub.add_parser("go", help="One command — describe goal, everything runs automatically")
    go_p.add_argument("goal", nargs="*", help="What you want to achieve")
    go_p.add_argument("--mode", choices=["auto", "chain", "ralph"], default="",
                       help="Force execution mode")
    go_p.add_argument("--max", type=int, default=25, help="Max iterations (ralph mode)")
    go_p.add_argument("--dry-run", action="store_true", default=False,
                       help="Show plan without executing")
    go_p.add_argument("--resume", action="store_true", default=False,
                       help="Resume interrupted chain from last step")
    go_p.add_argument("--no-auto-exec", action="store_true", default=False,
                       help="Disable auto-exec: output instructions instead of running subprocess")


def _add_wf_commands(sub):
    """Add cc-wf-studio workflow commands."""
    wf_p = sub.add_parser("wf", help="cc-wf-studio workflow executor (run/list/export/show)")
    wf_sub = wf_p.add_subparsers(dest="wf_cmd")

    wf_run = wf_sub.add_parser("run", help="Execute a workflow JSON file")
    wf_run.add_argument("path", help="Workflow JSON path or name")
    wf_run.add_argument("--dry-run", action="store_true", default=False)

    wf_sub.add_parser("list", help="List available workflows")

    wf_show = wf_sub.add_parser("show", help="Show workflow details")
    wf_show.add_argument("path", help="Workflow JSON path or name")

    wf_export = wf_sub.add_parser("export", help="Export cc-code chain as workflow JSON")
    wf_export.add_argument("name", help="Chain name (or 'all')")


def _add_wisdom_commands(sub):
    """Add wisdom and exploration cache commands."""
    # Wisdom
    wis_p = sub.add_parser("wisdom", help="Persistent knowledge: learnings, decisions, conventions")
    wis_sub = wis_p.add_subparsers(dest="wisdom_cmd")
    wis_show = wis_sub.add_parser("show", help="Show wisdom entries")
    wis_show.add_argument("--category", choices=["all", "learnings", "decisions", "conventions"], default="all")
    wis_show.add_argument("--limit", type=int, default=20)
    wis_search = wis_sub.add_parser("search", help="Search wisdom by keyword")
    wis_search.add_argument("query", nargs="+")
    wis_add = wis_sub.add_parser("add", help="Add wisdom entry")
    wis_add.add_argument("category", choices=["learnings", "decisions", "conventions"])
    wis_add.add_argument("--content", required=True)
    wis_clear = wis_sub.add_parser("clear", help="Clear wisdom")
    wis_clear.add_argument("--category", choices=["all", "learnings", "decisions", "conventions"], default="all")

    # Exploration cache
    exp_p = sub.add_parser("explore", help="Exploration cache — prevent redundant research")
    exp_sub = exp_p.add_subparsers(dest="explore_cmd")
    exp_sub.add_parser("cache", help="Show cache stats")
    exp_lookup = exp_sub.add_parser("lookup", help="Look up cached exploration")
    exp_lookup.add_argument("query", nargs="+")
    exp_sub.add_parser("clear", help="Clear exploration cache")


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
    sub.add_parser("help", help="Show all commands grouped by category")
    config_p = sub.add_parser("config", help="View/set cc-flow configuration")
    config_p.add_argument("key", nargs="?", default="")
    config_p.add_argument("value", nargs="?", default="")
    clean_p = sub.add_parser("clean", help="Remove old sessions and archived data")
    clean_p.add_argument("--days", type=int, default=30, help="Max age in days (default: 30)")
    clean_p.add_argument("--dry-run", action="store_true", default=False, help="Preview without deleting")
    profile_p = sub.add_parser("profile", help="Apply a configuration profile")
    profile_p.add_argument("action", nargs="?", default="list", choices=["list", "apply"])
    profile_p.add_argument("name", nargs="?", default="")

    # Unified review (auto-selects best mode: adversarial > multi > agent)
    review_p = sub.add_parser("review", help="Code review — auto-selects best mode (3-engine debate / consensus / agent)")
    review_p.add_argument("--mode", default="", choices=["", "adversarial", "multi", "agent", "pua"],
                          help="Force review mode (default: auto → adversarial → PUA if disputed)")
    review_p.add_argument("--timeout", type=int, default=300, help="Per-engine timeout")
    review_p.add_argument("--range", default="", help="Git diff range: main..HEAD, HEAD~5")
    review_p.add_argument("--path", nargs="*", default=None, help="Limit to paths: scripts/ tests/")
    review_p.add_argument("--dry-run", action="store_true", help="Show plan without running")

    # Review backend setup
    review_setup_p = sub.add_parser("review-setup",
                                    help="Detect available review backends and configure")
    review_setup_p.add_argument("--set", default="",
                                help="Set default backend: agent, rp, codex, export, none")
    review_setup_p.add_argument("--scope", default="", choices=["", "plan", "impl", "completion"],
                                help="Set backend for specific review type only")

    # Multi-engine review
    mr_p = sub.add_parser("multi-review", help="Multi-engine code review with consensus (codex+gemini+rp+agent)")
    mr_p.add_argument("--engines", default="", help="Comma-separated engines: codex,gemini,rp,agent")
    mr_p.add_argument("--timeout", type=int, default=1000, help="Per-engine timeout in seconds")
    mr_p.add_argument("--range", default="", help="Git diff range: main..HEAD, HEAD~5, commit-sha")
    mr_p.add_argument("--path", nargs="*", default=None, help="Limit review to paths: scripts/ tests/")
    mr_p.add_argument("--dry-run", action="store_true", help="Show plan without running")

    # Autopilot (3-engine guided execution)
    ap_p = sub.add_parser("autopilot", help="3-engine guided autopilot: plan → execute → checkpoint → review")
    ap_p.add_argument("goal", nargs="*", help="Goal or subcommand (checkpoint/status)")
    ap_p.add_argument("--timeout", type=int, default=300)
    ap_p.add_argument("--dry-run", action="store_true")
    ap_p.add_argument("--progress", default="")
    ap_p.add_argument("--step", type=int, default=0)
    ap_p.add_argument("--total", type=int, default=0)

    # Multi-engine plan
    mp_p = sub.add_parser("multi-plan", help="3-engine plan: Claude designs → Codex critiques → Gemini synthesizes")
    mp_p.add_argument("goal", nargs="*", help="What to plan: 'build user authentication'")
    mp_p.add_argument("--timeout", type=int, default=300, help="Per-engine timeout")
    mp_p.add_argument("--dry-run", action="store_true", help="Show plan without running")

    # PUA engine (3-model mutual challenge)
    pua_p = sub.add_parser("pua", help="3-model PUA: engines mutually challenge until optimal")
    pua_p.add_argument("--mode", default="code", choices=["code", "plan", "review"], help="PUA mode")
    pua_p.add_argument("--rounds", type=int, default=3, help="Max PUA rounds")
    pua_p.add_argument("--timeout", type=int, default=300, help="Per-engine timeout")
    pua_p.add_argument("--range", default="", help="Git diff range")
    pua_p.add_argument("--dry-run", action="store_true")

    # Adversarial review
    ar_p = sub.add_parser("adversarial-review", help="3-engine debate: Claude × Codex × Gemini review with battle")
    ar_p.add_argument("--engines", default="", help="Engines: claude,codex,gemini (default: all available)")
    ar_p.add_argument("--timeout", type=int, default=300, help="Per-round timeout in seconds")
    ar_p.add_argument("--range", default="", help="Git diff range: main..HEAD, HEAD~5")
    ar_p.add_argument("--path", nargs="*", default=None, help="Limit to paths: scripts/ tests/")
    ar_p.add_argument("--dry-run", action="store_true", help="Show plan without running")

    # Safety modes
    careful_p = sub.add_parser("careful", help="Toggle careful mode (warn on destructive ops)")
    careful_g = careful_p.add_mutually_exclusive_group()
    careful_g.add_argument("--enable", action="store_true", default=False, help="Enable careful mode")
    careful_g.add_argument("--disable", action="store_true", default=False, help="Disable careful mode")

    freeze_p = sub.add_parser("freeze", help="Freeze edits to a specific directory only")
    freeze_p.add_argument("directory", nargs="?", default="", help="Directory to restrict edits to")
    freeze_p.add_argument("--disable", action="store_true", default=False, help="Disable freeze mode")

    guard_p = sub.add_parser("guard", help="Maximum safety mode (careful + freeze combined)")
    guard_g = guard_p.add_mutually_exclusive_group()
    guard_g.add_argument("--enable", action="store_true", default=False, help="Enable guard mode")
    guard_g.add_argument("--disable", action="store_true", default=False, help="Disable guard mode")
    guard_p.add_argument("directory", nargs="?", default="", help="Directory to restrict edits to (default: cwd)")

    # Cross-worktree state commands
    sub.add_parser("state-path", help="Show shared state directory (for worktree debugging)")
    migrate_state_p = sub.add_parser("migrate-state",
                                     help="Move runtime state to shared dir for cross-worktree safety")
    migrate_state_p.add_argument("--clean", action="store_true", default=False,
                                 help="Remove runtime fields from .tasks/ JSON after migration")


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
  RepoPrompt: rp check/windows/workspace/tabs/select/builder/chat/
              read/search/tree/structure/context/prompt/chats/models/
              git/edit/file/setup-review/session/worktree-setup/run
  Go:         go "your goal" (auto-route to chain/ralph/auto)
  Skill Flow: skill next/graph/graph-build/ctx save/load/current/clear
  Chains:     chain list/show/suggest/run/advance
  Safety:     careful, freeze, guard
  Checkpoint: checkpoint create/verify/compare/list
  Analysis:   context-budget
  Config:     config, clean, version
  Worktree:   state-path, migrate-state
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
    _add_worktree_commands(sub)
    _add_bridge_commands(sub)
    _add_eval_commands(sub)
    _add_rp_commands(sub)
    _add_checkpoint_commands(sub)
    _add_skill_flow_commands(sub)
    _add_go_command(sub)
    _add_wf_commands(sub)
    _add_wisdom_commands(sub)
    _add_misc_commands(sub)

    # Let plugins register their own commands
    try:
        from cc_flow.plugins import register_plugin_commands
        register_plugin_commands(sub)
    except ImportError:
        pass

    return parser
