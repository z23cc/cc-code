#!/usr/bin/env python3
"""cc-flow — lightweight file-based task manager for cc-code plugin.

Usage:
    cc-flow init
    cc-flow epic create --title "Epic title"
    cc-flow epic close <epic-id>
    cc-flow task create --epic <epic-id> --title "Task title" [--deps id1,id2]
    cc-flow task reset <task-id>
    cc-flow dep add <task-id> <dep-id>
    cc-flow list
    cc-flow epics
    cc-flow tasks [--epic <epic-id>] [--status todo|in_progress|done|blocked]
    cc-flow show <id>
    cc-flow ready [--epic <epic-id>]
    cc-flow next [--epic <epic-id>]
    cc-flow start <task-id>
    cc-flow done <task-id> [--summary "What was done"]
    cc-flow block <task-id> --reason "Why blocked"
    cc-flow progress [--epic <epic-id>]
    cc-flow status
    cc-flow validate
    cc-flow scan [--create-tasks]
    cc-flow log --status KEPT --task-id <id> --description "..." [--iteration N]
    cc-flow log --show 10
    cc-flow summary
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


def cmd_epic_import(args):
    """Import tasks from a plan markdown file. Parses ### Task N: Title headers."""
    import re

    plan_path = Path(args.file)
    if not plan_path.exists():
        print(json.dumps({"success": False, "error": f"File not found: {args.file}"}))
        sys.exit(1)

    content = plan_path.read_text()

    # Extract title from first H1
    title_match = re.search(r"^#\s+(.+)", content, re.MULTILINE)
    title = title_match.group(1).strip() if title_match else plan_path.stem

    # Create epic
    cmd_init(argparse.Namespace())
    meta = load_meta()
    epic_num = meta["next_epic"]
    slug = slugify(title)
    epic_id = f"epic-{epic_num}-{slug}"
    meta["next_epic"] = epic_num + 1
    save_meta(meta)

    # Copy plan as epic spec
    spec_path = EPICS_DIR / f"{epic_id}.md"
    spec_path.write_text(content)

    # Parse tasks: ### Task N: Title  or  ### N. Title  or  ### Title
    task_pattern = re.compile(
        r"^###\s+(?:Task\s+\d+[:.]\s*|(\d+)\.\s+)?(.+)",
        re.MULTILINE,
    )
    matches = list(task_pattern.finditer(content))

    task_num = 0
    prev_task_id = None
    created = []
    for m in matches:
        task_title = m.group(2).strip()
        if not task_title or task_title.lower().startswith("phase"):
            continue
        task_num += 1
        task_id = f"{epic_id}.{task_num}"

        # Extract content between this ### and the next ###
        start = m.end()
        next_match = task_pattern.search(content, start)
        end = next_match.start() if next_match else len(content)
        task_body = content[start:end].strip()

        deps = [prev_task_id] if prev_task_id and args.sequential else []

        state = {
            "id": task_id,
            "epic": epic_id,
            "title": task_title,
            "status": "todo",
            "depends_on": deps,
            "created": now_iso(),
        }
        save_task(TASKS_SUBDIR / f"{task_id}.json", state)

        task_spec = TASKS_SUBDIR / f"{task_id}.md"
        task_spec.write_text(f"# Task: {task_title}\n\n{task_body}\n")

        created.append(task_id)
        prev_task_id = task_id

    print(json.dumps({
        "success": True,
        "epic": epic_id,
        "tasks_created": len(created),
        "tasks": created,
    }))


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


