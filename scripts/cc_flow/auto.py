"""cc-flow auto commands."""

import argparse
import json
import sys

from cc_flow.core import (
    EPICS_DIR,
    LOG_FILE,
    TASKS_SUBDIR,
    all_tasks,
    get_morph_client,
    now_iso,
    save_task,
)
from cc_flow.quality import cmd_scan  # cross-module dependency

TEAM_PATTERNS = [
    {
        "keywords": ["security", "bandit", "injection", "xss", "csrf", "auth", "secret", "vulnerability"],
        "template": "security-fix",
        "agents": ["researcher", "security-reviewer", "build-fixer"],
        "steps": [
            "Dispatch researcher: investigate the security issue, find affected code",
            "Dispatch security-reviewer: verify the vulnerability and suggest fix",
            "Apply minimal fix, run bandit to confirm resolved",
        ],
        "max_diff": 30,
    },
    {
        "keywords": ["type", "mypy", "annotation", "hint", "typing"],
        "template": "type-fix",
        "agents": ["build-fixer"],
        "steps": [
            "Read the mypy error message carefully",
            "Add type annotation or fix type mismatch (minimal change)",
            "Run mypy to verify the error is resolved",
        ],
        "max_diff": 20,
    },
    {
        "keywords": ["lint", "ruff", "unused", "import", "F401", "F841", "E741"],
        "template": "lint-fix",
        "agents": ["refactor-cleaner"],
        "steps": [
            "Run ruff check to see the exact violation",
            "Apply minimal fix (remove unused import, rename variable, etc.)",
            "Run ruff check to verify clean",
        ],
        "max_diff": 10,
    },
    {
        "keywords": ["test", "pytest", "failing", "assert", "fixture"],
        "template": "test-fix",
        "agents": ["researcher", "build-fixer"],
        "steps": [
            "Dispatch researcher: read the failing test + code under test",
            "Determine if it's a test bug or code bug",
            "Fix minimally, run pytest to verify green",
        ],
        "max_diff": 30,
    },
    {
        "keywords": ["refactor", "extract", "duplicate", "simplify", "complexity", "dead code"],
        "template": "refactor",
        "agents": ["researcher", "refactor-cleaner", "code-reviewer"],
        "steps": [
            "Dispatch researcher: map all usages and dependents",
            "Dispatch refactor-cleaner: apply the refactoring",
            "Dispatch code-reviewer: verify behavior preserved",
        ],
        "max_diff": 50,
    },
    {
        "keywords": ["doc", "docstring", "readme", "comment"],
        "template": "docs",
        "agents": ["refactor-cleaner"],
        "steps": [
            "Read the code to understand what it does",
            "Add/update documentation (docstring, comment, README)",
            "Verify no code changes, only docs",
        ],
        "max_diff": 30,
    },
]


DEFAULT_TEAM = {
    "template": "general-fix",
    "agents": ["researcher", "build-fixer"],
    "steps": [
        "Dispatch researcher: understand the issue and affected code",
        "Apply minimal fix (< 50 lines diff)",
        "Verify with lint + tests",
    ],
    "max_diff": 50,
}


def cmd_auto(args):
    """Integrated autoimmune loop using cc-flow task system."""
    mode = getattr(args, "auto_cmd", None)
    if mode == "scan":
        _auto_scan(args)
    elif mode == "run":
        _auto_run(args)
    elif mode == "test":
        _auto_test(args)
    elif mode == "full":
        print("## Mode: Full (scan → run → test)")
        _auto_scan(args)
        _auto_run(args)
        _auto_test(args)
    elif mode == "status":
        _auto_status(args)
    else:
        print(json.dumps({"success": False, "error": "Usage: cc-flow auto [scan|run|test|full|status]"}))
        sys.exit(1)


def _auto_scan(args):
    """Mode D: scan codebase, create epic + tasks."""
    print("## Auto Scan: detecting issues...")
    # Use existing scan with --create-tasks
    scan_args = argparse.Namespace(create_tasks=True)
    cmd_scan(scan_args)


