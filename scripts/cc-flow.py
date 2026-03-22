#!/usr/bin/env python3
"""cc-flow — task & workflow manager for cc-code plugin.

Version: see cc_flow/__init__.py

All command implementations live in the cc_flow/ package.
This file is the entry point that imports and dispatches.
"""

import sys
from pathlib import Path

# Ensure cc_flow package is importable
sys.path.insert(0, str(Path(__file__).parent))

from cc_flow.auto import cmd_auto  # noqa: E402
from cc_flow.cli import build_parser  # noqa: E402
from cc_flow.config import cmd_config, cmd_history, cmd_version  # noqa: E402
from cc_flow.doctor import cmd_doctor  # noqa: E402

# Import all command functions from domain modules
from cc_flow.epic_task import (  # noqa: E402
    cmd_dep_add,
    cmd_epic_close,
    cmd_epic_create,
    cmd_epic_import,
    cmd_epic_reset,
    cmd_init,
    cmd_task_create,
    cmd_task_reset,
    cmd_task_set_spec,
)
from cc_flow.graph import cmd_graph  # noqa: E402
from cc_flow.log_cmds import cmd_archive, cmd_log, cmd_stats, cmd_summary  # noqa: E402
from cc_flow.morph_cmds import cmd_apply, cmd_compact, cmd_embed, cmd_github_search, cmd_search  # noqa: E402
from cc_flow.quality import cmd_scan, cmd_validate  # noqa: E402
from cc_flow.route_learn import (  # noqa: E402
    cmd_consolidate,
    cmd_learn,
    cmd_learnings,
    cmd_route,
)
from cc_flow.session import cmd_session  # noqa: E402
from cc_flow.views import (  # noqa: E402
    cmd_dashboard,
    cmd_epics,
    cmd_list,
    cmd_next,
    cmd_progress,
    cmd_ready,
    cmd_show,
    cmd_status,
    cmd_tasks,
)
from cc_flow.work import cmd_block, cmd_done, cmd_rollback, cmd_start  # noqa: E402


def main():
    """Parse args and dispatch to command functions."""
    parser = build_parser()
    args = parser.parse_args()

    cmds = {
        "init": cmd_init, "list": cmd_list, "epics": cmd_epics, "tasks": cmd_tasks,
        "show": cmd_show, "ready": cmd_ready, "start": cmd_start, "done": cmd_done,
        "block": cmd_block, "progress": cmd_progress, "status": cmd_status,
        "version": cmd_version, "validate": cmd_validate, "next": cmd_next,
        "scan": cmd_scan, "route": cmd_route, "learn": cmd_learn,
        "learnings": cmd_learnings, "log": cmd_log, "summary": cmd_summary,
        "archive": cmd_archive, "stats": cmd_stats, "consolidate": cmd_consolidate,
        "history": cmd_history, "config": cmd_config, "graph": cmd_graph,
        "doctor": cmd_doctor, "dashboard": cmd_dashboard, "rollback": cmd_rollback,
        "apply": cmd_apply, "search": cmd_search, "embed": cmd_embed,
        "compact": cmd_compact, "github-search": cmd_github_search,
    }

    subcmd_map = {
        "epic": {"epic_cmd": {"create": cmd_epic_create, "close": cmd_epic_close,
                               "import": cmd_epic_import, "reset": cmd_epic_reset}},
        "task": {"task_cmd": {"create": cmd_task_create, "reset": cmd_task_reset,
                               "set-spec": cmd_task_set_spec}},
    }

    if args.command in subcmd_map:
        for attr, handlers in subcmd_map[args.command].items():
            sub = getattr(args, attr, None)
            if sub in handlers:
                handlers[sub](args)
            else:
                parser.print_help()
                sys.exit(1)
    elif args.command == "auto":
        cmd_auto(args)
    elif args.command == "session":
        cmd_session(args)
    elif args.command == "dep" and getattr(args, "dep_cmd", None) == "add":
        cmd_dep_add(args)
    elif args.command in cmds:
        cmds[args.command](args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
