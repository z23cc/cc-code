"""cc-flow CLI entry point — parse args and dispatch to command functions."""

import sys

from cc_flow.auto import cmd_auto
from cc_flow.cli import build_parser
from cc_flow.config import cmd_clean, cmd_config, cmd_history, cmd_version
from cc_flow.doctor import cmd_doctor
from cc_flow.epic_task import (
    cmd_dep_add,
    cmd_dep_show,
    cmd_epic_close,
    cmd_epic_create,
    cmd_epic_import,
    cmd_epic_reset,
    cmd_init,
    cmd_task_comment,
    cmd_task_create,
    cmd_task_reset,
    cmd_task_set_spec,
    cmd_task_update,
    cmd_template_create,
    cmd_template_list,
    cmd_template_show,
)
from cc_flow.graph import cmd_critical_path, cmd_graph
from cc_flow.log_cmds import (
    cmd_archive,
    cmd_burndown,
    cmd_changelog,
    cmd_log,
    cmd_report,
    cmd_standup,
    cmd_stats,
    cmd_summary,
    cmd_time,
)
from cc_flow.morph_cmds import cmd_apply, cmd_compact, cmd_embed, cmd_github_search, cmd_search
from cc_flow.quality import cmd_scan, cmd_validate, cmd_verify
from cc_flow.route_learn import (
    cmd_consolidate,
    cmd_learn,
    cmd_learnings,
    cmd_route,
)
from cc_flow.session import cmd_session
from cc_flow.views import (
    cmd_dashboard,
    cmd_dedupe,
    cmd_epics,
    cmd_export,
    cmd_find,
    cmd_index,
    cmd_list,
    cmd_next,
    cmd_priority,
    cmd_progress,
    cmd_ready,
    cmd_show,
    cmd_similar,
    cmd_status,
    cmd_suggest,
    cmd_tasks,
)
from cc_flow.work import cmd_block, cmd_bulk, cmd_diff, cmd_done, cmd_reopen, cmd_rollback, cmd_start

_COMMANDS = {
    "init": cmd_init, "list": cmd_list, "epics": cmd_epics, "tasks": cmd_tasks,
    "show": cmd_show, "ready": cmd_ready, "start": cmd_start, "done": cmd_done,
    "block": cmd_block, "progress": cmd_progress, "status": cmd_status,
    "version": cmd_version, "validate": cmd_validate, "next": cmd_next,
    "scan": cmd_scan, "route": cmd_route, "learn": cmd_learn,
    "learnings": cmd_learnings, "log": cmd_log, "summary": cmd_summary,
    "standup": cmd_standup, "changelog": cmd_changelog, "priority": cmd_priority,
    "burndown": cmd_burndown, "report": cmd_report, "bulk": cmd_bulk, "time": cmd_time,
    "critical-path": cmd_critical_path,
    "archive": cmd_archive, "stats": cmd_stats, "consolidate": cmd_consolidate,
    "history": cmd_history, "config": cmd_config, "graph": cmd_graph,
    "verify": cmd_verify, "clean": cmd_clean, "export": cmd_export,
    "find": cmd_find, "similar": cmd_similar, "index": cmd_index,
    "dedupe": cmd_dedupe, "suggest": cmd_suggest,
    "reopen": cmd_reopen, "diff": cmd_diff,
    "doctor": cmd_doctor, "dashboard": cmd_dashboard, "rollback": cmd_rollback,
    "apply": cmd_apply, "search": cmd_search, "embed": cmd_embed,
    "compact": cmd_compact, "github-search": cmd_github_search,
}

_SUBCMD_MAP = {
    "epic": ("epic_cmd", {"create": cmd_epic_create, "close": cmd_epic_close,
                          "import": cmd_epic_import, "reset": cmd_epic_reset}),
    "task": ("task_cmd", {"create": cmd_task_create, "reset": cmd_task_reset,
                          "set-spec": cmd_task_set_spec, "update": cmd_task_update,
                          "comment": cmd_task_comment}),
    "dep": ("dep_cmd", {"add": cmd_dep_add, "show": cmd_dep_show}),
    "template": ("template_cmd", {"list": cmd_template_list, "show": cmd_template_show,
                                  "create": cmd_template_create}),
    "auto": ("auto_cmd", None),  # special: dispatched by cmd_auto
    "session": ("session_cmd", None),  # special: dispatched by cmd_session
}


def main():
    """Parse args and dispatch to command functions."""
    parser = build_parser()
    args = parser.parse_args()

    if args.command in ("auto",):
        cmd_auto(args)
    elif args.command in ("session",):
        cmd_session(args)
    elif args.command in _SUBCMD_MAP:
        attr, handlers = _SUBCMD_MAP[args.command]
        if handlers is None:
            parser.print_help()
            sys.exit(1)
        sub = getattr(args, attr, None)
        if sub in handlers:
            handlers[sub](args)
        else:
            parser.print_help()
            sys.exit(1)
    elif args.command in _COMMANDS:
        _COMMANDS[args.command](args)
    else:
        parser.print_help()
        sys.exit(1)
