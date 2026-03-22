"""cc-flow views commands."""

import json
from datetime import datetime

from cc_flow import VERSION
from cc_flow.core import (
    EPICS_DIR,
    LEARNINGS_DIR,
    LOG_FILE,
    TASKS_DIR,
    TASKS_SUBDIR,
    all_tasks,
    error,
    safe_json_load,
)
from cc_flow.route_learn import _load_route_stats


def cmd_list(args):
    """Show all epics with their tasks, in text or JSON format."""
    epics = {}
    for f in sorted(EPICS_DIR.glob("*.md")):
        epic_id = f.stem
        epics[epic_id] = {"id": epic_id, "tasks": []}

    tasks = all_tasks()
    for t in tasks.values():
        epic = t.get("epic", "")
        if epic in epics:
            epics[epic]["tasks"].append(t)

    if getattr(args, "json", False):
        print(json.dumps({"success": True, "epics": list(epics.values()), "count": len(epics)}))
        return

    for epic_id, epic in epics.items():
        done = sum(1 for t in epic["tasks"] if t["status"] == "done")
        total = len(epic["tasks"])
        # Extract title from epic spec first line
        epic_spec = EPICS_DIR / f"{epic_id}.md"
        epic_title = ""
        if epic_spec.exists():
            first_line = epic_spec.read_text().split("\n", 1)[0]
            epic_title = first_line.lstrip("# ").replace("Epic:", "").strip()
        title_part = f": {epic_title}" if epic_title else ""
        print(f"\n[{epic_id}]{title_part} ({done}/{total} done)")
        for t in epic["tasks"]:
            status = t["status"]
            marker = {"todo": "○", "in_progress": "◐", "done": "●", "blocked": "✗"}
            size = t.get("size", "")
            size_tag = f" [{size}]" if size else ""
            print(f"  {marker.get(status, '?')} [{status:12}] {t['id']}: {t['title']}{size_tag}")

    if not epics:
        print("No epics found. Run: cc-flow init && cc-flow epic create --title '...'")


def cmd_epics(_args):
    """List all epics with task counts (JSON)."""
    epics = []
    tasks = all_tasks()
    for f in sorted(EPICS_DIR.glob("*.md")):
        epic_id = f.stem
        epic_tasks = [t for t in tasks.values() if t.get("epic") == epic_id]
        done = sum(1 for t in epic_tasks if t["status"] == "done")
        epics.append({"id": epic_id, "tasks": len(epic_tasks), "done": done})
    print(json.dumps({"success": True, "epics": epics}))


def cmd_tasks(args):
    """Filter and list tasks by epic, status, or tag."""
    tasks = all_tasks()
    tag_filter = getattr(args, "tag", "") or ""
    result = []
    for t in tasks.values():
        if args.epic and t.get("epic") != args.epic:
            continue
        if args.status and t["status"] != args.status:
            continue
        if tag_filter and tag_filter not in t.get("tags", []):
            continue
        result.append(t)
    print(json.dumps({"success": True, "tasks": result, "count": len(result)}))


def cmd_show(args):
    task_id = args.id
    # Try task first
    task_path = TASKS_SUBDIR / f"{task_id}.json"
    if task_path.exists():
        data = safe_json_load(task_path)
        spec_path = TASKS_SUBDIR / f"{task_id}.md"
        spec = spec_path.read_text() if spec_path.exists() else ""
        print(json.dumps({"success": True, "type": "task", "data": data}))
        if spec:
            print(f"\n{spec}")
        return

    # Try epic
    epic_path = EPICS_DIR / f"{task_id}.md"
    if epic_path.exists():
        print(epic_path.read_text())
        tasks = [t for t in all_tasks().values() if t.get("epic") == task_id]
        if tasks:
            print(f"\n## Tasks ({sum(1 for t in tasks if t['status'] == 'done')}/{len(tasks)} done)")
            for t in tasks:
                print(f"- [{t['status']}] {t['id']}: {t['title']}")
        return

    error(f"Not found: {task_id}")


