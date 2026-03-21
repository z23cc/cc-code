"""cc-flow views commands."""

import json
import sys
from datetime import datetime

from cc_flow import VERSION
from cc_flow.core import (
    EPICS_DIR, LEARNINGS_DIR, LOG_FILE, TASKS_DIR, TASKS_SUBDIR,
    all_tasks, safe_json_load,
)
from cc_flow.route_learn import _load_route_stats


def cmd_list(args):
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
    epics = []
    tasks = all_tasks()
    for f in sorted(EPICS_DIR.glob("*.md")):
        epic_id = f.stem
        epic_tasks = [t for t in tasks.values() if t.get("epic") == epic_id]
        done = sum(1 for t in epic_tasks if t["status"] == "done")
        epics.append({"id": epic_id, "tasks": len(epic_tasks), "done": done})
    print(json.dumps({"success": True, "epics": epics}))


def cmd_tasks(args):
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

    print(json.dumps({"success": False, "error": f"Not found: {task_id}"}))
    sys.exit(1)


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


def cmd_progress(args):
    tasks = all_tasks()
    epics = {}
    for f in sorted(EPICS_DIR.glob("*.md")):
        epics[f.stem] = []

    for t in tasks.values():
        epic = t.get("epic", "")
        if epic in epics:
            epics[epic].append(t)

    json_output = []
    for epic_id, epic_tasks in epics.items():
        if args.epic and epic_id != args.epic:
            continue
        total = len(epic_tasks)
        done = sum(1 for t in epic_tasks if t["status"] == "done")
        in_prog = sum(1 for t in epic_tasks if t["status"] == "in_progress")
        blocked = sum(1 for t in epic_tasks if t["status"] == "blocked")
        todo = total - done - in_prog - blocked
        pct = int(done / total * 100) if total > 0 else 0
        entry = {"epic": epic_id, "total": total, "done": done,
                 "in_progress": in_prog, "blocked": blocked, "todo": todo, "pct": pct}
        json_output.append(entry)

        if not getattr(args, "json", False):
            # Extract title from epic spec
            epic_spec = EPICS_DIR / f"{epic_id}.md"
            epic_title = ""
            if epic_spec.exists():
                first_line = epic_spec.read_text().split("\n", 1)[0]
                epic_title = first_line.lstrip("# ").replace("Epic:", "").strip()
            label = f"{epic_title}" if epic_title else epic_id
            if total == 0:
                print(f"{label}: no tasks")
            else:
                bar_len = 20
                filled = int(bar_len * done / total)
                bar = "█" * filled + "░" * (bar_len - filled)
                print(f"{label}: {bar} {pct}% ({done}/{total})")
                if in_prog:
                    print(f"  ◐ {in_prog} in progress")
                if blocked:
                    print(f"  ✗ {blocked} blocked")
                if todo:
                    print(f"  ○ {todo} todo")

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


