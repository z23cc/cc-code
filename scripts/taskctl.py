#!/usr/bin/env python3
"""taskctl — lightweight file-based task manager for cc-code plugin.

Usage:
    taskctl init
    taskctl epic create --title "Epic title"
    taskctl task create --epic epic-1 --title "Task title" [--deps epic-1.1,epic-1.2]
    taskctl list
    taskctl epics
    taskctl tasks [--epic epic-1] [--status todo]
    taskctl show <id>
    taskctl ready [--epic epic-1]
    taskctl start <task-id>
    taskctl done <task-id> [--summary "What was done"]
    taskctl block <task-id> --reason "Why blocked"
    taskctl progress [--epic epic-1]
"""

import argparse
import json
import glob
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

TASKS_DIR = Path(".tasks")
EPICS_DIR = TASKS_DIR / "epics"
TASKS_SUBDIR = TASKS_DIR / "tasks"
COMPLETED_DIR = TASKS_DIR / "completed"
META_FILE = TASKS_DIR / "meta.json"


def now_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def load_meta():
    if META_FILE.exists():
        return json.loads(META_FILE.read_text())
    return {"next_epic": 1}


def save_meta(meta):
    META_FILE.write_text(json.dumps(meta, indent=2) + "\n")


def slugify(title):
    return "-".join(title.lower().split()[:4]).replace("/", "-").replace(".", "")


def load_task(path):
    return json.loads(Path(path).read_text())


def save_task(path, data):
    Path(path).write_text(json.dumps(data, indent=2) + "\n")


def all_tasks():
    tasks = {}
    for f in sorted(TASKS_SUBDIR.glob("*.json")):
        d = json.loads(f.read_text())
        tasks[d["id"]] = d
    return tasks


def cmd_init(_args):
    for d in [TASKS_DIR, EPICS_DIR, TASKS_SUBDIR, COMPLETED_DIR]:
        d.mkdir(parents=True, exist_ok=True)
    if not META_FILE.exists():
        save_meta({"next_epic": 1})
    print(json.dumps({"success": True, "path": str(TASKS_DIR)}))


def cmd_epic_create(args):
    meta = load_meta()
    epic_num = meta["next_epic"]
    slug = slugify(args.title)
    epic_id = f"epic-{epic_num}-{slug}"
    meta["next_epic"] = epic_num + 1
    save_meta(meta)

    spec_path = EPICS_DIR / f"{epic_id}.md"
    spec_path.write_text(
        f"# Epic: {args.title}\n\n"
        f"## Goal\n\n[Describe the goal]\n\n"
        f"## Requirements\n\n- [ ] [Requirement 1]\n\n"
        f"## Acceptance Criteria\n\n- [Criterion 1]\n"
    )
    print(json.dumps({"success": True, "id": epic_id, "spec": str(spec_path)}))


def cmd_task_create(args):
    epic_id = args.epic
    # Find next task number for this epic
    existing = list(TASKS_SUBDIR.glob(f"{epic_id}.*.json"))
    next_num = len(existing) + 1
    task_id = f"{epic_id}.{next_num}"
    deps = args.deps.split(",") if args.deps else []

    state = {
        "id": task_id,
        "epic": epic_id,
        "title": args.title,
        "status": "todo",
        "depends_on": deps,
        "created": now_iso(),
    }
    save_task(TASKS_SUBDIR / f"{task_id}.json", state)

    spec_path = TASKS_SUBDIR / f"{task_id}.md"
    spec_path.write_text(
        f"# Task: {args.title}\n\n"
        f"## Description\n\n[Describe what to do]\n\n"
        f"## Acceptance Criteria\n\n- [ ] [Criterion 1]\n"
    )
    print(json.dumps({"success": True, "id": task_id, "epic": epic_id}))


def cmd_list(_args):
    epics = {}
    for f in sorted(EPICS_DIR.glob("*.md")):
        epic_id = f.stem
        epics[epic_id] = {"id": epic_id, "tasks": []}

    tasks = all_tasks()
    for t in tasks.values():
        epic = t.get("epic", "")
        if epic in epics:
            epics[epic]["tasks"].append(t)

    for epic_id, epic in epics.items():
        done = sum(1 for t in epic["tasks"] if t["status"] == "done")
        total = len(epic["tasks"])
        print(f"\n[{epic_id}] ({done}/{total} done)")
        for t in epic["tasks"]:
            status = t["status"]
            marker = {"todo": "○", "in_progress": "◐", "done": "●", "blocked": "✗"}
            print(f"  {marker.get(status, '?')} [{status:12}] {t['id']}: {t['title']}")

    if not epics:
        print("No epics found. Run: taskctl init && taskctl epic create --title '...'")


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
    result = []
    for t in tasks.values():
        if args.epic and t.get("epic") != args.epic:
            continue
        if args.status and t["status"] != args.status:
            continue
        result.append(t)
    print(json.dumps({"success": True, "tasks": result, "count": len(result)}))


