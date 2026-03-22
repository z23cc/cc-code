"""cc-flow logging commands — log, summary, archive, stats."""

import json
from datetime import datetime

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


def cmd_stats(_args):
    """Productivity stats."""
    stats = {"totals": {"kept": 0, "discarded": 0, "skipped": 0}}
    if LOG_FILE.exists():
        for line in LOG_FILE.read_text().strip().split("\n")[1:]:
            parts = line.split("\t")
            if len(parts) >= 7:
                s = parts[6]
                if s in stats["totals"]:
                    stats["totals"][s] += 1

    tasks = all_tasks()
    epic_stats = {}
    for t in tasks.values():
        epic = t.get("epic", "unknown")
        if epic not in epic_stats:
            epic_stats[epic] = {"total": 0, "done": 0}
        epic_stats[epic]["total"] += 1
        if t["status"] == "done":
            epic_stats[epic]["done"] += 1

    done_tasks = [t for t in tasks.values() if t.get("completed")]
    if len(done_tasks) >= 2:
        times = sorted(t["completed"] for t in done_tasks)
        first = datetime.fromisoformat(times[0].replace("Z", "+00:00"))
        last = datetime.fromisoformat(times[-1].replace("Z", "+00:00"))
        hours = max((last - first).total_seconds() / 3600, 0.1)
        velocity = f"{len(done_tasks) / hours:.1f} tasks/hour"
    else:
        velocity = "insufficient data"

    total_attempts = stats["totals"]["kept"] + stats["totals"]["discarded"]
    success_rate = int(stats["totals"]["kept"] / total_attempts * 100) if total_attempts > 0 else 0

    print("## Productivity Stats")
    print("| Metric | Value |")
    print("|--------|-------|")
    print(f"| Active epics | {len(epic_stats)} |")
    print(f"| Total tasks | {len(tasks)} |")
    print(f"| Done | {sum(e['done'] for e in epic_stats.values())} |")
    print(f"| Velocity | {velocity} |")
    if total_attempts > 0:
        print(f"| Autoimmune kept | {stats['totals']['kept']} |")
        print(f"| Success rate | {success_rate}% |")
