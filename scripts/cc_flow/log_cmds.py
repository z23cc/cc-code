"""cc-flow logging commands — log, summary, archive.

Analytics commands (stats, standup, changelog, burndown, report, time)
moved to analytics.py.
"""

import json

from cc_flow.core import COMPLETED_DIR, LOG_FILE, error, now_iso, safe_json_load

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
    from cc_flow import skin
    skin.heading("Autoimmune Summary")
    skin.table(["Metric", "Value"], [
        ["Iterations", str(total)],
        ["Kept", f"{kept} ({pct}%)"],
        ["Discarded", str(discarded)],
        ["Skipped", str(skipped)],
    ])


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


# Re-export analytics for backward compatibility
from cc_flow.analytics import (  # noqa: E402, F401
    cmd_burndown,
    cmd_changelog,
    cmd_report,
    cmd_standup,
    cmd_stats,
    cmd_time,
)
