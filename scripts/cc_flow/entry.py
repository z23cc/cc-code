"""cc-flow CLI entry point — lazy-loaded command dispatch.

Commands are mapped as 'module:function' strings and imported on demand.
This saves ~150ms startup time by avoiding importing all 18 modules upfront.
"""

import sys
from importlib import import_module

from cc_flow.cli import build_parser

# Lazy command registry: command name → "module:function"
# Only the module needed for the invoked command gets imported.
_COMMANDS = {
    # epic_task
    "init": "epic_task:cmd_init",
    # views
    "list": "views:cmd_list", "epics": "views:cmd_epics", "tasks": "views:cmd_tasks",
    "show": "views:cmd_show", "ready": "views:cmd_ready", "next": "views:cmd_next",
    "progress": "views:cmd_progress", "status": "views:cmd_status",
    "dashboard": "views:cmd_dashboard", "export": "views:cmd_export",
    "find": "views:cmd_find", "similar": "views:cmd_similar",
    "priority": "views:cmd_priority", "index": "views:cmd_index",
    "dedupe": "views:cmd_dedupe", "suggest": "views:cmd_suggest",
    # work
    "start": "work:cmd_start", "done": "work:cmd_done", "block": "work:cmd_block",
    "rollback": "work:cmd_rollback", "reopen": "work:cmd_reopen",
    "diff": "work:cmd_diff", "bulk": "work:cmd_bulk",
    # quality
    "validate": "quality:cmd_validate", "scan": "quality:cmd_scan",
    "verify": "quality:cmd_verify",
    # config
    "version": "config:cmd_version", "history": "config:cmd_history",
    "config": "config:cmd_config", "clean": "config:cmd_clean",
    # doctor
    "doctor": "doctor:cmd_doctor",
    # graph
    "graph": "graph:cmd_graph", "critical-path": "graph:cmd_critical_path",
    # log_cmds
    "log": "log_cmds:cmd_log", "summary": "log_cmds:cmd_summary",
    "archive": "log_cmds:cmd_archive", "stats": "log_cmds:cmd_stats",
    "standup": "log_cmds:cmd_standup", "changelog": "log_cmds:cmd_changelog",
    "burndown": "log_cmds:cmd_burndown", "report": "log_cmds:cmd_report",
    "time": "log_cmds:cmd_time",
    # route_learn
    "route": "route_learn:cmd_route", "learn": "route_learn:cmd_learn",
    "learnings": "route_learn:cmd_learnings", "consolidate": "route_learn:cmd_consolidate",
    # morph_cmds
    "apply": "morph_cmds:cmd_apply", "search": "morph_cmds:cmd_search",
    "embed": "morph_cmds:cmd_embed", "compact": "morph_cmds:cmd_compact",
    "github-search": "morph_cmds:cmd_github_search",
    # perf + profile
    "perf": "perf:cmd_perf", "profile": "config:cmd_profile",
}

# Subcommands: parent → (attr, {subcmd: "module:function"})
_SUBCMD_MAP = {
    "epic": ("epic_cmd", {
        "create": "epic_task:cmd_epic_create", "close": "epic_task:cmd_epic_close",
        "import": "epic_task:cmd_epic_import", "reset": "epic_task:cmd_epic_reset",
    }),
    "task": ("task_cmd", {
        "create": "epic_task:cmd_task_create", "reset": "epic_task:cmd_task_reset",
        "set-spec": "epic_task:cmd_task_set_spec", "update": "epic_task:cmd_task_update",
        "comment": "epic_task:cmd_task_comment",
    }),
    "dep": ("dep_cmd", {
        "add": "epic_task:cmd_dep_add", "show": "epic_task:cmd_dep_show",
    }),
    "template": ("template_cmd", {
        "list": "epic_task:cmd_template_list", "show": "epic_task:cmd_template_show",
        "create": "epic_task:cmd_template_create",
    }),
    "workflow": ("workflow_cmd", {
        "list": "workflow:cmd_workflow_list", "show": "workflow:cmd_workflow_show",
        "run": "workflow:cmd_workflow_run", "create": "workflow:cmd_workflow_create",
    }),
    "plugin": ("plugin_cmd", {
        "list": "plugins:cmd_plugin_list", "enable": "plugins:cmd_plugin_enable",
        "disable": "plugins:cmd_plugin_disable", "create": "plugins:cmd_plugin_create",
    }),
}

# Special dispatchers (these modules handle their own subcommand parsing)
_SPECIAL = {
    "auto": "auto:cmd_auto",
    "session": "session:cmd_session",
}


def _resolve(ref):
    """Import a 'module:function' reference and return the callable."""
    module_name, func_name = ref.split(":")
    mod = import_module(f"cc_flow.{module_name}")
    return getattr(mod, func_name)


def _run_with_perf(cmd, handler, args):
    """Run a command handler with optional performance tracking."""
    try:
        from cc_flow.perf import PerfTimer
        with PerfTimer(cmd):
            handler(args)
    except ImportError:
        handler(args)


def main():
    """Parse args and dispatch to the appropriate command handler."""
    parser = build_parser()
    args = parser.parse_args()

    cmd = args.command

    # Special dispatchers (handle own subcommands)
    if cmd in _SPECIAL:
        _run_with_perf(cmd, _resolve(_SPECIAL[cmd]), args)
    # Subcommand groups (epic/task/dep/template)
    elif cmd in _SUBCMD_MAP:
        attr, handlers = _SUBCMD_MAP[cmd]
        sub = getattr(args, attr, None)
        if sub in handlers:
            _run_with_perf(f"{cmd}.{sub}", _resolve(handlers[sub]), args)
        else:
            parser.print_help()
            sys.exit(1)
    # Direct commands
    elif cmd in _COMMANDS:
        _run_with_perf(cmd, _resolve(_COMMANDS[cmd]), args)
    else:
        # Try plugin commands before giving up
        try:
            from cc_flow.plugins import dispatch_plugin_command
            if dispatch_plugin_command(cmd, args):
                return
        except ImportError:
            pass
        parser.print_help()
        sys.exit(1)
