"""cc-flow misc commands."""

import argparse
import json
import sys
from datetime import datetime, timezone

from cc_flow import VERSION
from cc_flow.epic_task import cmd_init  # cross-module: scan creates tasks
from cc_flow.core import (
    COMPLETED_DIR, CONFIG_FILE, DEFAULT_CONFIG, EPICS_DIR, LOG_FILE, TASKS_SUBDIR,
    all_tasks, load_meta, now_iso, safe_json_load, save_meta, save_task,
)


LOG_HEADER = "timestamp\titeration\tmode\tarea\ttask_id\tdescription\tstatus\tfiles_changed\tdiff_lines\tduration_sec\tnotes\n"


def cmd_version(_args):
    """Print cc-flow version."""
    print(json.dumps({"success": True, "version": VERSION}))


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
    except (FileNotFoundError, subprocess.TimeoutExpired, json.JSONDecodeError):
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
            d = safe_json_load(f, default=None)
            if not d or "id" not in d:
                continue
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

    print("## Productivity Stats")
    print("| Metric | Value |")
    print("|--------|-------|")
    print(f"| Active epics | {len(epic_stats)} |")
    print(f"| Total tasks | {len(tasks)} |")
    print(f"| Done | {sum(e['done'] for e in epic_stats.values())} |")
    print(f"| Velocity | {stats['velocity']} |")
    if total_attempts > 0:
        print(f"| Autoimmune kept | {stats['totals']['kept']} |")
        print(f"| Autoimmune discarded | {stats['totals']['discarded']} |")
        print(f"| Success rate | {success_rate}% |")


# ─── Router ───


def cmd_history(_args):
    """Show task completion timeline with velocity trends."""
    tasks = all_tasks()

    # Include archived tasks
    archived = []
    if COMPLETED_DIR.exists():
        for f in COMPLETED_DIR.glob("*.json"):
            try:
                archived.append(json.loads(f.read_text()))
            except json.JSONDecodeError:
                continue

    all_done = [t for t in list(tasks.values()) + archived if t.get("completed")]
    all_done.sort(key=lambda t: t.get("completed", ""))

    if not all_done:
        print(json.dumps({"success": True, "entries": [], "count": 0}))
        return

    # Group by date
    by_date = {}
    for t in all_done:
        date = t["completed"][:10]
        by_date.setdefault(date, []).append(t)

    # Calculate rolling velocity (tasks/day over last 7 entries)
    entries = []
    dates = sorted(by_date.keys())
    for date in dates:
        tasks_done = by_date[date]
        entries.append({
            "date": date,
            "count": len(tasks_done),
            "tasks": [{"id": t["id"], "title": t.get("title", "")} for t in tasks_done],
        })

    # Overall stats
    if len(dates) >= 2:
        first = datetime.fromisoformat(dates[0])
        last = datetime.fromisoformat(dates[-1])
        days = max((last - first).days, 1)
        daily_velocity = len(all_done) / days
    else:
        daily_velocity = len(all_done)

    print(json.dumps({
        "success": True,
        "entries": entries[-20:],  # Last 20 days
        "count": len(all_done),
        "daily_velocity": round(daily_velocity, 1),
        "date_range": f"{dates[0]} → {dates[-1]}" if len(dates) >= 2 else dates[0],
    }))


def cmd_config(args):
    """Manage cc-flow configuration."""
    config = DEFAULT_CONFIG.copy()
    if CONFIG_FILE.exists():
        config.update(safe_json_load(CONFIG_FILE, default={}))

    if args.key and args.value:
        # Set a config value
        # Auto-convert types
        val = args.value
        if val.lower() in ("true", "false"):
            val = val.lower() == "true"
        elif val.isdigit():
            val = int(val)
        config[args.key] = val
        CONFIG_FILE.write_text(json.dumps(config, indent=2) + "\n")
        print(json.dumps({"success": True, "key": args.key, "value": val}))
    elif args.key:
        # Get a config value
        print(json.dumps({"success": True, "key": args.key, "value": config.get(args.key)}))
    else:
        # Show all config
        print(json.dumps({"success": True, "config": config}))