def cmd_validate(args):
    """Validate epic/task structure — specs exist, deps valid, no cycles."""
    tasks = all_tasks()
    errors = []
    warnings = []

    # Check all epics have spec files
    for f in sorted(EPICS_DIR.glob("*.md")):
        epic_id = f.stem
        epic_tasks = [t for t in tasks.values() if t.get("epic") == epic_id]
        if not epic_tasks:
            warnings.append(f"Epic {epic_id} has no tasks")

    # Check all tasks have valid structure
    for tid, t in tasks.items():
        # Check epic exists
        epic_id = t.get("epic", "")
        epic_path = EPICS_DIR / f"{epic_id}.md"
        if not epic_path.exists():
            errors.append(f"Task {tid}: epic {epic_id} spec missing")

        # Check spec exists
        spec_path = TASKS_SUBDIR / f"{tid}.md"
        if not spec_path.exists():
            warnings.append(f"Task {tid}: spec file missing")

        # Check status valid
        if t.get("status") not in ("todo", "in_progress", "done", "blocked"):
            errors.append(f"Task {tid}: invalid status '{t.get('status')}'")

        # Check deps exist
        for dep in t.get("depends_on", []):
            if dep not in tasks:
                errors.append(f"Task {tid}: dependency {dep} not found")

    # Check for dependency cycles (DFS)
    def has_cycle(task_id, visited, rec_stack):
        visited.add(task_id)
        rec_stack.add(task_id)
        for dep in tasks.get(task_id, {}).get("depends_on", []):
            if dep not in visited:
                if has_cycle(dep, visited, rec_stack):
                    return True
            elif dep in rec_stack:
                errors.append(f"Dependency cycle detected involving {task_id} → {dep}")
                return True
        rec_stack.discard(task_id)
        return False

    visited, rec_stack = set(), set()
    for tid in tasks:
        if tid not in visited:
            has_cycle(tid, visited, rec_stack)

    valid = len(errors) == 0
    print(json.dumps({
        "success": valid,
        "valid": valid,
        "errors": errors,
        "warnings": warnings,
        "task_count": len(tasks),
    }))
    if not valid:
        sys.exit(1)


def cmd_epic_close(args):
    """Close epic — requires all tasks done."""
    epic_id = args.id
    epic_path = EPICS_DIR / f"{epic_id}.md"
    if not epic_path.exists():
        print(json.dumps({"success": False, "error": f"Epic not found: {epic_id}"}))
        sys.exit(1)

    tasks = all_tasks()
    epic_tasks = [t for t in tasks.values() if t.get("epic") == epic_id]
    not_done = [t for t in epic_tasks if t["status"] != "done"]
    if not_done:
        ids = [t["id"] for t in not_done]
        print(json.dumps({"success": False, "error": f"Cannot close: {len(not_done)} tasks not done", "pending": ids}))
        sys.exit(1)

    # Move epic and tasks to completed/
    completed_epic = COMPLETED_DIR / epic_path.name
    epic_path.rename(completed_epic)
    for t in epic_tasks:
        for ext in (".json", ".md"):
            src = TASKS_SUBDIR / f"{t['id']}{ext}"
            if src.exists():
                src.rename(COMPLETED_DIR / src.name)

    print(json.dumps({"success": True, "id": epic_id, "tasks_archived": len(epic_tasks)}))


def cmd_task_reset(args):
    """Reset task to todo, clearing started/completed/blocked fields."""
    path = TASKS_SUBDIR / f"{args.id}.json"
    if not path.exists():
        print(json.dumps({"success": False, "error": f"Task not found: {args.id}"}))
        sys.exit(1)

    data = json.loads(path.read_text())
    data["status"] = "todo"
    for field in ("started", "completed", "summary", "blocked_reason", "blocked_at"):
        data.pop(field, None)
    save_task(path, data)
    print(json.dumps({"success": True, "id": args.id, "status": "todo"}))