def cmd_ready(args):
    tasks = all_tasks()
    ready, in_progress, blocked = [], [], []

    for t in tasks.values():
        if args.epic and t.get("epic") != args.epic:
            continue
        if t["status"] == "in_progress":
            in_progress.append(t)
        elif t["status"] == "blocked":
            blocked.append(t)
        elif t["status"] == "todo":
            deps_done = all(
                tasks.get(d, {}).get("status") == "done"
                for d in t.get("depends_on", [])
            )
            if deps_done:
                ready.append(t)

    print(json.dumps({
        "success": True,
        "ready": [{"id": t["id"], "title": t["title"]} for t in ready],
        "in_progress": [{"id": t["id"], "title": t["title"]} for t in in_progress],
        "blocked": [{"id": t["id"], "title": t["title"]} for t in blocked],
    }))


def cmd_next(args):
    """Smart next: pick highest-priority ready task."""
    tasks = all_tasks()
    ready = []
    for t in tasks.values():
        if args.epic and t.get("epic") != args.epic:
            continue
        if t["status"] != "todo":
            continue
        deps_done = all(
            tasks.get(d, {}).get("status") == "done"
            for d in t.get("depends_on", [])
        )
        if deps_done:
            ready.append(t)

    if not ready:
        # Check if there's in-progress work to resume
        in_prog = [t for t in tasks.values() if t["status"] == "in_progress"]
        if in_prog:
            t = in_prog[0]
            print(json.dumps({"success": True, "action": "resume", "id": t["id"], "title": t["title"]}))
        else:
            print(json.dumps({"success": True, "action": "none", "reason": "all done or blocked"}))
        return

    # Sort by priority field (lower = higher priority), then by id
    ready.sort(key=lambda t: (t.get("priority", 999), t["id"]))
    t = ready[0]
    print(json.dumps({"success": True, "action": "start", "id": t["id"], "title": t["title"]}))


def _task_counts(task_list):
    """Count tasks by status, return dict with total/done/in_progress/blocked/todo/pct."""
    total = len(task_list)
    done = sum(1 for t in task_list if t["status"] == "done")
    in_prog = sum(1 for t in task_list if t["status"] == "in_progress")
    blocked = sum(1 for t in task_list if t["status"] == "blocked")
    return {
        "total": total, "done": done, "in_progress": in_prog,
        "blocked": blocked, "todo": total - done - in_prog - blocked,
        "pct": int(done / total * 100) if total > 0 else 0,
    }


def _epic_label(epic_id):
    """Get epic display label from spec file, falling back to epic_id."""
    epic_spec = EPICS_DIR / f"{epic_id}.md"
    if epic_spec.exists():
        title = epic_spec.read_text().split("\n", 1)[0].lstrip("# ").replace("Epic:", "").strip()
        if title:
            return title
    return epic_id


def _print_epic_progress(epic_id, counts):
    """Print a progress bar for an epic."""
    label = _epic_label(epic_id)
    if counts["total"] == 0:
        print(f"{label}: no tasks")
        return
    filled = int(20 * counts["done"] / counts["total"])
    bar = "█" * filled + "░" * (20 - filled)
    print(f"{label}: {bar} {counts['pct']}% ({counts['done']}/{counts['total']})")
    if counts["in_progress"]:
        print(f"  ◐ {counts['in_progress']} in progress")
    if counts["blocked"]:
        print(f"  ✗ {counts['blocked']} blocked")
    if counts["todo"]:
        print(f"  ○ {counts['todo']} todo")


def cmd_progress(args):
    tasks = all_tasks()
    epics = {f.stem: [] for f in sorted(EPICS_DIR.glob("*.md"))}
    for t in tasks.values():
        epic = t.get("epic", "")
        if epic in epics:
            epics[epic].append(t)

    json_output = []
    for epic_id, epic_tasks in epics.items():
        if args.epic and epic_id != args.epic:
            continue
        counts = _task_counts(epic_tasks)
        json_output.append({"epic": epic_id, **counts})
        if not getattr(args, "json", False):
            _print_epic_progress(epic_id, counts)

    if getattr(args, "json", False):
        print(json.dumps({"success": True, "epics": json_output}))


