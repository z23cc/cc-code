"""cc-flow logging commands — log, summary, archive, stats, standup."""

import json
from datetime import datetime, timedelta, timezone

from cc_flow.core import COMPLETED_DIR, LOG_FILE, all_tasks, error, now_iso, safe_json_load

LOG_HEADER = (
    "timestamp\titeration\tmode\tarea\ttask_id\tdescription"
    "\tstatus\tfiles_changed\tdiff_lines\tduration_sec\tnotes\n"
)


def cmd_log(args):
    """Append entry to improvement-results.tsv or show recent entries."""
    if args.show:
        if not LOG_FILE.exists():
            error("No log file found")
        lines = LOG_FILE.read_text().strip().split("\n")
        n = min(args.show, len(lines) - 1)
        entries = []
        for line in lines[-n:]:
            parts = line.split("\t")
            if len(parts) >= 6:
                entries.append({
                    "timestamp": parts[0], "iteration": parts[1], "mode": parts[2],
                    "task_id": parts[4], "status": parts[6] if len(parts) > 6 else "",
                })
        print(json.dumps({"success": True, "entries": entries, "total": len(lines) - 1}))
        return

    if not LOG_FILE.exists():
        LOG_FILE.write_text(LOG_HEADER)

    row = "\t".join([
        now_iso(), str(args.iteration or ""), args.mode or "", args.area or "",
        args.task_id or "", args.description or "", args.status or "",
        str(args.files or ""), str(args.diff_lines or ""),
        str(args.duration or ""), args.notes or "",
    ])
    with open(LOG_FILE, "a") as f:
        f.write(row + "\n")
    print(json.dumps({"success": True, "logged": args.status}))


def cmd_summary(_args):
    """Print session summary from improvement-results.tsv."""
    if not LOG_FILE.exists():
        print("No improvement-results.tsv found.")
        return
    lines = LOG_FILE.read_text().strip().split("\n")[1:]
    kept = sum(1 for row in lines if "KEPT" in row)
    discarded = sum(1 for row in lines if "DISCARDED" in row)
    skipped = sum(1 for row in lines if "SKIPPED" in row)
    total = len(lines)
    pct = int(kept / total * 100) if total > 0 else 0
    print("## Autoimmune Summary")
    print("| Metric | Value |")
    print("|--------|-------|")
    print(f"| Iterations | {total} |")
    print(f"| Kept | {kept} ({pct}%) |")
    print(f"| Discarded | {discarded} |")
    print(f"| Skipped | {skipped} |")


def cmd_archive(_args):
    """Show completed/archived epics and tasks."""
    if not COMPLETED_DIR.exists():
        print(json.dumps({"success": True, "archived": [], "count": 0}))
        return
    archived_epics = []
    for f in sorted(COMPLETED_DIR.glob("*.md")):
        parts = f.stem.split(".")
        if len(parts) == 1:
            epic_id = f.stem
            task_files = list(COMPLETED_DIR.glob(f"{epic_id}.*.json"))
            archived_epics.append({"id": epic_id, "tasks": len(task_files)})
    if not archived_epics:
        task_jsons = sorted(COMPLETED_DIR.glob("*.json"))
        tasks = []
        for f in task_jsons:
            d = safe_json_load(f, default=None)
            if d and "id" in d:
                tasks.append({"id": d["id"], "title": d.get("title", ""), "completed": d.get("completed", "")})
        print(json.dumps({"success": True, "tasks": tasks, "count": len(tasks)}))
    else:
        print(json.dumps({"success": True, "archived": archived_epics, "count": len(archived_epics)}))


def _calc_velocity(tasks):
    """Calculate task velocity from completed timestamps."""
    done_tasks = [t for t in tasks.values() if t.get("completed")]
    if len(done_tasks) < 2:
        return None
    times = sorted(t["completed"] for t in done_tasks)
    first = datetime.fromisoformat(times[0].replace("Z", "+00:00"))
    last = datetime.fromisoformat(times[-1].replace("Z", "+00:00"))
    hours = max((last - first).total_seconds() / 3600, 0.1)
    return round(len(done_tasks) / hours, 1)


