"""Health check — environment, tools, config, task integrity."""

import json
import os
import shutil
import subprocess as sp
import sys

from cc_flow.core import (
    CONFIG_FILE, EPICS_DIR, LEARNINGS_DIR, META_FILE, TASKS_DIR,
    all_tasks, load_meta, safe_json_load,
)


def cmd_doctor(args):
    """Health check — validate environment, tools, config, and task integrity."""
    checks = _run_checks()
    fmt = getattr(args, "format", "text") or "text"

    if fmt == "json":
        passed = sum(1 for c in checks if c["status"] == "pass")
        warned = sum(1 for c in checks if c["status"] == "warn")
        failed = sum(1 for c in checks if c["status"] == "fail")
        print(json.dumps({
            "success": failed == 0,
            "checks": checks,
            "summary": {"pass": passed, "warn": warned, "fail": failed},
        }))
    else:
        icons = {"pass": "✓", "warn": "⚠", "fail": "✗"}
        print("## cc-flow Doctor\n")
        for c in checks:
            icon = icons.get(c["status"], "?")
            print(f"  {icon} {c['name']}: {c['message']}")
            if c.get("fix"):
                print(f"    → fix: {c['fix']}")
        passed = sum(1 for c in checks if c["status"] == "pass")
        print(f"\n  {passed}/{len(checks)} checks passed")

    if any(c["status"] == "fail" for c in checks):
        sys.exit(1)


def _run_checks():
    """Run all health checks, return list of results."""
    checks = []

    def chk(name, status, msg, fix=None):
        checks.append({"name": name, "status": status, "message": msg, "fix": fix})

    # Python
    v = sys.version_info
    if v >= (3, 9):
        chk("Python", "pass", f"{v.major}.{v.minor}.{v.micro}")
    elif v >= (3, 7):
        chk("Python", "warn", f"{v.major}.{v.minor} (3.9+ recommended)", "brew install python@3.12")
    else:
        chk("Python", "fail", f"{v.major}.{v.minor} (3.9+ required)", "brew install python@3.12")

    # Git
    if shutil.which("git"):
        try:
            ver = sp.run(["git", "--version"], capture_output=True, text=True, timeout=5).stdout.strip()
            chk("Git", "pass", ver)
            result = sp.run(["git", "rev-parse", "--is-inside-work-tree"],
                            capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                branch = sp.run(["git", "branch", "--show-current"],
                                capture_output=True, text=True, timeout=5).stdout.strip()
                chk("Git repo", "pass", f"branch: {branch}" if branch else "detached HEAD")
            else:
                chk("Git repo", "warn", "not a git repo", "git init")
        except (sp.TimeoutExpired, OSError):
            chk("Git", "warn", "git found but not responding")
    else:
        chk("Git", "fail", "git not found", "brew install git")

    # Lint tools
    for tool, pkg in [("ruff", "pip install ruff"), ("mypy", "pip install mypy")]:
        chk(tool, "pass" if shutil.which(tool) else "warn",
            "available" if shutil.which(tool) else "not installed",
            None if shutil.which(tool) else pkg)

    # .tasks/
    if TASKS_DIR.exists() and META_FILE.exists():
        chk(".tasks/", "pass", f"initialized (next_epic={load_meta().get('next_epic', '?')})")
    elif TASKS_DIR.exists():
        chk(".tasks/", "warn", "meta.json missing", "cc-flow init")
    else:
        chk(".tasks/", "warn", "not initialized", "cc-flow init")

    # Task integrity
    tasks = all_tasks()
    if tasks:
        orphaned = sum(1 for t in tasks.values() if not (EPICS_DIR / f"{t.get('epic', '')}.md").exists())
        broken = sum(1 for t in tasks.values() for d in t.get("depends_on", []) if d not in tasks)
        if orphaned == 0 and broken == 0:
            chk("Task integrity", "pass", f"{len(tasks)} tasks, all clean")
        else:
            parts = ([f"{orphaned} orphaned"] if orphaned else []) + ([f"{broken} broken deps"] if broken else [])
            chk("Task integrity", "warn", ", ".join(parts), "cc-flow validate")
    else:
        chk("Task integrity", "pass", "no tasks yet")

    # Learnings
    if LEARNINGS_DIR.exists():
        count = len(list(LEARNINGS_DIR.glob("*.json")))
        patterns_dir = TASKS_DIR / "patterns"
        patterns = len(list(patterns_dir.glob("*.json"))) if patterns_dir.exists() else 0
        chk("Learnings", "pass", f"{count} learnings, {patterns} patterns")
        if count >= 20 and patterns == 0:
            chk("Consolidation", "warn", f"{count} not consolidated", "cc-flow consolidate")
    else:
        chk("Learnings", "pass", "none yet")

    # Config + Claude Code
    if CONFIG_FILE.exists():
        chk("Config", "pass", f"{len(safe_json_load(CONFIG_FILE, default={}))} settings")
    else:
        chk("Config", "pass", "defaults")

    in_claude = bool(os.environ.get("CLAUDE_CODE") or os.environ.get("CLAUDE_PROJECT_DIR")
                     or os.environ.get("CLAUDE_PLUGIN_ROOT"))
    chk("Claude Code", "pass" if in_claude else "warn",
        "detected" if in_claude else "standalone mode")

    return checks
