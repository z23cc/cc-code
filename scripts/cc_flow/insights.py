"""cc-flow insights — forecast, evolve, health score.

Predictive analytics and meta-learning from project history.
"""

import json
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path

from cc_flow.core import (
    LEARNINGS_DIR,
    TASKS_DIR,
    all_tasks,
    error,
    now_iso,
    safe_json_load,
)

# ── Forecast ──

def cmd_forecast(args):
    """Predict epic completion date based on historical velocity."""
    epic_id = getattr(args, "epic", "") or ""
    tasks = all_tasks()

    if epic_id:
        epic_tasks = {tid: t for tid, t in tasks.items() if t.get("epic") == epic_id}
        if not epic_tasks:
            error(f"No tasks in epic: {epic_id}")
    else:
        epic_tasks = tasks

    done = [t for t in epic_tasks.values() if t["status"] == "done" and t.get("completed")]
    remaining = sum(1 for t in epic_tasks.values() if t["status"] in ("todo", "in_progress"))

    if len(done) < 2:
        print(json.dumps({"success": True, "forecast": None,
                          "reason": "Need at least 2 completed tasks for forecasting"}))
        return

    # Calculate velocity (tasks per hour)
    times = sorted(t["completed"] for t in done)
    first = datetime.fromisoformat(times[0].replace("Z", "+00:00"))
    last = datetime.fromisoformat(times[-1].replace("Z", "+00:00"))
    hours = max((last - first).total_seconds() / 3600, 0.1)
    velocity = len(done) / hours

    # Estimate remaining time
    if velocity > 0 and remaining > 0:
        hours_remaining = remaining / velocity
        eta = datetime.now(timezone.utc) + timedelta(hours=hours_remaining)
        eta_str = eta.strftime("%Y-%m-%d %H:%M UTC")
    elif remaining == 0:
        eta_str = "already complete"
        hours_remaining = 0
    else:
        eta_str = "unknown"
        hours_remaining = -1

    # Confidence based on sample size
    confidence = min(95, len(done) * 10)

    print(json.dumps({
        "success": True,
        "epic": epic_id or "all",
        "done": len(done),
        "remaining": remaining,
        "velocity": round(velocity, 2),
        "eta": eta_str,
        "hours_remaining": round(hours_remaining, 1),
        "confidence": confidence,
    }))


# ── Evolve ──

def _analyze_q_history():
    """Analyze Q-table for category strengths/weaknesses."""
    qtable_file = TASKS_DIR / "qtable.json"
    if not qtable_file.exists():
        return {}
    qtable = safe_json_load(qtable_file, default={})
    analysis = {}
    for category, commands in qtable.items():
        if not commands:
            continue
        best = max(commands, key=commands.get)
        worst = min(commands, key=commands.get)
        analysis[category] = {
            "best_command": best, "best_q": round(commands[best], 3),
            "worst_command": worst, "worst_q": round(commands[worst], 3),
            "total_commands": len(commands),
        }
    return analysis


def _analyze_scan_trend():
    """Get scan history trend."""
    scan_file = TASKS_DIR / "scan_history.json"
    if not scan_file.exists():
        return None
    data = safe_json_load(scan_file, default={})
    scans = data.get("scans", [])
    if len(scans) < 2:
        return None
    recent = scans[-3:]
    counts = [s["findings"] for s in recent]
    if counts[-1] < counts[0]:
        trend = "improving"
    elif counts[-1] > counts[0]:
        trend = "declining"
    else:
        trend = "stable"
    return {"trend": trend, "recent_counts": counts, "total_scans": len(scans)}


def _check_blocked(tasks):
    """Check for blocked tasks."""
    blocked = [t for t in tasks.values() if t["status"] == "blocked"]
    if blocked:
        return {"priority": 1, "area": "blocked_tasks",
                "action": f"{len(blocked)} blocked tasks need attention",
                "tasks": [t["id"] for t in blocked[:5]]}
    return None


def _check_test_ratio():
    """Check test-to-module ratio."""
    try:
        result = subprocess.run(["python3", "-m", "pytest", "--co", "-q"],
                                check=False, capture_output=True, text=True, timeout=15)
        test_count = result.stdout.strip().count("\n") if result.stdout else 0
        module_count = len(list(Path("scripts/cc_flow").glob("*.py")))
        ratio = test_count / module_count if module_count > 0 else 0
        if ratio < 5:
            return {"priority": 2, "area": "test_coverage",
                    "action": f"Low test ratio ({test_count} tests / {module_count} modules = {ratio:.1f}x)"}
    except (subprocess.TimeoutExpired, OSError):
        pass
    return None


