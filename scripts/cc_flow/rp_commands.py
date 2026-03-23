"""CLI commands for cc-flow rp — RepoPrompt integration."""

import json
import sys

from cc_flow import rp


def cmd_rp(args):
    """Dispatch rp subcommands."""
    sub = getattr(args, "rp_cmd", None)
    if not sub:
        print("Usage: cc-flow rp <command>")
        print("")
        print("Explore:   check, windows, workspace, tabs, tree, structure, search, read")
        print("Context:   select, builder, context, prompt, models")
        print("Chat:      chat, plan, review, chats")
        print("Edit:      edit, file")
        print("Git:       git, worktree-status, worktree-diff")
        print("Setup:     setup-review, session, worktree-setup, worktree-cleanup")
        print("Raw:       run")
        sys.exit(1)

    handlers = {
        "check": _cmd_check,
        "windows": _cmd_windows,
        "workspace": _cmd_workspace,
        "tabs": _cmd_tabs,
        "select": _cmd_select,
        "builder": _cmd_builder,
        "plan": _cmd_plan,
        "review": _cmd_review,
        "chat": _cmd_chat,
        "read": _cmd_read,
        "search": _cmd_search,
        "tree": _cmd_tree,
        "structure": _cmd_structure,
        "context": _cmd_context,
        "prompt": _cmd_prompt,
        "chats": _cmd_chats,
        "models": _cmd_models,
        "git": _cmd_git,
        "edit": _cmd_edit,
        "file": _cmd_file,
        "setup-review": _cmd_setup_review,
        "session": _cmd_session,
        "worktree-setup": _cmd_worktree_setup,
        "worktree-cleanup": _cmd_worktree_cleanup,
        "worktree-status": _cmd_worktree_status,
        "worktree-diff": _cmd_worktree_diff,
        "run": _cmd_run,
    }

    handler = handlers.get(sub)
    if handler:
        handler(args)
    else:
        print(json.dumps({"success": False, "error": f"Unknown rp command: {sub}"}))
        sys.exit(1)


def _wt(args):
    """Extract window/tab from args or session."""
    w = getattr(args, "window", None)
    t = getattr(args, "tab", None)
    if w is None or t is None:
        sw, st = rp.get_window_tab()
        if w is None:
            w = sw
        if t is None:
            t = st
    return w, t


def _run_safe(fn, *a, **kw):
    """Run an rp function with error handling."""
    try:
        result = fn(*a, **kw)
        if isinstance(result, str):
            print(result, end="" if result.endswith("\n") else "\n")
        elif isinstance(result, dict):
            print(json.dumps(result, indent=2))
        else:
            print(result)
    except RuntimeError as e:
        print(json.dumps({"success": False, "error": str(e)}))
        sys.exit(1)


# --- Individual commands ---

def _cmd_check(args):
    """Check available RP transports."""
    transports = rp.available_transports()
    cli_path = rp.find_rp_cli()
    version = rp.rp_version()
    result = {
        "success": transports["active"] != "none",
        "transports": {
            "cli": {
                "available": transports["cli"],
                "path": cli_path or "(not found)",
                "version": version or "(unknown)",
            },
            "mcp": {"available": transports["mcp"]},
        },
        "active_transport": transports["active"],
        "mcp_tools": list(rp.MCP_TOOLS.values()) if transports["mcp"] else [],
    }
    if not result["success"]:
        result["setup"] = "Install from RepoPrompt: Settings -> MCP Server -> Install CLI to PATH"
    print(json.dumps(result, indent=2))


def _cmd_windows(args):
    _run_safe(rp.windows, raw_json=getattr(args, "json", False))


def _cmd_workspace(args):
    w, _ = _wt(args)
    action = getattr(args, "action", "list")
    name = getattr(args, "name", "")

    if action == "list":
        _run_safe(rp.workspace_list, window=w)
    elif action == "switch":
        new_win = getattr(args, "new_window", False)
        _run_safe(rp.workspace_switch, name, window=w, new_window=new_win)
    elif action == "create":
        folder = getattr(args, "folder_path", "")
        new_win = getattr(args, "new_window", False)
        _run_safe(rp.workspace_create, name, window=w, folder_path=folder or None, new_window=new_win)
    elif action == "delete":
        close = getattr(args, "close_window", False)
        _run_safe(rp.workspace_delete, name, window=w, close_window=close)
    elif action == "tabs":
        _run_safe(rp.workspace_tabs, window=w)


