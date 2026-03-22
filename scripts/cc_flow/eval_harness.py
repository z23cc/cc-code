"""cc-flow eval harness — automated coding capability evaluation.

NOTE: 'eval' here means 'evaluation/benchmark', not Python eval().

Runs a suite of coding scenarios against cc-flow commands,
scores results, and identifies weaknesses for iterative improvement.

Eval dimensions:
  1. ROUTE   — does route suggest the right command?
  2. SEARCH  — can find/search locate relevant code?
  3. SPEED   — how fast are commands?
  4. HEALTH  — project health score integration

Each dimension returns a score 0-100 and diagnostic details.
"""

import json
import subprocess
import sys
import time

from cc_flow.core import TASKS_DIR, now_iso, safe_json_load

EVAL_RESULTS_FILE = TASKS_DIR / "eval_results.json"


def _run_cc(args_str, cwd=None, timeout=30):
    """Run a cc-flow command, return (stdout, stderr, returncode, elapsed_ms)."""
    cmd = [sys.executable, "-m", "cc_flow", *args_str.split()]
    start = time.monotonic()
    try:
        r = subprocess.run(cmd, check=False, capture_output=True, text=True,
                           cwd=cwd, timeout=timeout)
        elapsed = int((time.monotonic() - start) * 1000)
        return r.stdout.strip(), r.stderr.strip(), r.returncode, elapsed
    except subprocess.TimeoutExpired:
        return "", "timeout", 1, timeout * 1000


def _parse_json(stdout):
    """Try to parse JSON from stdout (handles multi-line output)."""
    for line in reversed(stdout.split("\n")):
        line = line.strip()
        if line.startswith("{"):
            try:
                return json.loads(line)
            except json.JSONDecodeError:
                continue
    return None


# ── Individual Evals ──

def eval_route():
    """Does route suggest the right command for different task types?"""
    cases = [
        ("fix login bug crash", "/debug"),
        ("add new feature user profile", "/brainstorm"),
        ("refactor auth module clean up", "/simplify"),
        ("review code quality check", "/review"),
    ]

    correct = 0
    details = []
    total_ms = 0

    for query, expected_cmd in cases:
        out, _, _, ms = _run_cc(f"route {query}")
        total_ms += ms
        data = _parse_json(out)
        if not data:
            details.append({"query": query, "result": "no output", "correct": False})
            continue

        suggested = data.get("suggestion", {}).get("command", "")
        is_correct = expected_cmd in suggested
        if is_correct:
            correct += 1
        details.append({
            "query": query, "expected": expected_cmd,
            "got": suggested, "correct": is_correct,
            "confidence": data.get("confidence", 0),
        })

    score = int(correct / len(cases) * 100) if cases else 0
    return {"score": score, "detail": details, "correct": correct,
            "total": len(cases), "ms": total_ms, "dimension": "route"}


def eval_search():
    """Can search locate relevant code? Tests both task search and code search."""
    # Ensure at least one task exists for task search test
    _run_cc("init")
    from cc_flow.core import all_tasks
    tasks = all_tasks()
    # Pick a word from an existing task title, or use a safe fallback
    task_word = ""
    for t in tasks.values():
        words = t.get("title", "").split()
        if len(words) >= 2:
            task_word = words[0]
            break

    cases = [
        # Code search (always works — searches source files)
        ("search atomic_write", True, "code"),
        ("search " + "z" * 40, False, "code"),
    ]
    # Task search (only if we have tasks with known content)
    if task_word:
        cases.insert(0, (f"find {task_word}", True, "task"))
    cases.append(("find " + "q" * 30, False, "task"))

    correct = 0
    details = []
    total_ms = 0

    for query, should_find, search_type in cases:
        out, _, _, ms = _run_cc(query)
        total_ms += ms
        data = _parse_json(out)
        if search_type == "task":
            if not data:
                details.append({"query": query, "result": "no output", "type": search_type})
                continue
            found = data.get("total", 0) > 0
        else:
            # code search: output may be text (grep) or JSON (morph)
            has_content = bool(out.strip())
            no_results = "No matches" in out or "0 results" in out or not has_content
            found = has_content and not no_results and "error" not in out.lower()
        is_correct = found == should_find
        if is_correct:
            correct += 1
        details.append({
            "query": query, "should_find": should_find, "type": search_type,
            "found": found, "correct": is_correct,
        })

    score = int(correct / len(cases) * 100) if cases else 0
    return {"score": score, "detail": details, "correct": correct,
            "total": len(cases), "ms": total_ms, "dimension": "search"}