def cmd_stats(_args):
    """Productivity stats (JSON output)."""
    log_totals = {"kept": 0, "discarded": 0, "skipped": 0}
    if LOG_FILE.exists():
        for line in LOG_FILE.read_text().strip().split("\n")[1:]:
            parts = line.split("\t")
            if len(parts) >= 7 and parts[6] in log_totals:
                log_totals[parts[6]] += 1

    tasks = all_tasks()
    by_status = {"todo": 0, "in_progress": 0, "done": 0, "blocked": 0}
    for t in tasks.values():
        by_status[t.get("status", "todo")] = by_status.get(t.get("status", "todo"), 0) + 1

    epic_count = len({t.get("epic") for t in tasks.values()})
    velocity = _calc_velocity(tasks)

    total_attempts = log_totals["kept"] + log_totals["discarded"]
    result = {
        "success": True,
        "epics": epic_count,
        "tasks": len(tasks),
        "by_status": by_status,
        "velocity": f"{velocity} tasks/hour" if velocity else "insufficient data",
    }
    if total_attempts > 0:
        result["autoimmune"] = {
            **log_totals,
            "success_rate": int(log_totals["kept"] / total_attempts * 100),
        }

    print(json.dumps(result))


def cmd_standup(args):
    """Daily standup report: done recently, in progress, blocked, next up."""
    hours = getattr(args, "hours", 24) or 24
    cutoff = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()

    tasks = all_tasks()

    recently_done = [
        {"id": t["id"], "title": t.get("title", ""), "completed": t.get("completed", "")}
        for t in tasks.values()
        if t["status"] == "done" and t.get("completed", "") >= cutoff
    ]
    recently_done.sort(key=lambda t: t["completed"], reverse=True)

    in_progress = [
        {"id": t["id"], "title": t.get("title", ""), "started": t.get("started", "")}
        for t in tasks.values()
        if t["status"] == "in_progress"
    ]

    blocked = [
        {"id": t["id"], "title": t.get("title", ""), "reason": t.get("blocked_reason", "")}
        for t in tasks.values()
        if t["status"] == "blocked"
    ]

    # Next ready tasks (deps satisfied)
    next_up = []
    for t in tasks.values():
        if t["status"] != "todo":
            continue
        deps_done = all(tasks.get(d, {}).get("status") == "done" for d in t.get("depends_on", []))
        if deps_done:
            next_up.append({"id": t["id"], "title": t.get("title", ""),
                            "priority": t.get("priority", 999)})
    next_up.sort(key=lambda t: t["priority"])

    print(json.dumps({
        "success": True,
        "period_hours": hours,
        "done": recently_done,
        "in_progress": in_progress,
        "blocked": blocked,
        "next_up": next_up[:5],
        "summary": {
            "done_count": len(recently_done),
            "active_count": len(in_progress),
            "blocked_count": len(blocked),
            "ready_count": len(next_up),
        },
    }))


def cmd_changelog(args):
    """Generate changelog from completed tasks, grouped by epic."""
    tasks = all_tasks()
    done = [t for t in tasks.values() if t["status"] == "done" and t.get("completed")]
    done.sort(key=lambda t: t.get("completed", ""), reverse=True)

    # Group by epic
    by_epic = {}
    for t in done:
        epic = t.get("epic", "ungrouped")
        by_epic.setdefault(epic, []).append(t)

    if getattr(args, "json", False):
        print(json.dumps({"success": True, "epics": {
            epic: [{"id": t["id"], "title": t.get("title", ""), "completed": t.get("completed", ""),
                     "summary": t.get("summary", "")} for t in tasks_list]
            for epic, tasks_list in by_epic.items()
        }, "total": len(done)}))
        return

    lines = ["# Changelog", ""]
    for epic, tasks_list in by_epic.items():
        lines.append(f"## {epic}")
        lines.append("")
        for t in tasks_list:
            date = t.get("completed", "")[:10]
            title = t.get("title", "")
            summary = f" — {t['summary']}" if t.get("summary") else ""
            lines.append(f"- [{date}] {title}{summary}")
        lines.append("")

    print("\n".join(lines))