def cmd_scan(args):
    """Scan codebase for issues, generate improvement epic + tasks."""
    import subprocess

    findings = {"P1": [], "P2": [], "P3": [], "P4": []}

    # Ruff scan
    try:
        result = subprocess.run(
            ["ruff", "check", ".", "--output-format", "json"],
            capture_output=True, text=True, timeout=30,
        )
        if result.stdout.strip():
            issues = json.loads(result.stdout)
            by_rule = {}
            for i in issues:
                by_rule.setdefault(i.get("code", "?"), []).append(i)
            for rule, items in sorted(by_rule.items(), key=lambda x: -len(x[1]))[:10]:
                findings["P3"].append(f"Fix {len(items)}x ruff {rule}: {items[0].get('message', '')}")
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    # Mypy scan
    try:
        result = subprocess.run(
            ["mypy", ".", "--no-error-summary"],
            capture_output=True, text=True, timeout=60,
        )
        for line in result.stdout.strip().split("\n")[:10]:
            if line.strip() and "error:" in line:
                findings["P2"].append(f"Fix mypy: {line.strip()}")
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    # Bandit scan
    try:
        result = subprocess.run(
            ["bandit", "-r", ".", "-f", "json", "-q"],
            capture_output=True, text=True, timeout=30,
        )
        if result.stdout.strip():
            data = json.loads(result.stdout)
            for r in data.get("results", [])[:10]:
                sev = r.get("issue_severity", "MEDIUM")
                priority = "P1" if sev in ("HIGH", "CRITICAL") else "P3"
                findings[priority].append(
                    f"[{sev}] {r.get('issue_text', '')} ({r.get('filename', '')}:{r.get('line_number', '')})"
                )
    except (FileNotFoundError, subprocess.TimeoutExpired, json.JSONDecodeError):
        pass

    # Count totals
    total = sum(len(v) for v in findings.values())

    if args.create_tasks and total > 0:
        # Auto-create epic + tasks
        cmd_init(argparse.Namespace())

        meta = load_meta()
        epic_num = meta["next_epic"]
        date_slug = datetime.now(timezone.utc).strftime("%Y%m%d")
        epic_id = f"epic-{epic_num}-scan-{date_slug}"
        meta["next_epic"] = epic_num + 1
        save_meta(meta)

        spec_lines = [f"# Epic: Code scan {date_slug}\n\n## Findings\n"]
        task_num = 0
        for priority in ("P1", "P2", "P3", "P4"):
            for finding in findings[priority]:
                task_num += 1
                task_id = f"{epic_id}.{task_num}"
                state = {
                    "id": task_id,
                    "epic": epic_id,
                    "title": f"[{priority}] {finding}",
                    "status": "todo",
                    "depends_on": [],
                    "priority": {"P1": 1, "P2": 2, "P3": 3, "P4": 4}[priority],
                    "created": now_iso(),
                }
                save_task(TASKS_SUBDIR / f"{task_id}.json", state)
                spec_path = TASKS_SUBDIR / f"{task_id}.md"
                spec_path.write_text(f"# Task: {finding}\n\n## Fix\n\n[Describe the fix]\n")
                spec_lines.append(f"- [{priority}] {finding}")

        epic_spec = EPICS_DIR / f"{epic_id}.md"
        epic_spec.write_text("\n".join(spec_lines) + "\n")

        print(json.dumps({
            "success": True,
            "epic": epic_id,
            "tasks_created": task_num,
            "findings": {k: len(v) for k, v in findings.items()},
        }))
    else:
        # Just report
        output = {"success": True, "total": total, "findings": {}}
        for priority in ("P1", "P2", "P3", "P4"):
            if findings[priority]:
                output["findings"][priority] = findings[priority]
        print(json.dumps(output))


LOG_FILE = Path("improvement-results.tsv")
LOG_HEADER = "timestamp\titeration\tmode\tarea\ttask_id\tdescription\tstatus\tfiles_changed\tdiff_lines\tduration_sec\tnotes\n"


def cmd_log(args):
    """Append entry to improvement-results.tsv or show recent entries."""
    if args.show:
        if not LOG_FILE.exists():
            print(json.dumps({"success": False, "error": "No log file found"}))
            sys.exit(1)
        lines = LOG_FILE.read_text().strip().split("\n")
        n = min(args.show, len(lines) - 1)  # Skip header
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

    # Append mode
    if not LOG_FILE.exists():
        LOG_FILE.write_text(LOG_HEADER)

    row = "\t".join([
        now_iso(),
        str(args.iteration or ""),
        args.mode or "",
        args.area or "",
        args.task_id or "",
        args.description or "",
        args.status or "",
        str(args.files or ""),
        str(args.diff_lines or ""),
        str(args.duration or ""),
        args.notes or "",
    ])
    with open(LOG_FILE, "a") as f:
        f.write(row + "\n")
    print(json.dumps({"success": True, "logged": args.status}))


