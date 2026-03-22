"""cc-flow context — intelligent context management for Claude Code sessions.

Captures project state as a compact JSON snapshot. Useful for:
- Resuming work after session restart
- Sharing project context with teammates
- Feeding into Claude Code as session primer
"""

import json
import subprocess

from cc_flow.core import (
    LEARNINGS_DIR,
    TASKS_DIR,
    all_tasks,
    now_iso,
    safe_json_load,
)

CONTEXT_FILE = TASKS_DIR / "context.json"


def _git_info():
    """Get current git state."""
    try:
        sha = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            check=False, capture_output=True, text=True, timeout=5,
        ).stdout.strip()
        branch = subprocess.run(
            ["git", "branch", "--show-current"],
            check=False, capture_output=True, text=True, timeout=5,
        ).stdout.strip()
        # Recent commits
        log = subprocess.run(
            ["git", "log", "--oneline", "-5"],
            check=False, capture_output=True, text=True, timeout=5,
        ).stdout.strip().split("\n")
    except (subprocess.TimeoutExpired, OSError):
        return {"sha": "", "branch": "", "recent_commits": []}
    else:
        return {"sha": sha, "branch": branch, "recent_commits": log}


def cmd_context_save(args):
    """Save current project context as compact snapshot."""
    tasks = all_tasks()
    name = getattr(args, "name", "") or "default"

    # Build compact context
    in_progress = [
        {"id": t["id"], "title": t.get("title", ""), "started": t.get("started", "")}
        for t in tasks.values() if t["status"] == "in_progress"
    ]
    blocked = [
        {"id": t["id"], "title": t.get("title", ""), "reason": t.get("blocked_reason", "")}
        for t in tasks.values() if t["status"] == "blocked"
    ]
    recent_done = sorted(
        [t for t in tasks.values() if t["status"] == "done" and t.get("completed")],
        key=lambda t: t.get("completed", ""), reverse=True,
    )[:5]

    # Key learnings
    learnings = []
    if LEARNINGS_DIR.exists():
        for f in sorted(LEARNINGS_DIR.glob("*.json"))[-5:]:
            d = safe_json_load(f, default=None)
            if d:
                learnings.append({
                    "task": d.get("task", ""), "lesson": d.get("lesson", ""),
                    "score": d.get("score", 0),
                })

    context = {
        "name": name,
        "saved_at": now_iso(),
        "git": _git_info(),
        "tasks": {
            "total": len(tasks),
            "in_progress": in_progress,
            "blocked": blocked,
            "recent_done": [{"id": t["id"], "title": t.get("title", "")} for t in recent_done],
            "todo_count": sum(1 for t in tasks.values() if t["status"] == "todo"),
        },
        "learnings": learnings,
    }

    CONTEXT_FILE.parent.mkdir(parents=True, exist_ok=True)
    CONTEXT_FILE.write_text(json.dumps(context, indent=2) + "\n")

    print(json.dumps({"success": True, "name": name, "file": str(CONTEXT_FILE)}))


def cmd_context_show(_args):
    """Show saved context (or current state if none saved)."""
    if CONTEXT_FILE.exists():
        context = safe_json_load(CONTEXT_FILE, default={})
        print(json.dumps({"success": True, **context}))
    else:
        # Generate on-the-fly
        import argparse
        cmd_context_save(argparse.Namespace(name="auto"))
        context = safe_json_load(CONTEXT_FILE, default={})
        print(json.dumps({"success": True, **context}))


def cmd_context_brief(_args):
    """One-paragraph project brief for Claude Code session start."""
    tasks = all_tasks()
    total = len(tasks)
    done = sum(1 for t in tasks.values() if t["status"] == "done")
    active = [t for t in tasks.values() if t["status"] == "in_progress"]
    blocked = [t for t in tasks.values() if t["status"] == "blocked"]
    todo = total - done - len(active) - len(blocked)

    git = _git_info()
    parts = [f"Project on branch '{git['branch']}' ({git['sha']})."]
    parts.append(f"Tasks: {done}/{total} done, {len(active)} active, {len(blocked)} blocked, {todo} todo.")

    if active:
        parts.append(f"Currently working on: {active[0]['title']}.")
    if blocked:
        parts.append(f"Blocked: {blocked[0].get('title', '')} — {blocked[0].get('blocked_reason', '')}.")

    if git["recent_commits"]:
        parts.append(f"Last commit: {git['recent_commits'][0]}.")

    brief = " ".join(parts)
    print(json.dumps({"success": True, "brief": brief}))
