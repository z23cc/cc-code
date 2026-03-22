"""cc-flow auto commands — OODA-loop autonomous improvement.

All status messages go to stderr, all data goes to stdout as JSON.

v2 architecture:
  OBSERVE: multi-dimensional scan (lint + architecture + tests + docs + deps)
  ORIENT:  Q-learning adaptive priority + trend analysis
  DECIDE:  generate proposals ranked by ROI
  ACT:     implement, verify, learn
  LOOP:    track effect, update Q-table, continue or stop
"""

import argparse
import json
import sys as _sys

from cc_flow.core import (
    EPICS_DIR,
    LOG_FILE,
    TASKS_SUBDIR,
    all_tasks,
    error,
    get_morph_client,
    now_iso,
    save_task,
)
from cc_flow.quality import cmd_scan


def _log(msg):
    """Log status to stderr (keeps stdout clean for JSON)."""
    _sys.stderr.write(f"cc-flow: {msg}\n")

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
        "keywords": ["test", "pytest", "failing", "assert", "fixture", "coverage", "no_test"],
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
        "keywords": ["refactor", "extract", "duplicate", "simplify", "complexity", "dead code",
                     "large_file", "many_functions", "duplication"],
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
        "keywords": ["doc", "docstring", "readme", "comment", "missing_docstrings"],
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
    """Integrated autoimmune loop using OODA pattern."""
    mode = getattr(args, "auto_cmd", None)
    if mode == "scan":
        _auto_scan(args)
    elif mode == "run":
        _auto_run(args)
    elif mode == "test":
        _auto_test(args)
    elif mode == "full":
        _log("Mode: Full (observe → orient → decide → act)")
        _auto_scan(args)
        _auto_run(args)
        _auto_test(args)
    elif mode == "status":
        _auto_status(args)
    elif mode == "deep":
        _auto_deep_scan(args)
    else:
        error("Usage: cc-flow auto [scan|run|test|full|deep|status]")


def _auto_scan(args):
    """OBSERVE: lint scan + create tasks."""
    _log("OBSERVE: scanning with lint tools...")
    scan_args = argparse.Namespace(create_tasks=True)
    cmd_scan(scan_args)


def _auto_deep_scan(args):
    """OBSERVE+ORIENT: multi-dimensional scan with Morph-enhanced analysis."""
    from cc_flow.scanner import get_scan_trend, record_scan_snapshot, run_smart_scan

    _log("OBSERVE: deep multi-dimensional scan...")

    # Run all smart scanners (uses Morph embed for duplication if available)
    findings = run_smart_scan()

    # Also run standard lint scan
    _log("Running lint scan...")
    scan_args = argparse.Namespace(create_tasks=False)
    cmd_scan(scan_args)

    # Morph-enhanced: use Search to find code patterns worth improving
    morph_insights = _morph_research_scan()
    if morph_insights:
        findings["morph_insights"] = morph_insights

    # Count total findings
    total = sum(len(v) for v in findings.values())
    record_scan_snapshot(total)
    trend = get_scan_trend()

    # ORIENT: apply Q-learning priority adjustment + Morph rerank
    prioritized = _orient_findings(findings)
    prioritized = _morph_rerank_findings(prioritized)

    print(json.dumps({
        "success": True,
        "scan_type": "deep",
        "morph_enhanced": morph_insights is not None,
        "findings": {k: len(v) for k, v in findings.items()},
        "total": total,
        "trend": trend,
        "prioritized": prioritized[:10],
        "instruction": "Run 'cc-flow auto run' to start fixing, or review findings first.",
    }))


def _morph_search_query(client, query):
    """Run a single Morph search query, return finding or None."""
    try:
        result = client.search(query, ".")
        if result and isinstance(result, str) and len(result.strip()) > 10:
            matches = [ln.strip() for ln in result.split("\n") if ln.strip()][:3]
            if matches:
                return {
                    "type": "morph_search", "severity": "P4",
                    "message": f"Morph found '{query}' patterns: {len(matches)} hits",
                    "query": query, "sample": matches[0][:100],
                }
    except (RuntimeError, TimeoutError, OSError, KeyError, ValueError):
        pass
    return None