def cmd_status(_args):
    """Global overview — epic counts, task counts, health."""
    tasks = all_tasks()
    epic_files = sorted(EPICS_DIR.glob("*.md"))
    total_tasks = len(tasks)
    done = sum(1 for t in tasks.values() if t["status"] == "done")
    in_prog = sum(1 for t in tasks.values() if t["status"] == "in_progress")
    blocked = sum(1 for t in tasks.values() if t["status"] == "blocked")
    todo = total_tasks - done - in_prog - blocked
    print(json.dumps({
        "success": True,
        "epics": len(epic_files),
        "tasks": total_tasks,
        "done": done,
        "in_progress": in_prog,
        "blocked": blocked,
        "todo": todo,
    }))


def _print_dashboard_progress(tasks):
    """Print progress bar and status counts."""
    counts = _task_counts(list(tasks.values()))
    filled = int(20 * counts["done"] / counts["total"]) if counts["total"] > 0 else 0
    bar = "█" * filled + "░" * (20 - filled)
    print(f"║  Progress: {bar} {counts['pct']:>3}%  ║")
    print(f"║  ● {counts['done']} done  ◐ {counts['in_progress']} active"
          f"  ○ {counts['todo']} todo  ✗ {counts['blocked']} blocked ║")


def _print_dashboard_velocity(tasks):
    """Print velocity stat from completed tasks."""
    done_tasks = [t for t in tasks.values() if t.get("completed")]
    if len(done_tasks) >= 2:
        times = sorted(t["completed"] for t in done_tasks)
        first = datetime.fromisoformat(times[0].replace("Z", "+00:00"))
        last = datetime.fromisoformat(times[-1].replace("Z", "+00:00"))
        hours = max((last - first).total_seconds() / 3600, 0.1)
        print(f"║  Velocity: {len(done_tasks) / hours:.1f} tasks/hour                  ║")
    else:
        print("║  Velocity: —                              ║")


