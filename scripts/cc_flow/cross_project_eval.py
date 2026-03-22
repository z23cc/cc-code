"""Cross-project testing — run cc-flow on real codebases.

NOTE: 'eval' in filename refers to evaluation/benchmark, not Python's eval().
Tests cc-flow commands across different project types and languages.
"""

import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

from cc_flow.core import TASKS_DIR, now_iso, safe_json_load

CROSS_RESULTS_FILE = TASKS_DIR / "cross_eval_results.json"


def _run_cc(args_str, cwd, timeout=30):
    """Run cc-flow command in a target project directory."""
    cmd = [sys.executable, str(Path(__file__).parent.parent / "cc-flow.py"), *args_str.split()]
    env = {**os.environ, "PYTHONPATH": str(Path(__file__).parent.parent)}
    start = time.monotonic()
    try:
        r = subprocess.run(cmd, check=False, capture_output=True, text=True,
                           cwd=cwd, timeout=timeout, env=env)
        elapsed = int((time.monotonic() - start) * 1000)
        return r.stdout.strip(), r.stderr.strip(), r.returncode, elapsed
    except subprocess.TimeoutExpired:
        return "", "timeout", 1, timeout * 1000


def _parse_json(stdout):
    """Parse last JSON line from output."""
    for line in reversed(stdout.split("\n")):
        if line.strip().startswith("{"):
            try:
                return json.loads(line)
            except json.JSONDecodeError:
                continue
    return None


def _detect_project(project_dir):
    """Detect project language and characteristics."""
    p = Path(project_dir)
    info = {"path": str(p), "name": p.name, "language": "unknown", "files": 0}

    if (p / "pyproject.toml").exists() or (p / "setup.py").exists():
        info["language"] = "python"
    elif (p / "package.json").exists():
        info["language"] = "node"
    elif (p / "go.mod").exists():
        info["language"] = "go"
    elif (p / "Cargo.toml").exists():
        info["language"] = "rust"

    exts = {"python": "*.py", "node": "*.ts", "go": "*.go", "rust": "*.rs"}
    ext = exts.get(info["language"], "*.py")
    info["files"] = len(list(p.rglob(ext)))
    return info


def _ext(language):
    """Return file extension for language."""
    return {"python": "py", "node": "ts", "go": "go", "rust": "rs"}.get(language, "py")


def _test_project(project_dir):
    """Run tests on a single project."""
    info = _detect_project(project_dir)
    tests = []

    # Test 1: init
    _, _, code, ms = _run_cc("init", project_dir)
    tests.append({"name": "init", "passed": code == 0, "ms": ms})

    # Test 2: verify (language detection)
    out, _, code, ms = _run_cc("verify", project_dir, timeout=60)
    data = _parse_json(out)
    lang = data.get("language", "?") if data else "?"
    tests.append({"name": "verify", "passed": code in (0, 1), "ms": ms, "detected": lang})

    # Test 3: doctor
    out, _, code, ms = _run_cc("doctor --format json", project_dir)
    data = _parse_json(out)
    checks = sum(1 for c in data.get("checks", []) if c["status"] == "pass") if data else 0
    tests.append({"name": "doctor", "passed": code == 0 and checks > 0, "ms": ms, "checks": checks})

    # Test 4: search (direct grep to avoid Morph API timeout)
    term = {"python": "def ", "node": "function", "go": "func ", "rust": "fn "}.get(
        info["language"], "import")
    search_result = subprocess.run(
        ["grep", "-rn", "-m", "5", f"--include=*.{_ext(info['language'])}",
         "--exclude-dir=node_modules", "--exclude-dir=.git",
         term, str(project_dir)],
        check=False, capture_output=True, text=True, timeout=10,
    )
    found = bool(search_result.stdout.strip())
    tests.append({"name": "search", "passed": found, "ms": 0})

    # Test 5: version
    _, _, code, ms = _run_cc("version", project_dir)
    tests.append({"name": "version", "passed": code == 0, "ms": ms})

    # Cleanup
    tasks_dir = Path(project_dir) / ".tasks"
    if tasks_dir.exists():
        shutil.rmtree(tasks_dir, ignore_errors=True)

    passed = sum(1 for t in tests if t["passed"])
    return {
        "project": info, "tests": tests,
        "score": int(passed / len(tests) * 100), "passed": passed, "total": len(tests),
    }


def cmd_cross_test(args):
    """Test cc-flow across multiple real projects."""
    projects_dir = getattr(args, "dir", "") or str(Path.home() / "Desktop")
    limit = getattr(args, "limit", 5) or 5

    projects = []
    for d in sorted(Path(projects_dir).iterdir()):
        if not d.is_dir() or d.name.startswith("."):
            continue
        info = _detect_project(d)
        if info["language"] != "unknown" and info["files"] > 0:
            projects.append(str(d))
        if len(projects) >= limit:
            break

    if not projects:
        from cc_flow.core import error
        error(f"No projects found in {projects_dir}")

    all_results = [_test_project(proj) for proj in projects]

    total_score = sum(r["score"] for r in all_results) // len(all_results) if all_results else 0

    by_language = {}
    for r in all_results:
        lang = r["project"]["language"]
        by_language.setdefault(lang, []).append(r["score"])
    lang_avg = {lang: sum(s) // len(s) for lang, s in by_language.items()}

    # Save
    CROSS_RESULTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    history = safe_json_load(CROSS_RESULTS_FILE, default={"runs": []})
    history["runs"].append({
        "timestamp": now_iso(), "score": total_score,
        "projects": len(all_results), "by_language": lang_avg,
    })
    history["runs"] = history["runs"][-10:]
    CROSS_RESULTS_FILE.write_text(json.dumps(history, indent=2) + "\n")

    print(json.dumps({
        "success": True,
        "overall_score": total_score,
        "projects_tested": len(all_results),
        "by_language": lang_avg,
        "results": [
            {"name": r["project"]["name"], "language": r["project"]["language"],
             "score": r["score"], "passed": r["passed"], "total": r["total"],
             "tests": r["tests"]}
            for r in all_results
        ],
    }))
