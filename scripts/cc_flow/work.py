"""cc-flow work commands."""

import json
import sys
from datetime import datetime, timezone

from cc_flow.core import (
    CONFIG_FILE, DEFAULT_CONFIG, LEARNINGS_DIR, TASKS_SUBDIR, all_tasks, error, now_iso, safe_json_load, save_task,
)


def cmd_start(args):
    path = TASKS_SUBDIR / f"{args.id}.json"
    if not path.exists():
        print(json.dumps({"success": False, "error": f"Task not found: {args.id}"}))
        sys.exit(1)

    data = safe_json_load(path)
    if data["status"] not in ("todo", "blocked"):
        print(json.dumps({"success": False, "error": f"Cannot start task with status: {data['status']}"}))
        sys.exit(1)

    # Check dependencies
    tasks = all_tasks()
    for dep in data.get("depends_on", []):
        dep_task = tasks.get(dep)
        if dep_task and dep_task["status"] != "done":
            print(json.dumps({"success": False, "error": f"Dependency not done: {dep}"}))
            sys.exit(1)

    data["status"] = "in_progress"
    data["started"] = now_iso()

    # Record git SHA at start for diff tracking and rollback
    import subprocess as _sp
    try:
        sha = _sp.run(["git", "rev-parse", "HEAD"],
                       capture_output=True, text=True, timeout=5).stdout.strip()
        if sha:
            data["git_sha_start"] = sha
    except (OSError, _sp.TimeoutExpired):
        pass

    save_task(path, data)
    print(json.dumps({"success": True, "id": args.id, "status": "in_progress"}))


def cmd_done(args):
    path = TASKS_SUBDIR / f"{args.id}.json"
    if not path.exists():
        print(json.dumps({"success": False, "error": f"Task not found: {args.id}"}))
        sys.exit(1)

    data = safe_json_load(path)

    # Calculate duration if started
    duration_sec = None
    if data.get("started"):
        try:
            started = datetime.fromisoformat(data["started"].replace("Z", "+00:00"))
            now = datetime.now(timezone.utc)
            duration_sec = int((now - started).total_seconds())
        except (ValueError, TypeError):
            pass

    # Track git diff since task start
    diff_stats = _get_diff_stats(data.get("git_sha_start"))

    data["status"] = "done"
    data["completed"] = now_iso()
    if duration_sec is not None:
        data["duration_sec"] = duration_sec
    if args.summary:
        data["summary"] = args.summary
    if diff_stats:
        data["diff"] = diff_stats
    save_task(path, data)

    result = {"success": True, "id": args.id, "status": "done"}
    if duration_sec is not None:
        mins = duration_sec // 60
        result["duration"] = f"{mins}m" if mins > 0 else f"{duration_sec}s"
    if diff_stats:
        result["diff"] = diff_stats

    # Auto-consolidate learnings if config allows
    config = DEFAULT_CONFIG.copy()
    if CONFIG_FILE.exists():
        try:
            config.update(json.loads(CONFIG_FILE.read_text()))
        except json.JSONDecodeError:
            pass
    if config.get("auto_consolidate") and LEARNINGS_DIR.exists():
        learning_count = len(list(LEARNINGS_DIR.glob("*.json")))
        if learning_count >= 10:
            result["hint"] = "Run 'cc-flow consolidate' to promote patterns"

    print(json.dumps(result))


def cmd_block(args):
    path = TASKS_SUBDIR / f"{args.id}.json"
    if not path.exists():
        print(json.dumps({"success": False, "error": f"Task not found: {args.id}"}))
        sys.exit(1)

    data = safe_json_load(path)
    data["status"] = "blocked"
    data["blocked_reason"] = args.reason
    data["blocked_at"] = now_iso()
    save_task(path, data)
    print(json.dumps({"success": True, "id": args.id, "status": "blocked"}))


def _get_diff_stats(start_sha=None):
    """Get git diff stats since a commit SHA."""
    import subprocess as _sp
    if not start_sha:
        return None
    try:
        result = _sp.run(
            ["git", "diff", "--stat", start_sha, "HEAD"],
            capture_output=True, text=True, timeout=10,
        )
        if result.returncode != 0 or not result.stdout.strip():
            return None

        lines = result.stdout.strip().split("\n")
        # Last line: "N files changed, X insertions(+), Y deletions(-)"
        summary_line = lines[-1] if lines else ""
        files_changed = 0
        insertions = 0
        deletions = 0

        import re
        m = re.search(r"(\d+) files? changed", summary_line)
        if m:
            files_changed = int(m.group(1))
        m = re.search(r"(\d+) insertions?", summary_line)
        if m:
            insertions = int(m.group(1))
        m = re.search(r"(\d+) deletions?", summary_line)
        if m:
            deletions = int(m.group(1))

        return {
            "files_changed": files_changed,
            "insertions": insertions,
            "deletions": deletions,
            "total_lines": insertions + deletions,
        }
    except (OSError, _sp.TimeoutExpired):
        return None


def cmd_rollback(args):
    """Rollback a failed task to the git state when it was started."""
    import subprocess as _sp

    path = TASKS_SUBDIR / f"{args.id}.json"
    if not path.exists():
        error(f"Task not found: {args.id}")

    data = safe_json_load(path)
    start_sha = data.get("git_sha_start")

    if not start_sha:
        error(f"No git SHA recorded for {args.id}. Task was not started in a git repo.")

    if data["status"] not in ("in_progress", "blocked"):
        error(f"Cannot rollback task with status: {data['status']}")

    # Show what will be rolled back
    diff_stats = _get_diff_stats(start_sha)
    if diff_stats and diff_stats["total_lines"] == 0:
        print(json.dumps({"success": True, "id": args.id, "action": "no_changes",
                          "message": "No changes to rollback"}))
        return

    if not getattr(args, "confirm", False):
        result = {
            "success": True,
            "id": args.id,
            "action": "preview",
            "sha": start_sha[:8],
            "diff": diff_stats,
            "message": f"Will reset to {start_sha[:8]}. Run with --confirm to execute.",
        }
        print(json.dumps(result))
        return

    # Execute rollback
    try:
        _sp.run(["git", "reset", "--hard", start_sha],
                capture_output=True, text=True, timeout=30, check=True)
    except (_sp.CalledProcessError, _sp.TimeoutExpired, OSError) as exc:
        error(f"Rollback failed: {exc}")

    # Reset task to todo
    data["status"] = "todo"
    for field in ("started", "completed", "summary", "blocked_reason",
                  "blocked_at", "git_sha_start", "duration_sec", "diff"):
        data.pop(field, None)
    save_task(path, data)

    print(json.dumps({
        "success": True,
        "id": args.id,
        "action": "rolled_back",
        "sha": start_sha[:8],
        "diff": diff_stats,
    }))