def _morph_research_scan():
    """Use Morph Search to find patterns worth improving."""
    client = get_morph_client()
    if not client:
        return None

    queries = ["TODO fixme hack", "error handling missing", "hardcoded config"]
    insights = [r for q in queries if (r := _morph_search_query(client, q))]
    return insights if insights else None


def _morph_rerank_findings(prioritized):
    """Use Morph Rerank to sort findings by relevance to project goals."""
    client = get_morph_client()
    if not client or len(prioritized) < 3:
        return prioritized

    try:
        documents = [f["message"] for f in prioritized[:15]]
        ranked = client.rerank("most impactful improvement for code quality", documents, top_n=10)
        if ranked:
            reordered = []
            for r in ranked:
                idx = r.get("index", 0)
                if idx < len(prioritized):
                    item = prioritized[idx].copy()
                    item["rerank_score"] = round(r.get("relevance_score", 0), 3)
                    reordered.append(item)
            return reordered
    except (RuntimeError, TimeoutError, OSError, KeyError, ValueError):
        pass

    return prioritized


def _orient_findings(findings):
    """ORIENT: rank findings by estimated ROI using Q-learning data."""
    try:
        from cc_flow.qrouter import _load_qtable
        qtable = _load_qtable()
    except ImportError:
        qtable = {}

    # Severity weights
    severity_weight = {"P1": 4, "P2": 3, "P3": 2, "P4": 1}

    prioritized = []
    for category, items in findings.items():
        for item in items:
            sev = item.get("severity", "P4")
            base_score = severity_weight.get(sev, 1)

            # Q-learning boost: if this type was successfully fixed before, boost priority
            q_boost = 0
            item_type = item.get("type", "")
            for cat_key, q_values in qtable.items():
                if item_type in cat_key or category in cat_key:
                    best_q = max(q_values.values()) if q_values else 0
                    q_boost = max(q_boost, best_q)

            final_score = base_score + q_boost
            prioritized.append({
                "category": category,
                "type": item.get("type", ""),
                "message": item.get("message", ""),
                "severity": sev,
                "score": round(final_score, 2),
                "file": item.get("file", ""),
            })

    prioritized.sort(key=lambda x: -x["score"])
    return prioritized


def _find_auto_epic(explicit_epic=""):
    """Find the best epic to work on."""
    if explicit_epic:
        return explicit_epic
    scan_epics = [f.stem for f in sorted(EPICS_DIR.glob("epic-*-scan-*.md"))]
    if scan_epics:
        return scan_epics[-1]
    for f in sorted(EPICS_DIR.glob("*.md"), reverse=True):
        if any(t.get("epic") == f.stem and t["status"] == "todo" for t in all_tasks().values()):
            return f.stem
    return ""


def _find_ready_tasks(epic_filter):
    """Find todo tasks with satisfied deps, sorted by priority."""
    tasks = all_tasks()
    ready = [
        t for t in tasks.values()
        if t.get("epic") == epic_filter
        and t["status"] == "todo"
        and all(tasks.get(d, {}).get("status") == "done" for d in t.get("depends_on", []))
    ]
    ready.sort(key=lambda t: (t.get("priority", 999), t["id"]))
    return ready


def _recommend_team(task):
    """Recommend a team template based on task keywords."""
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


def _morph_research_context(title):
    """Use Morph Search to find related code for the task."""
    client = get_morph_client()
    if not client:
        return None
    try:
        result = client.search(title, ".")
        if result and isinstance(result, str):
            lines = [ln.strip() for ln in result.split("\n") if ln.strip()][:5]
            return "\n".join(lines) if lines else None
    except (RuntimeError, TimeoutError, OSError, KeyError, ValueError):
        return None


