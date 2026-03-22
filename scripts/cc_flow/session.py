"""Session save/restore for cc-flow."""

import json
import subprocess as _sp
from datetime import datetime, timezone

from cc_flow.core import (
    LEARNINGS_DIR,
    SESSION_DIR,
    all_tasks,
    error,
    now_iso,
    safe_json_load,
)


def cmd_session(args):
    """Save or restore session state."""
    mode = getattr(args, "session_cmd", None)
    SESSION_DIR.mkdir(parents=True, exist_ok=True)

    if mode == "save":
        _session_save(args)
    elif mode == "restore":
        _session_restore(args)
    elif mode == "list":
        _session_list()
    else:
        error("Usage: cc-flow session [save|restore|list]")


def _session_save(args):
    """Save comprehensive session state."""
    tasks = all_tasks()
    in_prog = [t for t in tasks.values() if t["status"] == "in_progress"]
    done_count = sum(1 for t in tasks.values() if t["status"] == "done")
    learn_count = len(list(LEARNINGS_DIR.glob("*.json"))) if LEARNINGS_DIR.exists() else 0

    git_sha, git_branch, git_dirty = _git_state()

    recent_learnings = []
    if LEARNINGS_DIR.exists():
        for f in sorted(LEARNINGS_DIR.glob("*.json"))[-3:]:
            d = safe_json_load(f, default=None)
            if d:
                recent_learnings.append({"task": d.get("task", ""), "lesson": d.get("lesson", "")})

    name = getattr(args, "name", "") or datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    session = {
        "name": name,
        "timestamp": now_iso(),
        "git_sha": git_sha,
        "git_branch": git_branch,
        "git_dirty": bool(git_dirty),
        "tasks_total": len(tasks),
        "tasks_done": done_count,
        "in_progress": [{"id": t["id"], "title": t.get("title", "")} for t in in_prog],
        "learnings_count": learn_count,
        "recent_learnings": recent_learnings,
        "notes": getattr(args, "notes", "") or "",
    }

    path = SESSION_DIR / f"{name}.json"
    path.write_text(json.dumps(session, indent=2) + "\n")
    print(json.dumps({"success": True, "session": name, "path": str(path)}))


def _session_restore(args):
    """Restore and display session state."""
    name = getattr(args, "name", "latest")
    if name == "latest":
        files = sorted(SESSION_DIR.glob("*.json"))
        if not files:
            error("No sessions found")
        path = files[-1]
    else:
        path = SESSION_DIR / f"{name}.json"

    if not path.exists():
        error(f"Session not found: {name}")

    data = safe_json_load(path)
    print(f"## Session: {data.get('name', '?')}")
    print(f"Saved: {data.get('timestamp', '?')}")
    print(f"Branch: {data.get('git_branch', '?')} @ {data.get('git_sha', '?')[:8]}")
    if data.get("git_dirty"):
        print("WARNING: Had uncommitted changes when saved")
    print(f"Progress: {data.get('tasks_done', 0)}/{data.get('tasks_total', 0)} tasks done")

    if data.get("in_progress"):
        print("\n### Resume These Tasks:")
        for t in data["in_progress"]:
            print(f"  - cc-flow start {t['id']} — {t['title']}")
    if data.get("recent_learnings"):
        print("\n### Recent Learnings:")
        for entry in data["recent_learnings"]:
            print(f"  - {entry['task']}: {entry['lesson']}")
    if data.get("notes"):
        print(f"\n### Notes:\n{data['notes']}")
    print("\n### Next Steps:")
    print("  1. `cc-flow dashboard` — see current state")
    print("  2. `cc-flow next` — pick next task")


def _session_list():
    """List all saved sessions."""
    sessions = []
    for f in sorted(SESSION_DIR.glob("*.json")):
        d = safe_json_load(f, default=None)
        if d:
            sessions.append({
                "name": d.get("name", f.stem),
                "timestamp": d.get("timestamp", ""),
                "done": d.get("tasks_done", 0),
                "total": d.get("tasks_total", 0),
                "branch": d.get("git_branch", ""),
            })
    print(json.dumps({"success": True, "sessions": sessions, "count": len(sessions)}))


def _git_state():
    """Get current git SHA, branch, and dirty status."""
    try:
        sha = _sp.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, timeout=5).stdout.strip()
        branch = _sp.run(["git", "branch", "--show-current"], capture_output=True, text=True, timeout=5).stdout.strip()
        dirty = _sp.run(["git", "status", "--porcelain"], capture_output=True, text=True, timeout=5).stdout.strip()
        return sha, branch, dirty
    except (OSError, _sp.TimeoutExpired):
        return "", "", ""
