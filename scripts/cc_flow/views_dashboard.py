"""cc-flow dashboard and progress visualization."""

import json
from datetime import datetime

from cc_flow.core import (
    EPICS_DIR,
    LEARNINGS_DIR,
    LOG_FILE,
    TASKS_DIR,
    all_tasks,
)
from cc_flow.route_learn import _load_route_stats
from cc_flow.views import _epic_label, _task_counts, cmd_status


def _print_epic_progress(epic_id, counts):
    """Print a progress bar for an epic."""
    from cc_flow import skin

    label = _epic_label(epic_id)
    if counts["total"] == 0:
        skin.dim(f"{label}: no tasks")
        return
    skin.progress_bar(counts["done"], counts["total"], f"{label} ({counts['done']}/{counts['total']})")
    if counts["in_progress"]:
        skin.dim(f"  {counts['in_progress']} in progress")
    if counts["blocked"]:
        skin.warning(f"{counts['blocked']} blocked")
    if counts["todo"]:
        skin.dim(f"  {counts['todo']} todo")


def cmd_progress(args):
    """Show progress bars per epic with task status breakdown."""
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
    """One-screen overview: epics, velocity, health, learnings."""
    if getattr(args, "json", False):
        cmd_status(args)
        return

    from cc_flow import skin

    tasks = all_tasks()
    counts = _task_counts(list(tasks.values()))

    skin.banner()
    skin.progress_bar(counts["done"], counts["total"], "tasks completed")
    skin.info(
        f"{counts['done']} done  {counts['in_progress']} active  "
        f"{counts['todo']} todo  {counts['blocked']} blocked",
    )

    # Velocity
    done_tasks = [t for t in tasks.values() if t.get("completed")]
    if len(done_tasks) >= 2:
        times = sorted(t["completed"] for t in done_tasks)
        first = datetime.fromisoformat(times[0].replace("Z", "+00:00"))
        last = datetime.fromisoformat(times[-1].replace("Z", "+00:00"))
        hours = max((last - first).total_seconds() / 3600, 0.1)
        skin.dim(f"Velocity: {len(done_tasks) / hours:.1f} tasks/hour")

    # Epics
    epic_files = sorted(EPICS_DIR.glob("*.md")) if EPICS_DIR.exists() else []
    if epic_files:
        skin.heading("Epics")
        rows = []
        for f in epic_files[:5]:
            epic_tasks = [t for t in tasks.values() if t.get("epic") == f.stem]
            ec = _task_counts(epic_tasks)
            title = f.read_text().split("\n", 1)[0].lstrip("# ").replace("Epic:", "").strip()[:30]
            rows.append([f.stem, f"{ec['done']}/{ec['total']}", f"{ec['pct']}%", title])
        skin.table(["Epic", "Done", "Pct", "Title"], rows)

    # Learning + Autoimmune
    learn_count = len(list(LEARNINGS_DIR.glob("*.json"))) if LEARNINGS_DIR.exists() else 0
    if learn_count > 0:
        skin.dim(f"Learnings: {learn_count}")

    # Hint
    _print_dashboard_hint(tasks)
