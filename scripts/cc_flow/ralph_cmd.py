"""cc-flow ralph — one-command autonomous execution."""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

from cc_flow.core import error


def _find_ralph_sh():
    """Find ralph.sh — project-local first, then plugin template."""
    # Project-local (already initialized)
    local = Path("scripts/ralph/ralph.sh")
    if local.is_file():
        return str(local)
    # Plugin template
    root = os.environ.get("CLAUDE_PLUGIN_ROOT", "")
    if root:
        tpl = Path(root) / "templates" / "ralph" / "ralph.sh"
        if tpl.is_file():
            return str(tpl)
    # Relative to this file
    tpl = Path(__file__).parent.parent.parent / "templates" / "ralph" / "ralph.sh"
    if tpl.is_file():
        return str(tpl)
    return None


def _init_ralph(goal=""):
    """Initialize scripts/ralph/ from template if not present."""
    dest = Path("scripts/ralph")
    if dest.exists():
        return dest

    root = os.environ.get("CLAUDE_PLUGIN_ROOT", "")
    src = Path(root) / "templates" / "ralph" if root else Path(__file__).parent.parent.parent / "templates" / "ralph"

    if not src.is_dir():
        error("Ralph template not found. Run from plugin directory.")

    dest.mkdir(parents=True, exist_ok=True)
    for f in ["ralph.sh", "config.env", "prompt_plan.md", "prompt_work.md", "prompt_completion.md"]:
        s = src / f
        d = dest / f
        if s.is_file() and not d.exists():
            shutil.copy2(s, d)

    # Copy hooks
    hooks_src = src / "hooks"
    hooks_dst = dest / "hooks"
    if hooks_src.is_dir():
        hooks_dst.mkdir(exist_ok=True)
        for f in hooks_src.iterdir():
            if f.is_file():
                shutil.copy2(f, hooks_dst / f.name)

    os.chmod(str(dest / "ralph.sh"), 0o755)
    return dest


def cmd_ralph(args):
    """Start Ralph autonomous execution."""
    goal = getattr(args, "goal", "") or ""
    max_iter = getattr(args, "max", 25)
    yolo = getattr(args, "yolo", True)
    watch = getattr(args, "watch", False)

    # Init if needed
    ralph_dir = _init_ralph(goal)
    ralph_sh = ralph_dir / "ralph.sh"

    if not ralph_sh.is_file():
        sh = _find_ralph_sh()
        if not sh:
            error("Ralph not found. Run: cc-flow ralph --init")
        ralph_sh = Path(sh)

    # Build env overrides
    env = os.environ.copy()
    env["MAX_ITERATIONS"] = str(max_iter)
    if yolo:
        env["YOLO"] = "1"
    if goal:
        env["GOAL"] = goal
        env["SELF_HEAL"] = "1"
        env["GOAL_VERIFY"] = "tests"

    # Build command
    cmd = ["bash", str(ralph_sh)]
    if watch:
        cmd.append("--watch")

    print(json.dumps({
        "starting": True,
        "mode": "goal-driven" if goal else "task-driven",
        "goal": goal or "(work through existing tasks)",
        "max_iterations": max_iter,
        "yolo": yolo,
        "ralph_sh": str(ralph_sh),
    }))

    # Run Ralph
    try:
        result = subprocess.run(cmd, check=False, env=env, cwd=os.getcwd())
        sys.exit(result.returncode)
    except KeyboardInterrupt:
        print("\nRalph interrupted.")
        sys.exit(130)
