"""cc-flow worktree — unified worktree management.

Wraps worktree.sh + state detection + task association + dashboard.
"""

import json
import os
import subprocess
from pathlib import Path

from cc_flow.core import error


def _worktree_sh():
    """Find worktree.sh."""
    root = os.environ.get("CLAUDE_PLUGIN_ROOT", "")
    if root:
        p = Path(root) / "scripts" / "worktree.sh"
        if p.is_file():
            return str(p)
    p = Path(__file__).parent.parent / "worktree.sh"
    if p.is_file():
        return str(p)
    return None


def _run_wt(cmd, *extra_args):
    """Run worktree.sh command."""
    sh = _worktree_sh()
    if not sh:
        error("worktree.sh not found")
    args = ["bash", sh, cmd, *list(extra_args)]
    result = subprocess.run(args, check=False, capture_output=True, text=True)
    if result.returncode != 0:
        return None, result.stderr.strip()
    return result.stdout.strip(), None


def _is_in_worktree():
    """Check if CWD is inside a git worktree."""
    try:
        git_dir = subprocess.run(
            ["git", "rev-parse", "--git-dir"],
            capture_output=True, text=True, check=True,
        ).stdout.strip()
        git_common = subprocess.run(
            ["git", "rev-parse", "--git-common-dir"],
            capture_output=True, text=True, check=True,
        ).stdout.strip()
        git_dir_real = str(Path(git_dir).resolve())
        git_common_real = str(Path(git_common).resolve())
        return git_dir_real != git_common_real
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def _current_worktree_info():
    """Get info about the current worktree (if in one)."""
    if not _is_in_worktree():
        return None
    try:
        branch = subprocess.run(
            ["git", "branch", "--show-current"],
            capture_output=True, text=True, check=True,
        ).stdout.strip()
        cwd = os.getcwd()
        main_repo = subprocess.run(
            ["git", "rev-parse", "--git-common-dir"],
            capture_output=True, text=True, check=True,
        ).stdout.strip()
        main_repo = str(Path(main_repo).resolve().parent)
        return {"branch": branch, "path": cwd, "main_repo": main_repo}
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def cmd_worktree(args):
    """Unified worktree command dispatcher."""
    sub = getattr(args, "wt_cmd", None)
    if not sub:
        # No subcommand — show current status
        _cmd_info(args)
        return

    handlers = {
        "create": _cmd_create,
        "list": _cmd_list,
        "switch": _cmd_switch,
        "remove": _cmd_remove,
        "cleanup": _cmd_cleanup,
        "status": _cmd_status,
        "info": _cmd_info,
    }
    handler = handlers.get(sub)
    if not handler:
        error(f"Unknown subcommand: {sub}. Available: {', '.join(handlers)}")
    handler(args)


def _cmd_create(args):
    """Create a new worktree."""
    name = getattr(args, "name", "")
    base = getattr(args, "base", "")
    if not name:
        error("Provide a worktree name")

    extra = [name]
    if base:
        extra.append(base)

    out, err = _run_wt("create", *extra)
    if err:
        error(err)

    path = out.split("created: ")[-1].strip() if "created:" in out else ""
    print(json.dumps({
        "success": True,
        "name": name,
        "path": path,
        "message": out,
        "hint": f"Open Claude Code here: cd {path} && claude",
    }))


def _cmd_list(args):
    """List all worktrees with status."""
    _out, _err = _run_wt("list")

    # Also get per-worktree dirty status
    _status_out, _ = _run_wt("status")

    worktrees = []
    try:
        result = subprocess.run(
            ["git", "worktree", "list", "--porcelain"],
            capture_output=True, text=True, check=True,
        )
        current_wt = {}
        for line in result.stdout.splitlines():
            if line.startswith("worktree "):
                if current_wt:
                    worktrees.append(current_wt)
                current_wt = {"path": line[9:]}
            elif line.startswith("HEAD "):
                current_wt["sha"] = line[5:8]
            elif line.startswith("branch "):
                current_wt["branch"] = line[7:].replace("refs/heads/", "")
            elif line == "bare":
                current_wt["bare"] = True
        if current_wt:
            worktrees.append(current_wt)
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass

    # Mark current
    cwd = os.getcwd()
    for wt in worktrees:
        wt["current"] = os.path.abspath(wt.get("path", "")) == os.path.abspath(cwd)
        wt["is_main"] = ".claude/worktrees" not in wt.get("path", "")

    print(json.dumps({
        "success": True,
        "worktrees": worktrees,
        "total": len(worktrees),
        "in_worktree": _is_in_worktree(),
    }))


def _cmd_switch(args):
    """Print worktree path (for cd)."""
    name = getattr(args, "name", "")
    if not name:
        error("Provide worktree name")

    out, err = _run_wt("switch", name)
    if err:
        error(err)

    print(json.dumps({
        "success": True,
        "path": out.strip(),
        "hint": f"cd {out.strip()} && claude",
    }))


def _cmd_remove(args):
    """Remove a worktree."""
    name = getattr(args, "name", "")
    if not name:
        error("Provide worktree name")

    out, err = _run_wt("remove", name)
    if err:
        error(err)

    print(json.dumps({"success": True, "message": out}))


def _cmd_cleanup(args):
    """Remove all managed worktrees."""
    out, err = _run_wt("cleanup")
    print(json.dumps({"success": True, "message": out or err or "done"}))


def _cmd_status(args):
    """Show dirty/clean status of all worktrees."""
    out, err = _run_wt("status")
    print(json.dumps({"success": True, "output": out or err or "no worktrees"}))


def _cmd_info(args):
    """Show current worktree context."""
    info = _current_worktree_info()
    if info:
        print(json.dumps({
            "success": True,
            "in_worktree": True,
            **info,
            "guard_active": True,
            "message": f"In worktree '{info['branch']}'. Edits scoped to {info['path']}.",
        }))
    else:
        print(json.dumps({
            "success": True,
            "in_worktree": False,
            "message": "In main checkout. Use 'cc-flow worktree create <name>' to create a worktree.",
        }))