def _emit_task_instruction(task):
    """ACT: start task with Morph-enhanced context."""
    task_id = task["id"]
    task["status"] = "in_progress"
    task["started"] = now_iso()
    save_task(TASKS_SUBDIR / f"{task_id}.json", task)

    team_rec = _recommend_team(task)
    spec_path = TASKS_SUBDIR / f"{task_id}.md"
    spec_content = spec_path.read_text().strip() if spec_path.exists() else ""

    # Morph-enhanced: search for related code
    research = _morph_research_context(task.get("title", ""))

    output = {
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
    }
    if research:
        output["morph_context"] = research
    print(json.dumps(output))


def _auto_run(args):
    """DECIDE+ACT: pick next task, execute."""
    epic_filter = _find_auto_epic(getattr(args, "epic", "") or "")
    if not epic_filter:
        print(json.dumps({"success": True, "action": "none",
                          "reason": "No tasks to work on. Run: cc-flow auto scan"}))
        return

    max_iterations = getattr(args, "max", 0) or 20
    _log(f"DECIDE+ACT: epic={epic_filter}, max={max_iterations}")

    for iteration in range(1, max_iterations + 1):
        ready = _find_ready_tasks(epic_filter)
        if not ready:
            _log(f"All tasks done or blocked after {iteration - 1} iterations.")
            return

        _log(f"Iteration {iteration}: {ready[0]['id']} — {ready[0]['title']}")
        _emit_task_instruction(ready[0])
        return

    _log(f"Max iterations ({max_iterations}) reached.")


def _auto_test(args):
    """ACT: auto-fix lint/type/test errors."""
    import subprocess as sp

    _log("ACT: fixing lint + type + test errors...")

    result = sp.run(["ruff", "check", ".", "--fix"], check=False, capture_output=True, text=True)
    ruff_status = "clean" if result.returncode == 0 else result.stdout[:200]

    result = sp.run(["ruff", "check", "."], check=False, capture_output=True, text=True)
    remaining = result.stdout.strip().count("\n") + 1 if result.stdout.strip() else 0

    print(json.dumps({
        "action": "fix_remaining",
        "ruff": ruff_status,
        "remaining_issues": remaining,
        "instruction": "Run mypy and pytest. Fix any errors with minimal changes.",
    }))


def _auto_status(args):
    """LEARN: show session status with trend analysis."""
    tasks = all_tasks()
    total = len(tasks)
    done = sum(1 for t in tasks.values() if t["status"] == "done")
    in_prog = sum(1 for t in tasks.values() if t["status"] == "in_progress")
    blocked = sum(1 for t in tasks.values() if t["status"] == "blocked")
    todo = total - done - in_prog - blocked

    log_entries = 0
    kept = 0
    disc = 0
    if LOG_FILE.exists():
        lines = LOG_FILE.read_text().strip().split("\n")[1:]
        log_entries = len(lines)
        kept = sum(1 for row in lines if "KEPT" in row)
        disc = sum(1 for row in lines if "DISCARDED" in row)

    # Trend
    try:
        from cc_flow.scanner import get_scan_trend
        trend = get_scan_trend()
    except ImportError:
        trend = "unknown"

    # Q-learning stats
    try:
        from cc_flow.qrouter import q_stats
        q_data = q_stats()
    except ImportError:
        q_data = {}

    result = {
        "success": True,
        "tasks": {"total": total, "done": done, "in_progress": in_prog,
                  "blocked": blocked, "todo": todo},
        "trend": trend,
    }
    if log_entries > 0:
        pct = int(kept / (kept + disc) * 100) if (kept + disc) > 0 else 0
        result["autoimmune"] = {"kept": kept, "discarded": disc, "success_rate": pct}
    if q_data:
        result["q_learning"] = q_data

    print(json.dumps(result))
