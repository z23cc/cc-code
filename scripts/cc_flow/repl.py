"""cc-flow REPL — interactive shell mode.

Enter by running `cc-flow` with no arguments.
Maintains session state across commands.
"""

from cc_flow import skin


def _repl_help():
    """Show curated REPL help — progressive disclosure."""
    skin.heading("One Command")
    go = [
        ("go \"describe goal\"", "Auto-route + execute (chain/ralph/auto)"),
        ("go \"fix bug\" --dry-run", "Preview plan without executing"),
    ]
    skin.table(["Command", "Description"], go)

    skin.heading("Start Here")
    start = [
        ("route <task>", "Don't know what to do? Describe your task"),
        ("dashboard", "One-screen project overview"),
        ("verify", "Run lint + tests (auto-detect language)"),
        ("health", "Project health score (0-100)"),
        ("next", "What to work on next"),
    ]
    skin.table(["Command", "Description"], start)

    skin.heading("Skill Chains (46 workflows)")
    chains = [
        ("chain run feature", "brainstorm → plan → tdd → review → commit"),
        ("chain run bugfix", "debug → tdd → review → commit"),
        ("chain run hotfix", "tdd → review → commit (fast-track)"),
        ("chain run idea-to-ship", "office-hours → brainstorm → plan → work → ship"),
        ("chain run deploy", "readiness → verify → deploy → ship"),
        ("chain run security-audit", "scout-security → security-review → commit"),
        ("chain suggest <task>", "Find best chain for your task"),
        ("chain list", "Show all 46 chains"),
    ]
    skin.table(["Command", "Steps"], chains)
    print()
    skin.dim("Type 'help all' for full command list, or 'quit' to exit.")
    print()


def _repl_help_all():
    """Show all commands grouped by category."""
    groups = [
        ("Automation",
         "go \"goal\", ralph, auto scan/run/deep/full"),
        ("Task Management",
         "init, epic, task, dep, list, show, ready, next, progress, dashboard"),
        ("Work Execution",
         "start, done, block, reopen, rollback, diff, bulk"),
        ("Quality",
         "verify, scan, validate, validate-skills, doctor, health"),
        ("Search & Route",
         "search, route, learn, learnings, consolidate, find, similar, suggest"),
        ("Skill Flow",
         "skill next/graph/ctx, chain list/show/suggest/run/advance/stats"),
        ("Wisdom & Learning",
         "wisdom show/search/add, explore cache/lookup"),
        ("Worktree",
         "worktree create/list/switch/remove/status/info"),
        ("Safety",
         "careful, freeze, guard, checkpoint create/verify/compare/list"),
        ("Bridge (Morph\u00d7RP\u00d7SM)",
         "deep-search, smart-chat, embed-structure, recall-review, bridge-status"),
        ("RepoPrompt",
         "rp check/builder/plan/review/chat/search/tree/structure/git/edit/..."),
        ("Workflows",
         "wf run/list/show/export, workflow list/run/show/create"),
        ("Analytics",
         "stats, standup, changelog, burndown, report, time, forecast"),
        ("Session",
         "session save/restore/list, context-budget"),
        ("Misc",
         "config, version, clean, graph, export, perf, help"),
    ]
    print()
    for title, cmds in groups:
        skin.heading(title)
        print(f"  {cmds}")
        print()
    skin.dim("Type a command to run it, or 'quit' to exit.")


def cmd_help(_args=None):
    """Print grouped help (usable from CLI: cc-flow help)."""
    _repl_help()
    _repl_help_all()


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
    "ralph", "scan", "validate", "validate-skills", "export", "clean", "perf", "health", "evolve",
    "deep-search", "smart-chat", "embed-structure", "recall-review", "bridge-status",
    "review-setup", "state-path",
    "careful", "freeze", "guard", "context-budget",
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
    "checkpoint create", "checkpoint verify", "checkpoint compare", "checkpoint list",
    "eval run", "eval detail", "eval cross", "eval history",
    "gh import", "gh export", "gh status",
    "profile list", "profile apply",
    "rp check", "rp builder", "rp plan", "rp review", "rp chat",
    "rp search", "rp tree", "rp structure", "rp read", "rp context",
    "rp select", "rp git", "rp edit", "rp prompt", "rp chats",
    "rp setup-review", "rp session", "rp worktree-status", "rp worktree-diff",
    "rp worktree-setup", "rp worktree-cleanup", "rp windows", "rp workspace",
    "worktree create", "worktree list", "worktree switch", "worktree remove",
    "worktree cleanup", "worktree status", "worktree info",
    "memory save", "memory search", "memory sync", "memory recall",
    "chain list", "chain show", "chain suggest", "chain run", "chain advance", "chain stats",
    "skill next", "skill graph", "skill graph-build", "skill check-deps",
    "skill ctx save", "skill ctx load", "skill ctx current", "skill ctx clear",
    "go", "go --dry-run", "go --mode=chain", "go --mode=ralph", "go --resume",
    "wisdom show", "wisdom search", "wisdom add", "wisdom clear",
    "explore cache", "explore lookup", "explore clear",
    "wf run", "wf list", "wf show", "wf export",
    # Flags
    "--json", "--epic", "--fix", "--dry-run", "--semantic",
    # REPL
    "help", "help all", "quit",
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
            """Read input with prompt_toolkit."""
            return session.prompt("cc-flow> ").strip()

    except ImportError:
        def get_input_basic():
            """Read input with basic input()."""
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
            if dispatch_plugin_command(cmd, args):
                return
        except ImportError:
            pass
        # Unknown command — suggest closest match
        all_cmds = list(_COMMANDS.keys()) + list(_SUBCMD_MAP.keys()) + list(_SPECIAL.keys())
        suggestion = skin.did_you_mean(cmd, all_cmds)
        if suggestion:
            skin.error(f"Unknown command: {cmd}. Did you mean: {suggestion}?")
        else:
            skin.error(f"Unknown command: {cmd}. Try: help")


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
            if line.lower() in ("help all", "commands"):
                _repl_help_all()
                continue
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
