"""cc-flow views — core query commands.

Split into 3 modules:
  views.py           — list, epics, tasks, show, ready, next, status (this file)
  views_dashboard.py — progress, dashboard visualization
  views_search.py    — find, similar, export, priority, index, dedupe, suggest
"""

import json

from cc_flow.core import (
    EPICS_DIR,
    TASKS_SUBDIR,
    all_tasks,
    error,
    safe_json_load,
)


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
    """Show detail for an epic or task by ID."""
    task_id = args.id
    task_path = TASKS_SUBDIR / f"{task_id}.json"
    if task_path.exists():
        data = safe_json_load(task_path)
        spec_path = TASKS_SUBDIR / f"{task_id}.md"
        spec = spec_path.read_text() if spec_path.exists() else ""
        print(json.dumps({"success": True, "type": "task", "data": data}))
        if spec:
            print(f"\n{spec}")
        return

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
    """Show tasks with all dependencies satisfied (ready to start)."""
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
        in_prog = [t for t in tasks.values() if t["status"] == "in_progress"]
        if in_prog:
            t = in_prog[0]
            print(json.dumps({"success": True, "action": "resume", "id": t["id"], "title": t["title"]}))
        else:
            print(json.dumps({"success": True, "action": "none", "reason": "all done or blocked"}))
        return

    ready.sort(key=lambda t: (t.get("priority", 999), t["id"]))
    t = ready[0]
    print(json.dumps({"success": True, "action": "start", "id": t["id"], "title": t["title"]}))


# ── Shared helpers (used by views_dashboard.py and views_search.py) ──

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


# Re-export split modules for backward compatibility with entry.py lazy refs
from cc_flow.views_dashboard import cmd_dashboard, cmd_progress  # noqa: E402, F401
from cc_flow.views_search import (  # noqa: E402, F401
    cmd_dedupe,
    cmd_export,
    cmd_find,
    cmd_index,
    cmd_priority,
    cmd_similar,
    cmd_suggest,
)
