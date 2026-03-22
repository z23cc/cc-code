"""cc-flow analytics — stats, standup, changelog, burndown, report, time."""

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from cc_flow.core import EPICS_DIR, LEARNINGS_DIR, LOG_FILE, all_tasks, error, now_iso


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


def _fmt_time(seconds):
    """Format seconds as human-readable duration."""
    if seconds < 60:
        return f"{seconds}s"
    if seconds < 3600:
        return f"{seconds // 60}m {seconds % 60}s"
    h = seconds // 3600
    m = (seconds % 3600) // 60
    return f"{h}h {m}m"


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


def cmd_burndown(args):
    """Burndown data for an epic -- remaining tasks over time."""
    epic_id = args.epic
    if not (EPICS_DIR / f"{epic_id}.md").exists():
        error(f"Epic not found: {epic_id}")

    tasks = all_tasks()
    epic_tasks = [t for t in tasks.values() if t.get("epic") == epic_id]
    if not epic_tasks:
        error(f"No tasks in epic: {epic_id}")

    total = len(epic_tasks)
    events = sorted(
        [(t["completed"], t["id"]) for t in epic_tasks if t.get("completed")],
        key=lambda x: x[0],
    )

    points = []
    if events:
        start_times = [t.get("started") or t.get("created", "") for t in epic_tasks]
        earliest = min(t for t in start_times if t) if any(start_times) else events[0][0]
        points.append({"date": earliest[:10], "remaining": total, "done": 0})

        done_count = 0
        for completed, _ in events:
            done_count += 1
            points.append({"date": completed[:10], "remaining": total - done_count, "done": done_count})

    remaining = total - sum(1 for t in epic_tasks if t["status"] == "done")
    print(json.dumps({
        "success": True, "epic": epic_id, "total": total,
        "remaining": remaining, "done": total - remaining,
        "pct": int((total - remaining) / total * 100) if total > 0 else 0,
        "burndown": points,
    }))


def cmd_report(args):
    """Generate comprehensive project report in markdown."""
    tasks = all_tasks()
    total = len(tasks)
    done = [t for t in tasks.values() if t["status"] == "done"]
    in_prog = [t for t in tasks.values() if t["status"] == "in_progress"]
    blocked = [t for t in tasks.values() if t["status"] == "blocked"]
    todo = [t for t in tasks.values() if t["status"] == "todo"]

    velocity = _calc_velocity(tasks)
    epic_files = sorted(EPICS_DIR.glob("*.md")) if EPICS_DIR.exists() else []
    learn_count = len(list(LEARNINGS_DIR.glob("*.json"))) if LEARNINGS_DIR.exists() else 0

    lines = [
        "# Project Report",
        f"*Generated: {now_iso()}*",
        "",
        "## Overview",
        "",
        "| Metric | Value |",
        "|--------|-------|",
        f"| Epics | {len(epic_files)} |",
        f"| Total tasks | {total} |",
        f"| Done | {len(done)} ({int(len(done) / total * 100) if total else 0}%) |",
        f"| In progress | {len(in_prog)} |",
        f"| Blocked | {len(blocked)} |",
        f"| Todo | {len(todo)} |",
        f"| Velocity | {velocity} tasks/hour |" if velocity else "| Velocity | --- |",
        f"| Learnings | {learn_count} |",
        "",
    ]

    if epic_files:
        lines.extend(["## Epics", ""])
        for f in epic_files:
            eid = f.stem
            etasks = [t for t in tasks.values() if t.get("epic") == eid]
            edone = sum(1 for t in etasks if t["status"] == "done")
            pct = int(edone / len(etasks) * 100) if etasks else 0
            lines.append(f"- **{eid}**: {edone}/{len(etasks)} ({pct}%)")
        lines.append("")

    if done:
        lines.extend(["## Recently Completed", ""])
        for t in sorted(done, key=lambda x: x.get("completed", ""), reverse=True)[:10]:
            date = t.get("completed", "")[:10]
            lines.append(f"- [{date}] {t.get('title', '')}")
        lines.append("")

    if blocked:
        lines.extend(["## Blocked", ""])
        lines.extend(
            f"- **{t['id']}**: {t.get('title', '')} -- {t.get('blocked_reason', 'no reason')}"
            for t in blocked
        )
        lines.append("")

    output = "\n".join(lines)
    out_file = getattr(args, "output", "") or ""
    if out_file:
        Path(out_file).write_text(output)
        print(json.dumps({"success": True, "file": out_file, "lines": len(lines)}))
    else:
        print(output)


def cmd_time(args):
    """Time tracking report -- duration per task, averages, slowest tasks."""
    tasks = all_tasks()
    epic_filter = getattr(args, "epic", "") or ""

    timed = []
    for t in tasks.values():
        dur = t.get("duration_sec")
        if dur is None or t["status"] != "done":
            continue
        if epic_filter and t.get("epic") != epic_filter:
            continue
        timed.append({
            "id": t["id"], "title": t.get("title", ""), "epic": t.get("epic", ""),
            "duration_sec": dur, "duration": _fmt_time(dur),
            "size": t.get("size", "M"),
        })

    timed.sort(key=lambda t: -t["duration_sec"])

    total_sec = sum(t["duration_sec"] for t in timed)
    avg_sec = total_sec // len(timed) if timed else 0

    by_size = {}
    for t in timed:
        by_size.setdefault(t["size"], []).append(t["duration_sec"])
    size_avg = {s: sum(v) // len(v) for s, v in by_size.items()}

    by_epic = {}
    for t in timed:
        by_epic.setdefault(t["epic"], {"total": 0, "count": 0})
        by_epic[t["epic"]]["total"] += t["duration_sec"]
        by_epic[t["epic"]]["count"] += 1

    print(json.dumps({
        "success": True,
        "tasks": timed[:10],
        "total_tasks": len(timed),
        "total_time": _fmt_time(total_sec),
        "avg_time": _fmt_time(avg_sec),
        "slowest": timed[0] if timed else None,
        "by_size": {s: _fmt_time(v) for s, v in size_avg.items()},
        "by_epic": {e: {"total": _fmt_time(v["total"]), "count": v["count"]}
                    for e, v in by_epic.items()},
    }))