def cmd_evolve(_args):
    """Meta-learning: analyze history and recommend next improvement focus."""
    tasks = all_tasks()
    recommendations = []

    scan_trend = _analyze_scan_trend()
    if scan_trend:
        if scan_trend["trend"] == "declining":
            recommendations.append({
                "priority": 1, "area": "code_quality",
                "action": "Run cc-flow auto deep — findings increasing",
                "data": scan_trend,
            })
        elif scan_trend["trend"] == "improving":
            recommendations.append({
                "priority": 3, "area": "code_quality",
                "action": "Quality improving — consider enabling stricter rules",
                "data": scan_trend,
            })

    # 2. Check Q-learning insights
    q_analysis = _analyze_q_history()
    for cat, info in q_analysis.items():
        if info["worst_q"] < -0.3:
            recommendations.append({
                "priority": 2, "area": f"routing:{cat}",
                "action": f"'{info['worst_command']}' has low success for {cat} tasks — try different approach",
            })

    # 3. Check blocked tasks
    blocked_rec = _check_blocked(tasks)
    if blocked_rec:
        recommendations.append(blocked_rec)

    # 4. Check learnings consolidation
    if LEARNINGS_DIR.exists():
        learn_count = len(list(LEARNINGS_DIR.glob("*.json")))
        patterns_dir = TASKS_DIR / "patterns"
        pattern_count = len(list(patterns_dir.glob("*.json"))) if patterns_dir.exists() else 0
        if learn_count >= 15 and pattern_count == 0:
            recommendations.append({
                "priority": 2, "area": "learnings",
                "action": f"{learn_count} learnings not consolidated — run cc-flow consolidate",
            })

    # 5. Check test ratio
    test_rec = _check_test_ratio()
    if test_rec:
        recommendations.append(test_rec)

    recommendations.sort(key=lambda r: r["priority"])

    print(json.dumps({
        "success": True,
        "recommendations": recommendations,
        "total": len(recommendations),
        "q_learning": q_analysis if q_analysis else None,
        "scan_trend": scan_trend,
        "generated": now_iso(),
    }))


# ── Health Score ──

def _score_lint():
    """Lint health score (0-25)."""
    try:
        result = subprocess.run(["ruff", "check", ".", "--output-format", "json"],
                                check=False, capture_output=True, text=True, timeout=15)
        if result.returncode == 0:
            return 25
        violations = len(json.loads(result.stdout)) if result.stdout.strip() else 0
        return max(0, 25 - violations)
    except (subprocess.TimeoutExpired, OSError, json.JSONDecodeError):
        return 0


def _score_tests():
    """Test health score (0-25)."""
    import re
    try:
        result = subprocess.run(["python3", "-m", "pytest", "--tb=no", "-q"],
                                check=False, capture_output=True, text=True, timeout=120)
        if result.returncode == 0:
            return 25
        last = result.stdout.strip().split("\n")[-1] if result.stdout else ""
        if "passed" in last:
            m = re.search(r"(\d+) passed", last)
            f = re.search(r"(\d+) failed", last)
            passed = int(m.group(1)) if m else 0
            failed = int(f.group(1)) if f else 0
            total = passed + failed
            return int(25 * passed / total) if total > 0 else 0
    except (subprocess.TimeoutExpired, OSError):
        pass
    return 0


def _score_architecture():
    """Architecture health score (0-25). Returns (score, file_count)."""
    large_files = 0
    total_files = 0
    for py in Path("scripts/cc_flow").glob("*.py"):
        if py.name.startswith("_"):
            continue
        total_files += 1
        if len(py.read_text().split("\n")) > 400:
            large_files += 1
    return max(0, 25 - large_files * 5), total_files


def _score_documentation():
    """Documentation health score (0-25)."""
    import ast
    doc_score = sum(5 for f in ("README.md", "CHANGELOG.md", "CLAUDE.md") if Path(f).exists())
    missing_docs = 0
    for py in Path("scripts/cc_flow").glob("*.py"):
        if py.name.startswith("_"):
            continue
        try:
            tree = ast.parse(py.read_text())
            missing_docs += sum(
                1 for n in ast.walk(tree)
                if isinstance(n, ast.FunctionDef) and not n.name.startswith("_") and not ast.get_docstring(n)
            )
        except SyntaxError:
            continue
    return min(25, doc_score + max(0, 10 - missing_docs))


def cmd_health(_args):
    """Calculate composite project health score (0-100)."""
    arch_score, total_files = _score_architecture()
    scores = {
        "lint": _score_lint(),
        "tests": _score_tests(),
        "architecture": arch_score,
        "documentation": _score_documentation(),
    }
    total = sum(scores.values())
    grade = "A" if total >= 90 else "B" if total >= 75 else "C" if total >= 60 else "D" if total >= 40 else "F"

    print(json.dumps({
        "success": True, "score": total, "max": 100, "grade": grade,
        "breakdown": scores, "files": total_files,
    }))