def cmd_summary(_args):
    """Print session summary from improvement-results.tsv."""
    if not LOG_FILE.exists():
        print("No improvement-results.tsv found.")
        return

    lines = LOG_FILE.read_text().strip().split("\n")[1:]  # Skip header
    kept = sum(1 for l in lines if "KEPT" in l)
    discarded = sum(1 for l in lines if "DISCARDED" in l)
    skipped = sum(1 for l in lines if "SKIPPED" in l)
    total = len(lines)
    pct = int(kept / total * 100) if total > 0 else 0

    print(f"## Autoimmune Summary")
    print(f"| Metric | Value |")
    print(f"|--------|-------|")
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
        if "." not in f.stem.split("-", 2)[-1]:  # Epic md (no task dot notation)
            # Check if it looks like an epic (no dot in the id part)
            parts = f.stem.split(".")
            if len(parts) == 1:  # Epic file, not task
                epic_id = f.stem
                task_files = list(COMPLETED_DIR.glob(f"{epic_id}.*.json"))
                archived_epics.append({
                    "id": epic_id,
                    "tasks": len(task_files),
                })

    if not archived_epics:
        # Try listing all json files
        task_jsons = sorted(COMPLETED_DIR.glob("*.json"))
        tasks = []
        for f in task_jsons:
            d = json.loads(f.read_text())
            tasks.append({"id": d["id"], "title": d.get("title", ""), "completed": d.get("completed", "")})
        print(json.dumps({"success": True, "tasks": tasks, "count": len(tasks)}))
    else:
        print(json.dumps({"success": True, "archived": archived_epics, "count": len(archived_epics)}))


def cmd_stats(_args):
    """Productivity stats from improvement-results.tsv and .tasks/ history."""
    stats = {"epics": {}, "totals": {"kept": 0, "discarded": 0, "skipped": 0}}

    # From TSV log
    if LOG_FILE.exists():
        lines = LOG_FILE.read_text().strip().split("\n")[1:]
        for line in lines:
            parts = line.split("\t")
            if len(parts) < 7:
                continue
            status = parts[6]
            if status == "KEPT":
                stats["totals"]["kept"] += 1
            elif status == "DISCARDED":
                stats["totals"]["discarded"] += 1
            elif status == "SKIPPED":
                stats["totals"]["skipped"] += 1

    # From .tasks/
    tasks = all_tasks()
    epic_stats = {}
    for t in tasks.values():
        epic = t.get("epic", "unknown")
        if epic not in epic_stats:
            epic_stats[epic] = {"total": 0, "done": 0, "todo": 0, "in_progress": 0, "blocked": 0}
        epic_stats[epic]["total"] += 1
        epic_stats[epic][t["status"]] = epic_stats[epic].get(t["status"], 0) + 1

    # Calculate velocity
    done_tasks = [t for t in tasks.values() if t.get("completed")]
    if len(done_tasks) >= 2:
        times = sorted(t["completed"] for t in done_tasks)
        first = datetime.fromisoformat(times[0].replace("Z", "+00:00"))
        last = datetime.fromisoformat(times[-1].replace("Z", "+00:00"))
        hours = max((last - first).total_seconds() / 3600, 0.1)
        velocity = len(done_tasks) / hours
        stats["velocity"] = f"{velocity:.1f} tasks/hour"
    else:
        stats["velocity"] = "insufficient data"

    total_attempts = stats["totals"]["kept"] + stats["totals"]["discarded"]
    success_rate = int(stats["totals"]["kept"] / total_attempts * 100) if total_attempts > 0 else 0

    print(f"## Productivity Stats")
    print(f"| Metric | Value |")
    print(f"|--------|-------|")
    print(f"| Active epics | {len(epic_stats)} |")
    print(f"| Total tasks | {len(tasks)} |")
    print(f"| Done | {sum(e['done'] for e in epic_stats.values())} |")
    print(f"| Velocity | {stats['velocity']} |")
    if total_attempts > 0:
        print(f"| Autoimmune kept | {stats['totals']['kept']} |")
        print(f"| Autoimmune discarded | {stats['totals']['discarded']} |")
        print(f"| Success rate | {success_rate}% |")