def eval_speed():
    """Are key commands fast enough?"""
    benchmarks = {
        "version": 200,
        "status": 500,
        "doctor --format json": 2000,
    }

    results = []
    total_score = 0

    for cmd, max_ms in benchmarks.items():
        _, _, _, ms = _run_cc(cmd)
        passed = ms <= max_ms
        cmd_score = 100 if passed else max(0, int(100 * max_ms / ms))
        total_score += cmd_score
        results.append({"command": cmd, "ms": ms, "max_ms": max_ms, "passed": passed})

    score = total_score // len(benchmarks) if benchmarks else 0
    return {"score": score, "detail": results, "dimension": "speed"}


def eval_health():
    """Does the health command produce a valid score?"""
    out, _, code, ms = _run_cc("health", timeout=120)
    data = _parse_json(out)
    if not data or code != 0:
        return {"score": 0, "detail": "health command failed", "ms": ms, "dimension": "health"}

    return {
        "score": data.get("score", 0),
        "grade": data.get("grade", "F"),
        "breakdown": data.get("breakdown", {}),
        "ms": ms,
        "dimension": "health",
    }


# ── Eval Runner ──

ALL_EVALS = {
    "route": eval_route,
    "search": eval_search,
    "speed": eval_speed,
    "health": eval_health,
}


def _save_results(results):
    """Save results for trend tracking."""
    EVAL_RESULTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    history = safe_json_load(EVAL_RESULTS_FILE, default={"runs": []})
    history["runs"].append({"timestamp": now_iso(), "results": results})
    history["runs"] = history["runs"][-20:]
    EVAL_RESULTS_FILE.write_text(json.dumps(history, indent=2) + "\n")


def _get_trend():
    """Compare with last run."""
    history = safe_json_load(EVAL_RESULTS_FILE, default={"runs": []})
    runs = history.get("runs", [])
    if len(runs) < 2:
        return None
    prev = runs[-2]["results"]
    curr = runs[-1]["results"]
    prev_avg = sum(r.get("score", 0) for r in prev.values()) / len(prev) if prev else 0
    curr_avg = sum(r.get("score", 0) for r in curr.values()) / len(curr) if curr else 0
    if curr_avg > prev_avg + 2:
        return "improving"
    if curr_avg < prev_avg - 2:
        return "declining"
    return "stable"


def cmd_eval_run(args):
    """Run coding capability evaluation suite."""
    dimensions = getattr(args, "dimensions", "") or ""
    selected = dimensions.split(",") if dimensions else list(ALL_EVALS.keys())

    results = {}
    for name in selected:
        if name in ALL_EVALS:
            results[name] = ALL_EVALS[name]()

    _save_results(results)
    trend = _get_trend()

    scores = [r.get("score", 0) for r in results.values()]
    avg = sum(scores) // len(scores) if scores else 0
    grade = "A" if avg >= 90 else "B" if avg >= 75 else "C" if avg >= 60 else "D" if avg >= 40 else "F"

    weakest = min(results.items(), key=lambda x: x[1].get("score", 0)) if results else None

    print(json.dumps({
        "success": True,
        "overall": {"score": avg, "grade": grade},
        "results": {k: {"score": v["score"], "dimension": v["dimension"]}
                    for k, v in results.items()},
        "weakest": weakest[0] if weakest else None,
        "trend": trend,
        "recommendation": f"Focus on '{weakest[0]}' (score: {weakest[1]['score']})" if weakest else None,
    }))


def cmd_eval_detail(args):
    """Show detailed results for a dimension."""
    dimension = args.dimension
    if dimension not in ALL_EVALS:
        from cc_flow.core import error
        error(f"Unknown dimension: {dimension}. Available: {', '.join(ALL_EVALS.keys())}")

    result = ALL_EVALS[dimension]()
    print(json.dumps({"success": True, **result}))


def cmd_eval_history(_args):
    """Show score history and trends."""
    history = safe_json_load(EVAL_RESULTS_FILE, default={"runs": []})
    runs = history.get("runs", [])

    timeline = []
    for run in runs[-10:]:
        scores = run.get("results", {})
        avg = sum(r.get("score", 0) for r in scores.values()) // len(scores) if scores else 0
        timeline.append({"timestamp": run["timestamp"], "score": avg,
                          "dimensions": {k: v.get("score", 0) for k, v in scores.items()}})

    print(json.dumps({
        "success": True,
        "history": timeline,
        "total_runs": len(runs),
        "trend": _get_trend(),
    }))
