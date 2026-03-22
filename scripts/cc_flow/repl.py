"""cc-flow REPL — interactive shell mode.

Enter by running `cc-flow` with no arguments.
Maintains session state across commands.
"""

from cc_flow import skin


def _repl_help():
    """Show curated REPL help."""
    skin.heading("Quick Commands")
    commands = [
        ("dashboard", "One-screen project overview"),
        ("status", "Task counts (JSON)"),
        ("next", "What to work on next"),
        ("standup", "Daily standup report"),
        ("verify", "Run lint + tests"),
        ("health", "Project health score"),
        ("find <query>", "Search tasks"),
        ("search <query>", "Search code (Morph/grep)"),
        ("route <task>", "Smart command routing"),
    ]
    skin.table(["Command", "Description"], commands)
    print()
    skin.dim("Type any cc-flow subcommand, or 'quit' to exit.")
    print()


def _show_context():
    """Show brief task context on REPL start."""
    try:
        from cc_flow.core import all_tasks
        tasks = all_tasks()
        total = len(tasks)
        done = sum(1 for t in tasks.values() if t["status"] == "done")
        active = sum(1 for t in tasks.values() if t["status"] == "in_progress")
        if total > 0:
            skin.info(f"Tasks: {done}/{total} done, {active} active")
        else:
            skin.dim("No tasks yet. Try: epic create --title 'My Project'")
    except (ImportError, OSError):
        pass
    print()


_COMPLETIONS = [
    # Top-level
    "dashboard", "status", "doctor", "verify", "health", "version",
    "init", "list", "epics", "tasks", "show", "ready", "next", "progress",
    "start", "done", "block", "reopen", "rollback", "diff", "bulk",
    "find", "search", "similar", "suggest", "dedupe", "index", "priority",
    "route", "learn", "learnings", "consolidate",
    "standup", "stats", "changelog", "burndown", "report", "time", "forecast",
    "scan", "validate", "export", "clean", "perf", "health", "evolve",
    # Subcommands
    "epic create", "epic close", "epic import", "epic reset",
    "task create", "task update", "task comment", "task reset",
    "dep add", "dep show",
    "auto scan", "auto run", "auto deep", "auto full", "auto status",
    "session save", "session restore", "session list",
    "workflow list", "workflow run", "workflow show", "workflow create",
    "template list", "template show", "template create",
    "plugin list", "plugin create", "plugin enable", "plugin disable",
    "context save", "context show", "context brief",
    "alias set", "alias list", "alias remove",
    "eval run", "eval detail", "eval cross", "eval history",
    "gh import", "gh export", "gh status",
    "profile list", "profile apply",
    # Flags
    "--json", "--epic", "--fix", "--dry-run", "--semantic",
    # REPL
    "help", "quit",
]


def _create_input_fn():
    """Create input function with tab completion + history."""
    try:
        from prompt_toolkit import PromptSession
        from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
        from prompt_toolkit.completion import WordCompleter
        from prompt_toolkit.history import InMemoryHistory

        completer = WordCompleter(_COMPLETIONS, ignore_case=True, sentence=True)
        session = PromptSession(
            history=InMemoryHistory(),
            auto_suggest=AutoSuggestFromHistory(),
            completer=completer,
        )

        def get_input():
            return session.prompt("cc-flow> ").strip()

    except ImportError:
        def get_input_basic():
            return input("cc-flow> ").strip()

        return get_input_basic
    else:
        return get_input


def _dispatch(cmd, args):
    """Dispatch a single command."""
    from cc_flow.entry import _COMMANDS, _SPECIAL, _SUBCMD_MAP, _resolve, _run_with_perf

    if cmd in _SPECIAL:
        _run_with_perf(cmd, _resolve(_SPECIAL[cmd]), args)
    elif cmd in _SUBCMD_MAP:
        attr, handlers = _SUBCMD_MAP[cmd]
        sub = getattr(args, attr, None)
        if sub in handlers:
            _run_with_perf(f"{cmd}.{sub}", _resolve(handlers[sub]), args)
        else:
            skin.warning(f"Missing subcommand for '{cmd}'. Try: {cmd} --help")
    elif cmd in _COMMANDS:
        _run_with_perf(cmd, _resolve(_COMMANDS[cmd]), args)
    else:
        try:
            from cc_flow.plugins import dispatch_plugin_command
            if not dispatch_plugin_command(cmd, args):
                skin.error(f"Unknown command: {cmd}")
        except ImportError:
            skin.error(f"Unknown command: {cmd}")


def run_repl():
    """Start interactive REPL session."""
    skin.banner()
    _show_context()
    get_input = _create_input_fn()

    while True:
        try:
            line = get_input()
            if not line:
                continue
            if line.lower() in ("quit", "exit", "q"):
                skin.goodbye()
                break
            if line.lower() in ("help", "?"):
                _repl_help()
                continue

            from cc_flow.cli import build_parser
            parser = build_parser()
            try:
                args = parser.parse_args(line.split())
            except SystemExit:
                continue

            cmd = args.command
            if not cmd:
                _repl_help()
                continue

            _dispatch(cmd, args)

        except (EOFError, KeyboardInterrupt):
            print()
            skin.goodbye()
            break
        except SystemExit:
            pass