def _print_dashboard_epics(tasks):
    """Print epic summary section."""
    epic_files = sorted(EPICS_DIR.glob("*.md")) if EPICS_DIR.exists() else []
    if not epic_files:
        print("║  No epics yet. Run: cc-flow epic create   ║")
        return
    print("║  Epics:                                   ║")
    for f in epic_files[:5]:
        epic_tasks = [t for t in tasks.values() if t.get("epic") == f.stem]
        e_counts = _task_counts(epic_tasks)
        title = f.read_text().split("\n", 1)[0].lstrip("# ").replace("Epic:", "").strip()[:25]
        mini_bar = "█" * (e_counts["pct"] // 10) + "░" * (10 - e_counts["pct"] // 10)
        print(f"║    {mini_bar} {e_counts['pct']:>3}% {title:<25} ║")
    if len(epic_files) > 5:
        print(f"║    ... +{len(epic_files) - 5} more                          ║")


def _print_dashboard_learning():
    """Print learning, routing, and autoimmune stats."""
    learn_count = len(list(LEARNINGS_DIR.glob("*.json"))) if LEARNINGS_DIR.exists() else 0
    patterns_dir = TASKS_DIR / "patterns"
    pattern_count = len(list(patterns_dir.glob("*.json"))) if patterns_dir.exists() else 0
    print(f"║  Learning: {learn_count} entries, {pattern_count} patterns         ║")

    route_stats = _load_route_stats()
    cmd_stats = route_stats.get("commands", {})
    total_routes = sum(v.get("success", 0) + v.get("failure", 0) for v in cmd_stats.values())
    if total_routes > 0:
        total_success = sum(v.get("success", 0) for v in cmd_stats.values())
        print(f"║  Routing:  {total_routes} routes, {int(total_success / total_routes * 100)}% success rate      ║")
    else:
        print("║  Routing:  no data yet                    ║")

    if LOG_FILE.exists():
        lines = LOG_FILE.read_text().strip().split("\n")[1:]
        kept = sum(1 for row in lines if "KEPT" in row)
        disc = sum(1 for row in lines if "DISCARDED" in row)
        ai_total = kept + disc
        if ai_total > 0:
            print(f"║  Autoimmune: {ai_total} runs, {int(kept / ai_total * 100)}% success         ║")


def _print_dashboard_hint(tasks):
    """Print next-action suggestion based on task state."""
    counts = _task_counts(list(tasks.values()))
    if counts["blocked"] > 0:
        print(f"\n  ⚠ {counts['blocked']} blocked task(s). Run: cc-flow tasks --status blocked")
    elif counts["in_progress"] > 0:
        ip = next(t for t in tasks.values() if t["status"] == "in_progress")
        print(f"\n  → Resume: {ip['id']} — {ip['title']}")
    elif counts["todo"] > 0:
        for t in tasks.values():
            if t["status"] == "todo":
                deps_done = all(tasks.get(d, {}).get("status") == "done" for d in t.get("depends_on", []))
                if deps_done:
                    print(f"\n  → Next: cc-flow start {t['id']} — {t['title']}")
                    break
    elif counts["total"] > 0:
        print("\n  ✅ All tasks done!")
    else:
        print("\n  → Get started: cc-flow epic create --title 'My Feature'")


def cmd_dashboard(args):
    """One-screen overview: epics, velocity, health, learnings. Use --json for machine-readable."""
    if getattr(args, "json", False):
        cmd_status(args)
        return
    tasks = all_tasks()
    print("╔══════════════════════════════════════════╗")
    print(f"║  cc-flow Dashboard  (v{VERSION})          ║")
    print("╠══════════════════════════════════════════╣")
    _print_dashboard_progress(tasks)
    _print_dashboard_velocity(tasks)
    print("╠══════════════════════════════════════════╣")
    _print_dashboard_epics(tasks)
    print("╠══════════════════════════════════════════╣")
    _print_dashboard_learning()
    print("╚══════════════════════════════════════════╝")
    _print_dashboard_hint(tasks)


def cmd_export(args):
    """Export an epic and its tasks as a self-contained markdown report."""
    epic_id = args.id
    epic_path = EPICS_DIR / f"{epic_id}.md"
    if not epic_path.exists():
        error(f"Epic not found: {epic_id}")

    tasks = all_tasks()
    epic_tasks = sorted(
        [t for t in tasks.values() if t.get("epic") == epic_id],
        key=lambda t: t["id"],
    )
    counts = _task_counts(epic_tasks)

    lines = [
        f"# {epic_id}",
        "",
        f"**Progress:** {counts['done']}/{counts['total']} ({counts['pct']}%)",
        f"**Status:** {counts['done']} done, {counts['in_progress']} in progress, "
        f"{counts['blocked']} blocked, {counts['todo']} todo",
        "",
        "## Spec",
        "",
        epic_path.read_text().strip(),
        "",
        "## Tasks",
        "",
    ]

    status_icon = {"todo": "[ ]", "in_progress": "[~]", "done": "[x]", "blocked": "[!]"}
    for t in epic_tasks:
        icon = status_icon.get(t["status"], "[ ]")
        line = f"- {icon} **{t['id']}**: {t.get('title', '')}"
        if t.get("summary"):
            line += f" — {t['summary']}"
        lines.append(line)

    output = "\n".join(lines) + "\n"

    out_file = getattr(args, "output", "") or ""
    if out_file:
        from pathlib import Path
        Path(out_file).write_text(output)
        print(json.dumps({"success": True, "epic": epic_id, "file": out_file,
                          "tasks": len(epic_tasks)}))
    else:
        print(output)
