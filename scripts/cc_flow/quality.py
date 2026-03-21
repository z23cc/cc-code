"""cc-flow quality commands — validate, scan."""

import argparse
import json
import sys
from datetime import datetime, timezone

from cc_flow.core import (
    EPICS_DIR, TASKS_SUBDIR,
    all_tasks, load_meta, now_iso, save_meta, save_task,
)
from cc_flow.epic_task import cmd_init


def cmd_validate(args):
    """Validate epic/task structure — specs exist, deps valid, no cycles."""
    tasks = all_tasks()
    errors = []
    warnings = []

    for f in sorted(EPICS_DIR.glob("*.md")):
        epic_id = f.stem
        epic_tasks = [t for t in tasks.values() if t.get("epic") == epic_id]
        if not epic_tasks:
            warnings.append(f"Epic {epic_id} has no tasks")

    for tid, t in tasks.items():
        epic_path = EPICS_DIR / f"{t.get('epic', '')}.md"
        if not epic_path.exists():
            errors.append(f"Task {tid}: epic {t.get('epic', '')} spec missing")
        spec_path = TASKS_SUBDIR / f"{tid}.md"
        if not spec_path.exists():
            warnings.append(f"Task {tid}: spec file missing")
        if t.get("status") not in ("todo", "in_progress", "done", "blocked"):
            errors.append(f"Task {tid}: invalid status '{t.get('status')}'")
        for dep in t.get("depends_on", []):
            if dep not in tasks:
                errors.append(f"Task {tid}: dependency {dep} not found")

    def has_cycle(task_id, visited, rec_stack):
        visited.add(task_id)
        rec_stack.add(task_id)
        for dep in tasks.get(task_id, {}).get("depends_on", []):
            if dep not in visited:
                if has_cycle(dep, visited, rec_stack):
                    return True
            elif dep in rec_stack:
                errors.append(f"Dependency cycle: {task_id} → {dep}")
                return True
        rec_stack.discard(task_id)
        return False

    visited, rec_stack = set(), set()
    for tid in tasks:
        if tid not in visited:
            has_cycle(tid, visited, rec_stack)

    valid = len(errors) == 0
    print(json.dumps({"success": valid, "valid": valid, "errors": errors,
                       "warnings": warnings, "task_count": len(tasks)}))
    if not valid:
        sys.exit(1)


def cmd_scan(args):
    """Scan codebase for issues, generate improvement epic + tasks."""
    import subprocess

    findings = {"P1": [], "P2": [], "P3": [], "P4": []}

    # Ruff
    try:
        result = subprocess.run(["ruff", "check", ".", "--output-format", "json"],
                                capture_output=True, text=True, timeout=30)
        if result.stdout.strip():
            issues = json.loads(result.stdout)
            by_rule = {}
            for i in issues:
                by_rule.setdefault(i.get("code", "?"), []).append(i)
            for rule, items in sorted(by_rule.items(), key=lambda x: -len(x[1]))[:10]:
                findings["P3"].append(f"Fix {len(items)}x ruff {rule}: {items[0].get('message', '')}")
    except (FileNotFoundError, subprocess.TimeoutExpired, json.JSONDecodeError):
        pass

    # Mypy
    try:
        result = subprocess.run(["mypy", ".", "--no-error-summary"],
                                capture_output=True, text=True, timeout=60)
        for line in result.stdout.strip().split("\n")[:10]:
            if line.strip() and "error:" in line:
                findings["P2"].append(f"Fix mypy: {line.strip()}")
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    # Bandit
    try:
        result = subprocess.run(["bandit", "-r", ".", "-f", "json", "-q"],
                                capture_output=True, text=True, timeout=30)
        if result.stdout.strip():
            data = json.loads(result.stdout)
            for r in data.get("results", [])[:10]:
                sev = r.get("issue_severity", "MEDIUM")
                priority = "P1" if sev in ("HIGH", "CRITICAL") else "P3"
                findings[priority].append(
                    f"[{sev}] {r.get('issue_text', '')} ({r.get('filename', '')}:{r.get('line_number', '')})")
    except (FileNotFoundError, subprocess.TimeoutExpired, json.JSONDecodeError):
        pass

    total = sum(len(v) for v in findings.values())

    if args.create_tasks and total > 0:
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
                save_task(TASKS_SUBDIR / f"{task_id}.json", {
                    "id": task_id, "epic": epic_id, "title": f"[{priority}] {finding}",
                    "status": "todo", "depends_on": [],
                    "priority": {"P1": 1, "P2": 2, "P3": 3, "P4": 4}[priority],
                    "created": now_iso(),
                })
                (TASKS_SUBDIR / f"{task_id}.md").write_text(f"# Task: {finding}\n\n## Fix\n\n[Describe the fix]\n")
                spec_lines.append(f"- [{priority}] {finding}")

        (EPICS_DIR / f"{epic_id}.md").write_text("\n".join(spec_lines) + "\n")
        print(json.dumps({"success": True, "epic": epic_id, "tasks_created": task_num,
                          "findings": {k: len(v) for k, v in findings.items()}}))
    else:
        output = {"success": True, "total": total, "findings": {}}
        for p in ("P1", "P2", "P3", "P4"):
            if findings[p]:
                output["findings"][p] = findings[p]
        print(json.dumps(output))