def cmd_dashboard(args):
    """One-screen overview: epics, velocity, health, learnings. Use --json for machine-readable."""
    if getattr(args, "json", False):
        cmd_status(args)
        return
    tasks = all_tasks()
    total = len(tasks)
    done = sum(1 for t in tasks.values() if t["status"] == "done")
    in_prog = sum(1 for t in tasks.values() if t["status"] == "in_progress")
    blocked = sum(1 for t in tasks.values() if t["status"] == "blocked")
    todo = total - done - in_prog - blocked

    # Header
    print("╔══════════════════════════════════════════╗")
    print(f"║  cc-flow Dashboard  (v{VERSION})          ║")
    print("╠══════════════════════════════════════════╣")

    # Global stats
    pct = int(done / total * 100) if total > 0 else 0
    bar_len = 20
    filled = int(bar_len * done / total) if total > 0 else 0
    bar = "█" * filled + "░" * (bar_len - filled)
    print(f"║  Progress: {bar} {pct:>3}%  ║")
    print(f"║  ● {done} done  ◐ {in_prog} active  ○ {todo} todo  ✗ {blocked} blocked ║")

    # Velocity
    done_tasks = [t for t in tasks.values() if t.get("completed")]
    if len(done_tasks) >= 2:
        times = sorted(t["completed"] for t in done_tasks)
        first = datetime.fromisoformat(times[0].replace("Z", "+00:00"))
        last = datetime.fromisoformat(times[-1].replace("Z", "+00:00"))
        hours = max((last - first).total_seconds() / 3600, 0.1)
        velocity = len(done_tasks) / hours
        print(f"║  Velocity: {velocity:.1f} tasks/hour                  ║")
    else:
        print("║  Velocity: —                              ║")

    print("╠══════════════════════════════════════════╣")

    # Epic summary
    epic_files = sorted(EPICS_DIR.glob("*.md")) if EPICS_DIR.exists() else []
    if epic_files:
        print("║  Epics:                                   ║")
        for f in epic_files[:5]:
            epic_id = f.stem
            epic_tasks = [t for t in tasks.values() if t.get("epic") == epic_id]
            e_done = sum(1 for t in epic_tasks if t["status"] == "done")
            e_total = len(epic_tasks)
            # Title
            first_line = f.read_text().split("\n", 1)[0]
            title = first_line.lstrip("# ").replace("Epic:", "").strip()[:25]
            e_pct = int(e_done / e_total * 100) if e_total > 0 else 0
            mini_bar = "█" * (e_pct // 10) + "░" * (10 - e_pct // 10)
            print(f"║    {mini_bar} {e_pct:>3}% {title:<25} ║")
        if len(epic_files) > 5:
            print(f"║    ... +{len(epic_files) - 5} more                          ║")
    else:
        print("║  No epics yet. Run: cc-flow epic create   ║")

    print("╠══════════════════════════════════════════╣")

    # Learnings & patterns
    learn_count = len(list(LEARNINGS_DIR.glob("*.json"))) if LEARNINGS_DIR.exists() else 0
    patterns_dir = TASKS_DIR / "patterns"
    pattern_count = len(list(patterns_dir.glob("*.json"))) if patterns_dir.exists() else 0
    route_stats = _load_route_stats()
    total_routes = sum(
        v.get("success", 0) + v.get("failure", 0)
        for v in route_stats.get("commands", {}).values()
    )

    print(f"║  Learning: {learn_count} entries, {pattern_count} patterns         ║")
    if total_routes > 0:
        total_success = sum(v.get("success", 0) for v in route_stats.get("commands", {}).values())
        rate = int(total_success / total_routes * 100) if total_routes > 0 else 0
        print(f"║  Routing:  {total_routes} routes, {rate}% success rate      ║")
    else:
        print("║  Routing:  no data yet                    ║")

    # Autoimmune log
    if LOG_FILE.exists():
        lines = LOG_FILE.read_text().strip().split("\n")[1:]
        kept = sum(1 for row in lines if "KEPT" in row)
        disc = sum(1 for row in lines if "DISCARDED" in row)
        ai_total = kept + disc
        if ai_total > 0:
            ai_rate = int(kept / ai_total * 100)
            print(f"║  Autoimmune: {ai_total} runs, {ai_rate}% success         ║")

    print("╚══════════════════════════════════════════╝")

    # Next action suggestion
    if blocked > 0:
        print(f"\n  ⚠ {blocked} blocked task(s). Run: cc-flow tasks --status blocked")
    elif in_prog > 0:
        ip = next(t for t in tasks.values() if t["status"] == "in_progress")
        print(f"\n  → Resume: {ip['id']} — {ip['title']}")
    elif todo > 0:
        # Find next ready
        for t in tasks.values():
            if t["status"] == "todo":
                deps_done = all(tasks.get(d, {}).get("status") == "done" for d in t.get("depends_on", []))
                if deps_done:
                    print(f"\n  → Next: cc-flow start {t['id']} — {t['title']}")
                    break
    elif total > 0:
        print("\n  ✅ All tasks done!")
    else:
        print("\n  → Get started: cc-flow epic create --title 'My Feature'")