def _cmd_tabs(args):
    w, _ = _wt(args)
    action = getattr(args, "action", "list")
    name = getattr(args, "name", "")

    if action == "list":
        _run_safe(rp.workspace_tabs, window=w)
    elif action == "create":
        _run_safe(rp.tab_create, name, window=w)
    elif action == "close":
        allow = getattr(args, "allow_active", False)
        _run_safe(rp.tab_close, name, window=w, allow_active=allow)


def _cmd_select(args):
    w, t = _wt(args)
    op = getattr(args, "op", "get")
    paths = getattr(args, "paths", [])

    if op == "get":
        _run_safe(rp.select_get, window=w, tab=t)
    elif op == "set":
        _run_safe(rp.select_set, paths, window=w, tab=t)
    elif op == "add":
        _run_safe(rp.select_add, paths, window=w, tab=t)
    elif op == "remove":
        _run_safe(rp.select_remove, paths, window=w, tab=t)
    elif op == "clear":
        _run_safe(rp.select_clear, window=w, tab=t)


def _cmd_builder(args):
    w, t = _wt(args)
    instructions = getattr(args, "instructions", "")
    response_type = getattr(args, "type", None)
    _run_safe(
        rp.builder, instructions,
        response_type=response_type, window=w, tab=t,
        raw_json=bool(response_type),
    )


def _cmd_plan(args):
    """Send a plan request (new chat in plan mode)."""
    w, t = _wt(args)
    message = getattr(args, "message", "")
    _run_safe(rp.plan, message, window=w, tab=t)


def _cmd_review(args):
    """Send a review request (new chat in review mode)."""
    w, t = _wt(args)
    message = getattr(args, "message", "")
    _run_safe(rp.review, message, window=w, tab=t)


def _cmd_chat(args):
    w, t = _wt(args)
    message = getattr(args, "message", "")
    message_file = getattr(args, "message_file", "")
    new = getattr(args, "new", False)
    chat_name = getattr(args, "chat_name", "")

    if message_file:
        _run_safe(
            rp.chat_send_file, message_file,
            new_chat=new, chat_name=chat_name or None,
            window=w, tab=t,
        )
    else:
        _run_safe(rp.chat, message, new_chat=new, window=w, tab=t)


def _cmd_read(args):
    w, t = _wt(args)
    path = getattr(args, "path", "")
    start = getattr(args, "start_line", None)
    limit = getattr(args, "limit_n", None)
    _run_safe(rp.read_file, path, start_line=start, limit=limit, window=w, tab=t)


def _cmd_search(args):
    w, t = _wt(args)
    pattern = getattr(args, "pattern", "")
    ext = getattr(args, "extensions", "")
    extensions = ext.split(",") if ext else None
    ctx = getattr(args, "context_lines", None)
    _run_safe(rp.search, pattern, extensions=extensions, context_lines=ctx, window=w, tab=t)


def _cmd_tree(args):
    w, t = _wt(args)
    mode = getattr(args, "mode", None)
    depth = getattr(args, "max_depth", None)
    path = getattr(args, "path", "")
    _run_safe(rp.tree, mode=mode, max_depth=depth, path=path or None, window=w, tab=t)


def _cmd_structure(args):
    w, t = _wt(args)
    paths = getattr(args, "paths", [])
    _run_safe(rp.structure, paths, window=w, tab=t)


def _cmd_context(args):
    w, t = _wt(args)
    all_flag = getattr(args, "all", False)
    _run_safe(rp.context, include_all=all_flag, window=w, tab=t)


