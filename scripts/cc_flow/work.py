"""cc-flow work commands."""

import json
from datetime import datetime, timezone

from cc_flow.core import (
    CONFIG_FILE,
    DEFAULT_CONFIG,
    LEARNINGS_DIR,
    TASKS_SUBDIR,
    all_tasks,
    error,
    now_iso,
    safe_json_load,
    save_task,
)


def _fire_plugin_hook(hook_name, **kwargs):
    """Fire lifecycle hook on plugins, silently ignoring failures."""
    try:
        from cc_flow.plugins import fire_hook
        fire_hook(hook_name, **kwargs)
    except ImportError:
        pass


def cmd_start(args):
    """Start a task — check deps, record git SHA, set status to in_progress."""
    from cc_flow.core import resolve_task_id
    args.id = resolve_task_id(args.id)
    path = TASKS_SUBDIR / f"{args.id}.json"
    if not path.exists():
        error(f"Task not found: {args.id}")

    data = safe_json_load(path)
    if data["status"] not in ("todo", "blocked"):
        error(f"Cannot start task with status: {data['status']}")

    # Check dependencies
    tasks = all_tasks()
    for dep in data.get("depends_on", []):
        dep_task = tasks.get(dep)
        if dep_task and dep_task["status"] != "done":
            error(f"Dependency not done: {dep}")

    data["status"] = "in_progress"
    data["started"] = now_iso()

    # Record git SHA at start for diff tracking and rollback
    import subprocess as _sp
    try:
        sha = _sp.run(["git", "rev-parse", "HEAD"],
                       check=False, capture_output=True, text=True, timeout=5).stdout.strip()
        if sha:
            data["git_sha_start"] = sha
    except (OSError, _sp.TimeoutExpired):
        pass

    save_task(path, data)
    _fire_plugin_hook("on_task_start", task=data)
    print(json.dumps({"success": True, "id": args.id, "status": "in_progress"}))


def _calc_duration(started_iso):
    """Calculate seconds elapsed since an ISO timestamp. Returns None on failure."""
    if not started_iso:
        return None
    try:
        started = datetime.fromisoformat(started_iso.replace("Z", "+00:00"))
        return int((datetime.now(timezone.utc) - started).total_seconds())
    except (ValueError, TypeError):
        return None


def _format_duration(seconds):
    """Format seconds as a human-readable string."""
    mins = seconds // 60
    return f"{mins}m" if mins > 0 else f"{seconds}s"


def _consolidation_hint():
    """Return a consolidation hint if learnings need attention, else None."""
    config = DEFAULT_CONFIG.copy()
    if CONFIG_FILE.exists():
        try:
            config.update(json.loads(CONFIG_FILE.read_text()))
        except json.JSONDecodeError:
            pass
    if config.get("auto_consolidate") and LEARNINGS_DIR.exists():
        if len(list(LEARNINGS_DIR.glob("*.json"))) >= 10:
            return "Run 'cc-flow consolidate' to promote patterns"
    return None


def cmd_done(args):
    """Complete a task — record duration, diff stats, and optional summary."""
    from cc_flow.core import resolve_task_id
    args.id = resolve_task_id(args.id)
    path = TASKS_SUBDIR / f"{args.id}.json"
    if not path.exists():
        error(f"Task not found: {args.id}")

    data = safe_json_load(path)
    if data["status"] not in ("in_progress", "todo"):
        error(f"Cannot complete task with status: {data['status']}")

    duration_sec = _calc_duration(data.get("started"))
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
    _fire_plugin_hook("on_task_done", task=data)

    result = {"success": True, "id": args.id, "status": "done"}
    if duration_sec is not None:
        result["duration"] = _format_duration(duration_sec)
    if diff_stats:
        result["diff"] = diff_stats
    hint = _consolidation_hint()
    if hint:
        result["hint"] = hint

    print(json.dumps(result))


def cmd_block(args):
    """Block a task with a reason."""
    from cc_flow.core import resolve_task_id
    args.id = resolve_task_id(args.id)
    path = TASKS_SUBDIR / f"{args.id}.json"
    if not path.exists():
        error(f"Task not found: {args.id}")

    data = safe_json_load(path)
    data["status"] = "blocked"
    data["blocked_reason"] = args.reason
    data["blocked_at"] = now_iso()
    save_task(path, data)
    _fire_plugin_hook("on_task_block", task=data)
    print(json.dumps({"success": True, "id": args.id, "status": "blocked"}))