def cmd_show(args):
    task_id = args.id
    # Try task first
    task_path = TASKS_SUBDIR / f"{task_id}.json"
    if task_path.exists():
        data = json.loads(task_path.read_text())
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


def cmd_start(args):
    path = TASKS_SUBDIR / f"{args.id}.json"
    if not path.exists():
        print(json.dumps({"success": False, "error": f"Task not found: {args.id}"}))
        sys.exit(1)

    data = json.loads(path.read_text())
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
    save_task(path, data)
    print(json.dumps({"success": True, "id": args.id, "status": "in_progress"}))


def cmd_done(args):
    path = TASKS_SUBDIR / f"{args.id}.json"
    if not path.exists():
        print(json.dumps({"success": False, "error": f"Task not found: {args.id}"}))
        sys.exit(1)

    data = json.loads(path.read_text())
    data["status"] = "done"
    data["completed"] = now_iso()
    if args.summary:
        data["summary"] = args.summary
    save_task(path, data)
    print(json.dumps({"success": True, "id": args.id, "status": "done"}))


def cmd_block(args):
    path = TASKS_SUBDIR / f"{args.id}.json"
    if not path.exists():
        print(json.dumps({"success": False, "error": f"Task not found: {args.id}"}))
        sys.exit(1)

    data = json.loads(path.read_text())
    data["status"] = "blocked"
    data["blocked_reason"] = args.reason
    data["blocked_at"] = now_iso()
    save_task(path, data)
    print(json.dumps({"success": True, "id": args.id, "status": "blocked"}))


def cmd_progress(args):
    tasks = all_tasks()
    epics = {}
    for f in sorted(EPICS_DIR.glob("*.md")):
        epics[f.stem] = []

    for t in tasks.values():
        epic = t.get("epic", "")
        if epic in epics:
            epics[epic].append(t)

    for epic_id, epic_tasks in epics.items():
        if args.epic and epic_id != args.epic:
            continue
        total = len(epic_tasks)
        if total == 0:
            print(f"{epic_id}: no tasks")
            continue
        done = sum(1 for t in epic_tasks if t["status"] == "done")
        in_prog = sum(1 for t in epic_tasks if t["status"] == "in_progress")
        blocked = sum(1 for t in epic_tasks if t["status"] == "blocked")
        todo = total - done - in_prog - blocked
        pct = int(done / total * 100)

        bar_len = 20
        filled = int(bar_len * done / total)
        bar = "█" * filled + "░" * (bar_len - filled)

        print(f"{epic_id}: {bar} {pct}% ({done}/{total})")
        if in_prog:
            print(f"  ◐ {in_prog} in progress")
        if blocked:
            print(f"  ✗ {blocked} blocked")
        if todo:
            print(f"  ○ {todo} todo")


def main():
    parser = argparse.ArgumentParser(prog="taskctl", description="cc-code task manager")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("init")

    epic_p = sub.add_parser("epic")
    epic_sub = epic_p.add_subparsers(dest="epic_cmd")
    ec = epic_sub.add_parser("create")
    ec.add_argument("--title", required=True)

    tc = sub.add_parser("task")
    task_sub = tc.add_subparsers(dest="task_cmd")
    tc_create = task_sub.add_parser("create")
    tc_create.add_argument("--epic", required=True)
    tc_create.add_argument("--title", required=True)
    tc_create.add_argument("--deps", default="")

    sub.add_parser("list")
    sub.add_parser("epics")

    tasks_p = sub.add_parser("tasks")
    tasks_p.add_argument("--epic", default="")
    tasks_p.add_argument("--status", default="")

    show_p = sub.add_parser("show")
    show_p.add_argument("id")

    ready_p = sub.add_parser("ready")
    ready_p.add_argument("--epic", default="")

    start_p = sub.add_parser("start")
    start_p.add_argument("id")

    done_p = sub.add_parser("done")
    done_p.add_argument("id")
    done_p.add_argument("--summary", default="")

    block_p = sub.add_parser("block")
    block_p.add_argument("id")
    block_p.add_argument("--reason", required=True)

    progress_p = sub.add_parser("progress")
    progress_p.add_argument("--epic", default="")

    args = parser.parse_args()

    cmds = {
        "init": cmd_init,
        "list": cmd_list,
        "epics": cmd_epics,
        "tasks": cmd_tasks,
        "show": cmd_show,
        "ready": cmd_ready,
        "start": cmd_start,
        "done": cmd_done,
        "block": cmd_block,
        "progress": cmd_progress,
    }

    if args.command == "epic" and getattr(args, "epic_cmd", None) == "create":
        cmd_epic_create(args)
    elif args.command == "task" and getattr(args, "task_cmd", None) == "create":
        cmd_task_create(args)
    elif args.command in cmds:
        cmds[args.command](args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