def _auto_run(args):
    """Mode A: pick tasks, implement, verify, mark done/discarded."""
    epic_filter = getattr(args, "epic", "") or ""

    # Find the latest scan epic if no filter
    if not epic_filter:
        tasks = all_tasks()
        scan_epics = [f.stem for f in sorted(EPICS_DIR.glob("epic-*-scan-*.md"))]
        if scan_epics:
            epic_filter = scan_epics[-1]

    if not epic_filter:
        # Fall back to any epic with todo tasks
        for f in sorted(EPICS_DIR.glob("*.md"), reverse=True):
            epic_tasks = [t for t in all_tasks().values() if t.get("epic") == f.stem and t["status"] == "todo"]
            if epic_tasks:
                epic_filter = f.stem
                break

    if not epic_filter:
        print(json.dumps({"success": True, "action": "none", "reason": "No tasks to work on. Run: cc-flow auto scan"}))
        return

    max_iterations = getattr(args, "max", 0) or 20
    iteration = 0
    kept = 0
    discarded = 0

    print(f"## Auto Run: epic={epic_filter}, max={max_iterations}")

    while iteration < max_iterations:
        # Find next ready task
        tasks = all_tasks()
        ready = []
        for t in tasks.values():
            if t.get("epic") != epic_filter:
                continue
            if t["status"] != "todo":
                continue
            deps_done = all(tasks.get(d, {}).get("status") == "done" for d in t.get("depends_on", []))
            if deps_done:
                ready.append(t)

        if not ready:
            print(f"\n✅ All tasks done or blocked. Iterations: {iteration}, kept: {kept}, discarded: {discarded}")
            break

        ready.sort(key=lambda t: (t.get("priority", 999), t["id"]))
        task = ready[0]
        task_id = task["id"]
        iteration += 1

        print(f"\n--- Iteration {iteration}: {task_id} — {task['title']} ---")

        # Start task
        task["status"] = "in_progress"
        task["started"] = now_iso()
        save_task(TASKS_SUBDIR / f"{task_id}.json", task)

        # Determine team based on task content
        team_rec = _recommend_team(task)

        # Read spec content for context
        spec_path = TASKS_SUBDIR / f"{task_id}.md"
        spec_content = spec_path.read_text().strip() if spec_path.exists() else ""

        # Output structured instruction for Claude
        print(json.dumps({
            "action": "implement",
            "task_id": task_id,
            "title": task["title"],
            "size": task.get("size", "M"),
            "spec": str(spec_path),
            "spec_preview": spec_content[:200] if spec_content else "",
            "team": team_rec,
            "instruction": (
                f"Execute this task using the {team_rec['template']} team pattern:\n"
                f"1. {team_rec['steps'][0]}\n"
                f"2. {team_rec['steps'][1]}\n"
                f"3. {team_rec['steps'][2]}\n"
                f"Max diff: {team_rec['max_diff']} lines. Verify before marking done."
            ),
            "morph_available": get_morph_client() is not None,
            "morph_hint": "Use cc-flow apply for fast edits, cc-flow search for exploration.",
        }))

        # Return control to Claude for implementation
        break

    if iteration >= max_iterations:
        print(f"\n⏹ Max iterations ({max_iterations}) reached. Kept: {kept}, Discarded: {discarded}")


def _auto_test(args):
    """Mode B: auto-fix lint/type/test errors."""
    import subprocess as sp

    print("## Auto Test: fixing lint + type + test errors...")

    # Phase B1: ruff auto-fix
    result = sp.run(["ruff", "check", ".", "--fix"], capture_output=True, text=True)
    if result.returncode == 0:
        print("B1 ruff: clean (or auto-fixed)")
    else:
        print(f"B1 ruff: {result.stdout[:200]}")

    # Phase B2: Check for remaining issues
    result = sp.run(["ruff", "check", "."], capture_output=True, text=True)
    remaining = result.stdout.strip().count("\n") + 1 if result.stdout.strip() else 0
    print(f"B2 remaining ruff issues: {remaining}")

    # Note: mypy and pytest fixes require Claude's reasoning — print instructions
    print(json.dumps({
        "action": "fix_remaining",
        "instruction": "Run mypy and pytest. Fix any errors with minimal changes. Verify after each fix.",
    }))


def _auto_status(args):
    """Show autoimmune session status from cc-flow data."""
    tasks = all_tasks()
    total = len(tasks)
    done = sum(1 for t in tasks.values() if t["status"] == "done")
    in_prog = sum(1 for t in tasks.values() if t["status"] == "in_progress")
    blocked = sum(1 for t in tasks.values() if t["status"] == "blocked")
    todo = total - done - in_prog - blocked

    # Check log
    log_entries = 0
    kept = 0
    disc = 0
    if LOG_FILE.exists():
        lines = LOG_FILE.read_text().strip().split("\n")[1:]
        log_entries = len(lines)
        kept = sum(1 for row in lines if "KEPT" in row)
        disc = sum(1 for row in lines if "DISCARDED" in row)

    print("## Auto Status")
    print("| Metric | Value |")
    print("|--------|-------|")
    print(f"| Tasks total | {total} |")
    print(f"| Done | {done} |")
    print(f"| In progress | {in_prog} |")
    print(f"| Blocked | {blocked} |")
    print(f"| Todo | {todo} |")
    if log_entries > 0:
        pct = int(kept / (kept + disc) * 100) if (kept + disc) > 0 else 0
        print(f"| Log entries | {log_entries} |")
        print(f"| Kept | {kept} ({pct}%) |")
        print(f"| Discarded | {disc} |")


def _recommend_team(task):
    """Recommend a team template based on task title/content keywords."""
    title_lower = task.get("title", "").lower()

    for pattern in TEAM_PATTERNS:
        score = sum(1 for kw in pattern["keywords"] if kw in title_lower)
        if score > 0:
            return {
                "template": pattern["template"],
                "agents": pattern["agents"],
                "steps": pattern["steps"],
                "max_diff": pattern["max_diff"],
                "match_score": score,
            }

    return {
        "template": DEFAULT_TEAM["template"],
        "agents": DEFAULT_TEAM["agents"],
        "steps": DEFAULT_TEAM["steps"],
        "max_diff": DEFAULT_TEAM["max_diff"],
        "match_score": 0,
    }