def cmd_dep_add(args):
    """Add dependency to existing task."""
    path = TASKS_SUBDIR / f"{args.id}.json"
    if not path.exists():
        print(json.dumps({"success": False, "error": f"Task not found: {args.id}"}))
        sys.exit(1)

    dep_path = TASKS_SUBDIR / f"{args.dep}.json"
    if not dep_path.exists():
        print(json.dumps({"success": False, "error": f"Dependency not found: {args.dep}"}))
        sys.exit(1)

    data = json.loads(path.read_text())
    deps = data.get("depends_on", [])
    if args.dep not in deps:
        deps.append(args.dep)
        data["depends_on"] = deps
        save_task(path, data)
    print(json.dumps({"success": True, "id": args.id, "depends_on": deps}))


def main():
    parser = argparse.ArgumentParser(prog="cc-flow", description="cc-code task manager")
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

    sub.add_parser("status")
    sub.add_parser("validate")

    scan_p = sub.add_parser("scan")
    scan_p.add_argument("--create-tasks", action="store_true", default=False)

    log_p = sub.add_parser("log")
    log_p.add_argument("--show", type=int, default=0, help="Show last N entries")
    log_p.add_argument("--iteration", type=int, default=None)
    log_p.add_argument("--mode", default="")
    log_p.add_argument("--area", default="")
    log_p.add_argument("--task-id", default="")
    log_p.add_argument("--description", default="")
    log_p.add_argument("--status", default="")
    log_p.add_argument("--files", type=int, default=None)
    log_p.add_argument("--diff-lines", type=int, default=None)
    log_p.add_argument("--duration", type=int, default=None)
    log_p.add_argument("--notes", default="")

    sub.add_parser("summary")
    sub.add_parser("archive")
    sub.add_parser("stats")

    next_p = sub.add_parser("next")
    next_p.add_argument("--epic", default="")

    dep_p = sub.add_parser("dep")
    dep_sub = dep_p.add_subparsers(dest="dep_cmd")
    dep_add = dep_sub.add_parser("add")
    dep_add.add_argument("id")
    dep_add.add_argument("dep")

    epic_close = epic_sub.add_parser("close")
    epic_close.add_argument("id")

    epic_import = epic_sub.add_parser("import")
    epic_import.add_argument("--file", required=True)
    epic_import.add_argument("--sequential", action="store_true", default=False)

    task_reset = task_sub.add_parser("reset")
    task_reset.add_argument("id")

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
        "status": cmd_status,
        "validate": cmd_validate,
        "next": cmd_next,
        "scan": cmd_scan,
        "log": cmd_log,
        "summary": cmd_summary,
        "archive": cmd_archive,
        "stats": cmd_stats,
    }

    if args.command == "epic":
        ec = getattr(args, "epic_cmd", None)
        if ec == "create":
            cmd_epic_create(args)
        elif ec == "close":
            cmd_epic_close(args)
        elif ec == "import":
            cmd_epic_import(args)
        else:
            parser.print_help()
            sys.exit(1)
    elif args.command == "task":
        tc = getattr(args, "task_cmd", None)
        if tc == "create":
            cmd_task_create(args)
        elif tc == "reset":
            cmd_task_reset(args)
        else:
            parser.print_help()
            sys.exit(1)
    elif args.command == "dep" and getattr(args, "dep_cmd", None) == "add":
        cmd_dep_add(args)
    elif args.command in cmds:
        cmds[args.command](args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
