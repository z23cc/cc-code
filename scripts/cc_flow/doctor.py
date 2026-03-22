"""Health check — environment, tools, config, task integrity."""

import json
import os
import shutil
import subprocess as sp
import sys

from cc_flow.core import (
    CONFIG_FILE,
    EPICS_DIR,
    LEARNINGS_DIR,
    META_FILE,
    TASKS_DIR,
    all_tasks,
    load_meta,
    safe_json_load,
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
        from cc_flow import skin
        skin.heading("cc-flow Doctor")
        dispatch = {"pass": skin.success, "warn": skin.warning, "fail": skin.error}
        for c in checks:
            fn = dispatch.get(c["status"], skin.info)
            fn(f"{c['name']}: {c['message']}")
            if c.get("fix"):
                skin.dim(f"    fix: {c['fix']}")
        passed = sum(1 for c in checks if c["status"] == "pass")
        print()
        skin.info(f"{passed}/{len(checks)} checks passed")

    if any(c["status"] == "fail" for c in checks):
        sys.exit(1)


def _chk(name, status, msg, fix=None):
    """Build a single check result dict."""
    return {"name": name, "status": status, "message": msg, "fix": fix}


def _check_python():
    v = sys.version_info
    ver_str = f"{v.major}.{v.minor}.{v.micro}"
    if v >= (3, 9):
        return [_chk("Python", "pass", ver_str)]
    if v >= (3, 7):
        return [_chk("Python", "warn", f"{v.major}.{v.minor} (3.9+ recommended)", "brew install python@3.12")]
    return [_chk("Python", "fail", f"{v.major}.{v.minor} (3.9+ required)", "brew install python@3.12")]


def _check_git():
    if not shutil.which("git"):
        return [_chk("Git", "fail", "git not found", "brew install git")]
    try:
        ver = sp.run(["git", "--version"], check=False, capture_output=True, text=True, timeout=5).stdout.strip()
        results = [_chk("Git", "pass", ver)]
        result = sp.run(["git", "rev-parse", "--is-inside-work-tree"],
                        check=False, capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            branch = sp.run(["git", "branch", "--show-current"],
                            check=False, capture_output=True, text=True, timeout=5).stdout.strip()
            results.append(_chk("Git repo", "pass", f"branch: {branch}" if branch else "detached HEAD"))
        else:
            results.append(_chk("Git repo", "warn", "not a git repo", "git init"))
    except (sp.TimeoutExpired, OSError):
        return [_chk("Git", "warn", "git found but not responding")]
    else:
        return results


def _check_lint_tools():
    results = []
    for tool, pkg in [("ruff", "pip install ruff"), ("mypy", "pip install mypy")]:
        found = shutil.which(tool) is not None
        results.append(_chk(tool, "pass" if found else "warn",
                            "available" if found else "not installed",
                            None if found else pkg))
    return results


def _check_tasks_dir():
    results = []
    if TASKS_DIR.exists() and META_FILE.exists():
        results.append(_chk(".tasks/", "pass", f"initialized (next_epic={load_meta().get('next_epic', '?')})"))
    elif TASKS_DIR.exists():
        results.append(_chk(".tasks/", "warn", "meta.json missing", "cc-flow init"))
    else:
        results.append(_chk(".tasks/", "warn", "not initialized", "cc-flow init"))

    tasks = all_tasks()
    if not tasks:
        results.append(_chk("Task integrity", "pass", "no tasks yet"))
        return results

    orphaned = sum(1 for t in tasks.values() if not (EPICS_DIR / f"{t.get('epic', '')}.md").exists())
    broken = sum(1 for t in tasks.values() for d in t.get("depends_on", []) if d not in tasks)
    if orphaned == 0 and broken == 0:
        results.append(_chk("Task integrity", "pass", f"{len(tasks)} tasks, all clean"))
    else:
        parts = ([f"{orphaned} orphaned"] if orphaned else []) + ([f"{broken} broken deps"] if broken else [])
        results.append(_chk("Task integrity", "warn", ", ".join(parts), "cc-flow validate"))
    return results


def _check_learnings():
    if not LEARNINGS_DIR.exists():
        return [_chk("Learnings", "pass", "none yet")]
    count = len(list(LEARNINGS_DIR.glob("*.json")))
    patterns_dir = TASKS_DIR / "patterns"
    patterns = len(list(patterns_dir.glob("*.json"))) if patterns_dir.exists() else 0
    results = [_chk("Learnings", "pass", f"{count} learnings, {patterns} patterns")]
    if count >= 20 and patterns == 0:
        results.append(_chk("Consolidation", "warn", f"{count} not consolidated", "cc-flow consolidate"))
    return results


def _check_env():
    results = []
    if CONFIG_FILE.exists():
        results.append(_chk("Config", "pass", f"{len(safe_json_load(CONFIG_FILE, default={}))} settings"))
    else:
        results.append(_chk("Config", "pass", "defaults"))

    morph_key = os.environ.get("MORPH_API_KEY", "")
    if morph_key:
        results.append(_chk("Morph API", "pass", f"key set ({morph_key[:8]}...)"))
    else:
        results.append(_chk("Morph API", "warn", "MORPH_API_KEY not set (search/apply/embed disabled)",
                            "export MORPH_API_KEY=your_key"))

    in_claude = bool(os.environ.get("CLAUDE_CODE") or os.environ.get("CLAUDE_PROJECT_DIR")
                     or os.environ.get("CLAUDE_PLUGIN_ROOT"))
    results.append(_chk("Claude Code", "pass" if in_claude else "warn",
                        "detected" if in_claude else "standalone mode"))
    return results


def _run_checks():
    """Run all health checks, return list of results."""
    return (
        _check_python()
        + _check_git()
        + _check_lint_tools()
        + _check_tasks_dir()
        + _check_learnings()
        + _check_env()
    )