def cmd_reopen(args):
    """Reopen a done or blocked task back to todo."""
    from cc_flow.core import resolve_task_id
    args.id = resolve_task_id(args.id)
    path = TASKS_SUBDIR / f"{args.id}.json"
    if not path.exists():
        error(f"Task not found: {args.id}")

    data = safe_json_load(path)
    if data["status"] not in ("done", "blocked"):
        error(f"Cannot reopen task with status: {data['status']} (must be done or blocked)")

    prev_status = data["status"]
    data["status"] = "todo"
    for field in ("completed", "summary", "blocked_reason", "blocked_at", "duration_sec", "diff"):
        data.pop(field, None)
    if args.reason:
        data["reopen_reason"] = args.reason
    data["reopened_at"] = now_iso()
    save_task(path, data)
    print(json.dumps({"success": True, "id": args.id, "previous": prev_status, "status": "todo"}))


def cmd_diff(args):
    """Show git changes since a task was started."""
    import subprocess as _sp

    from cc_flow.core import resolve_task_id

    args.id = resolve_task_id(args.id)
    path = TASKS_SUBDIR / f"{args.id}.json"
    if not path.exists():
        error(f"Task not found: {args.id}")

    data = safe_json_load(path)
    start_sha = data.get("git_sha_start")
    if not start_sha:
        error(f"Task {args.id} has no recorded start SHA (was it started with cc-flow start?)")

    stat_only = getattr(args, "stat", False)
    cmd = ["git", "diff", start_sha, "HEAD"]
    if stat_only:
        cmd.append("--stat")

    try:
        result = _sp.run(cmd, check=False, capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            error(f"git diff failed: {result.stderr[:200]}")

        if getattr(args, "json", False):
            diff_stats = _get_diff_stats(start_sha)
            print(json.dumps({
                "success": True, "id": args.id, "start_sha": start_sha,
                "stats": diff_stats, "output_lines": len(result.stdout.split("\n")),
            }))
        else:
            print(result.stdout)
    except (_sp.TimeoutExpired, OSError) as exc:
        error(f"git diff failed: {exc}")


def _get_diff_stats(start_sha=None):
    """Get git diff stats since a commit SHA."""
    import subprocess as _sp
    if not start_sha:
        return None
    try:
        result = _sp.run(
            ["git", "diff", "--stat", start_sha, "HEAD"],
            check=False, capture_output=True, text=True, timeout=10,
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


_VALID_BULK_ACTIONS = ("done", "todo", "blocked")


def cmd_bulk(args):
    """Batch status change: mark multiple tasks done/todo/blocked at once."""
    action = args.action
    if action not in _VALID_BULK_ACTIONS:
        error(f"Invalid action: {action}. Use: {', '.join(_VALID_BULK_ACTIONS)}")

    tasks = all_tasks()
    task_ids = args.ids
    epic_filter = getattr(args, "epic", "") or ""

    # If --epic, apply to all matching tasks
    if epic_filter and not task_ids:
        task_ids = [tid for tid, t in tasks.items() if t.get("epic") == epic_filter]

    if not task_ids:
        error("No tasks specified. Use task IDs or --epic.")

    updated = []
    skipped = []
    for tid in task_ids:
        path = TASKS_SUBDIR / f"{tid}.json"
        if not path.exists():
            skipped.append({"id": tid, "reason": "not found"})
            continue

        data = safe_json_load(path)
        if data["status"] == action:
            skipped.append({"id": tid, "reason": f"already {action}"})
            continue

        data["status"] = action
        if action == "done":
            data["completed"] = now_iso()
        elif action == "todo":
            for field in ("started", "completed", "summary", "blocked_reason", "blocked_at"):
                data.pop(field, None)
        save_task(path, data)
        updated.append(tid)

    print(json.dumps({
        "success": True,
        "action": action,
        "updated": updated,
        "skipped": skipped,
        "count": len(updated),
    }))