def _cmd_prompt(args):
    w, t = _wt(args)
    op = getattr(args, "op", "get")
    if op == "get":
        _run_safe(rp.prompt_get, window=w, tab=t)
    elif op == "set":
        text = getattr(args, "text", "")
        _run_safe(rp.prompt_set, text, window=w, tab=t)
    elif op == "export":
        path = getattr(args, "export_path", "")
        _run_safe(rp.prompt_export, path, window=w, tab=t)


def _cmd_chats(args):
    w, t = _wt(args)
    action = getattr(args, "action", "list")
    scope = getattr(args, "scope", "workspace")
    limit = getattr(args, "limit_n", None)
    if action == "list":
        _run_safe(rp.chats_list, scope=scope, limit=limit, window=w, tab=t)
    elif action == "log":
        chat_id = getattr(args, "chat_id", "")
        _run_safe(rp.chats_log, scope=scope, chat_id=chat_id or None, limit=limit, window=w, tab=t)


def _cmd_models(args):
    w, _ = _wt(args)
    _run_safe(rp.models, window=w)


def _cmd_git(args):
    w, t = _wt(args)
    op = getattr(args, "op", "status")
    _run_safe(
        rp.git, op,
        compare=getattr(args, "compare", None),
        detail=getattr(args, "detail", None),
        count=getattr(args, "count", None),
        artifacts=getattr(args, "artifacts", False),
        window=w, tab=t,
    )


def _cmd_edit(args):
    w, t = _wt(args)
    path = getattr(args, "path", "")
    s = getattr(args, "search_text", "")
    r = getattr(args, "replace_text", "")
    _run_safe(rp.apply_edits, path, search=s, replace=r, window=w, tab=t)


def _cmd_file(args):
    w, t = _wt(args)
    action = getattr(args, "action", "")
    path = getattr(args, "path", "")
    content = getattr(args, "content", None)
    new_path = getattr(args, "new_path", None)
    _run_safe(rp.file_actions, action, path, content=content, new_path=new_path, window=w, tab=t)


def _cmd_setup_review(args):
    summary = getattr(args, "summary", "Review recent changes")
    root = getattr(args, "repo_root", None)
    response_type = getattr(args, "type", None)
    try:
        result = rp.setup_review(summary, root=root, response_type=response_type)
        print(json.dumps({"success": True, **result}, indent=2))
    except RuntimeError as e:
        print(json.dumps({"success": False, "error": str(e)}))
        sys.exit(1)


def _cmd_session(args):
    action = getattr(args, "action", "show")
    if action == "show":
        s = rp.load_session()
        print(json.dumps({"success": True, "session": s}, indent=2))
    elif action == "clear":
        rp.save_session({})
        print(json.dumps({"success": True, "message": "Session cleared"}))


def _cmd_worktree_setup(args):
    wt_path = getattr(args, "worktree_path", "")
    w, _ = _wt(args)
    try:
        result = rp.setup_worktree_workspace(wt_path, window=w)
        print(json.dumps({"success": True, **result}, indent=2))
    except RuntimeError as e:
        print(json.dumps({"success": False, "error": str(e)}))
        sys.exit(1)


def _cmd_worktree_cleanup(args):
    wt_path = getattr(args, "worktree_path", "")
    w, _ = _wt(args)
    rp.cleanup_worktree_workspace(wt_path, window=w)
    print(json.dumps({"success": True, "message": f"Cleaned up workspace for {wt_path}"}))


def _cmd_worktree_status(args):
    """Get git status for a worktree by branch name (no workspace switch)."""
    w, t = _wt(args)
    branch = getattr(args, "branch", "")
    _run_safe(rp.worktree_git_status, branch, window=w, tab=t)


def _cmd_worktree_diff(args):
    """Get diff for a worktree branch vs trunk."""
    w, t = _wt(args)
    branch = getattr(args, "branch", "")
    compare = getattr(args, "compare", "main")
    detail = getattr(args, "detail", "files")
    _run_safe(rp.worktree_diff, branch, compare=compare, detail=detail, window=w, tab=t)


def _cmd_run(args):
    """Raw rp-cli passthrough — run any rp-cli -e command."""
    w, t = _wt(args)
    command = getattr(args, "command", "")
    _run_safe(rp.exec_cmd, command, window=w, tab=t)
