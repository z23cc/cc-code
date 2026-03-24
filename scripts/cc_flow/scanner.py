"""Smart scanner — multi-dimensional project analysis beyond lint.

Scans: architecture, test coverage, documentation, code duplication,
dependency health, complexity hotspots. Returns prioritized findings
with ROI estimates based on Q-learning history.
"""

import ast
import json
import subprocess
from pathlib import Path

from cc_flow.core import TASKS_DIR, safe_json_load

SCAN_HISTORY_FILE = TASKS_DIR / "scan_history.json"


def _run_cmd(cmd, timeout=15):
    """Run a command, return stdout or empty string on failure."""
    try:
        r = subprocess.run(cmd, check=False, capture_output=True, text=True, timeout=timeout)
        return r.stdout.strip() if r.returncode == 0 else ""
    except (subprocess.TimeoutExpired, OSError):
        return ""


# ── Individual scanners ──

def scan_architecture():
    """Scan code architecture: file sizes, function counts, module structure."""
    findings = []
    for py in sorted(Path(".").rglob("*.py")):
        if any(p in str(py) for p in ["__pycache__", ".venv", "node_modules", ".git", "ref/", "zcf/", "ccg-workflow/"]):
            continue
        try:
            content = py.read_text()
            lines = len(content.split("\n"))
            tree = ast.parse(content)
            funcs = [n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
        except (SyntaxError, OSError):
            continue

        if lines > 300:
            findings.append({
                "type": "large_file", "severity": "P3",
                "message": f"File {py} has {lines} lines (>300), consider splitting",
                "file": str(py), "metric": lines,
            })
        if len(funcs) > 20:
            findings.append({
                "type": "many_functions", "severity": "P4",
                "message": f"File {py} has {len(funcs)} functions (>20)",
                "file": str(py), "metric": len(funcs),
            })

    return findings


def scan_test_coverage():
    """Identify source files without corresponding test files."""
    findings = []
    src_dir = Path("scripts/cc_flow")
    test_dir = Path("tests")

    if not src_dir.exists() or not test_dir.exists():
        return findings

    test_content = ""
    for tf in test_dir.glob("*.py"):
        test_content += tf.read_text()

    for src in sorted(src_dir.glob("*.py")):
        if src.name.startswith("_"):
            continue
        module_name = src.stem
        # Check if module is imported in any test
        if f"cc_flow.{module_name}" not in test_content and "from cc_flow import" not in test_content:
            findings.append({
                "type": "no_test", "severity": "P3",
                "message": f"Module {module_name} has no test imports",
                "file": str(src),
            })

    return findings


def scan_docstrings():
    """Find public functions missing docstrings."""
    findings = []
    for py in sorted(Path("scripts/cc_flow").glob("*.py")):
        if py.name.startswith("_"):
            continue
        try:
            tree = ast.parse(py.read_text())
        except SyntaxError:
            continue
        missing = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and not node.name.startswith("_"):
                if not ast.get_docstring(node):
                    missing.append(node.name)
        if len(missing) > 3:
            findings.append({
                "type": "missing_docstrings", "severity": "P4",
                "message": f"{py.name}: {len(missing)} public funcs without docstrings ({', '.join(missing[:3])}...)",
                "file": str(py), "metric": len(missing),
            })

    return findings


def scan_duplication():
    """Find code duplication using embedding similarity (Morph) or line-hash fallback."""
    # Try embedding-based detection first
    semantic = _scan_duplication_semantic()
    if semantic is not None:
        return semantic

    # No semantic results, use line-hash fallback
    return _scan_duplication_linehash()


def _extract_functions():
    """Extract function bodies from cc_flow modules for duplication analysis."""
    functions = []
    for py in sorted(Path("scripts/cc_flow").glob("*.py")):
        if py.name.startswith("_"):
            continue
        try:
            content = py.read_text()
            tree = ast.parse(content)
        except (SyntaxError, OSError):
            continue
        source_lines = content.split("\n")
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and len(source_lines) > node.end_lineno:
                body = "\n".join(source_lines[node.lineno - 1:node.end_lineno])
                if len(body) > 50:
                    functions.append({"file": py.name, "name": node.name,
                                      "text": body[:200], "lineno": node.lineno})
    return functions


def _find_similar_pairs(functions, embedded):
    """Find cross-file function pairs with high embedding similarity."""
    from cc_flow.embeddings import cosine_similarity

    findings = []
    seen = set()
    for i in range(len(functions)):
        for j in range(i + 1, len(functions)):
            if functions[i]["file"] == functions[j]["file"]:
                continue
            score = cosine_similarity(embedded[i][1], embedded[j][1])
            pair_key = f"{functions[i]['name']}:{functions[j]['name']}"
            if score > 0.85 and pair_key not in seen:
                seen.add(pair_key)
                findings.append({
                    "type": "semantic_duplication", "severity": "P3",
                    "message": (f"{functions[i]['file']}:{functions[i]['name']} ~ "
                                f"{functions[j]['file']}:{functions[j]['name']} "
                                f"(similarity: {score:.2f})"),
                    "files": [functions[i]["file"], functions[j]["file"]],
                    "score": round(score, 3),
                })
                if len(findings) >= 5:
                    return findings
    return findings


def _scan_duplication_semantic():
    """Use Morph embeddings to find semantically similar functions across files."""
    try:
        from cc_flow.embeddings import embed_texts
    except ImportError:
        return None

    functions = _extract_functions()
    if len(functions) < 2:
        return []

    embedded = embed_texts([f["text"] for f in functions])
    if not embedded:
        return None

    return _find_similar_pairs(functions, embedded)


def _scan_duplication_linehash():
    """Fallback: line-hash based duplication detection."""
    findings = []
    line_hashes = {}

    for py in sorted(Path("scripts/cc_flow").glob("*.py")):
        try:
            lines = py.read_text().split("\n")
        except OSError:
            continue
        for i in range(len(lines) - 3):
            block = "\n".join(lines[i:i + 4]).strip()
            if len(block) < 40:
                continue
            h = hash(block)
            if h not in line_hashes:
                line_hashes[h] = []
            line_hashes[h].append((str(py), i + 1))

    for locations in line_hashes.values():
        if len(locations) >= 2:
            files = list({loc[0] for loc in locations})
            if len(files) >= 2:
                findings.append({
                    "type": "duplication", "severity": "P4",
                    "message": f"Similar code in {files[0].split('/')[-1]} and {files[1].split('/')[-1]}",
                    "files": files[:2],
                })
                if len(findings) >= 5:
                    break

    return findings


def scan_dependencies():
    """Check for outdated or missing dependency declarations."""
    findings = []
    pyproject = Path("pyproject.toml")
    if not pyproject.exists():
        return findings

    content = pyproject.read_text()

    # Check if key imports are declared as dependencies
    imports_used = _collect_imports()

    stdlib = {"json", "sys", "os", "pathlib", "datetime", "hashlib", "math",
              "subprocess", "importlib", "argparse", "ast", "re", "time",
              "shutil", "threading", "functools", "collections"}

    third_party = imports_used - stdlib - {"cc_flow", "morph_client"}
    findings.extend(
        {"type": "undeclared_dep", "severity": "P3",
         "message": f"Import '{pkg}' used but not in pyproject.toml"}
        for pkg in third_party if pkg not in content
    )

    return findings


def _collect_imports():
    """Collect all top-level import names from scripts/."""
    imports_used = set()
    for py in Path("scripts").rglob("*.py"):
        try:
            text = py.read_text()
        except OSError:
            continue
        for line in text.split("\n"):
            if line.startswith(("import ", "from ")):
                parts = line.split()
                if len(parts) >= 2:
                    imports_used.add(parts[1].split(".")[0])
    return imports_used


# ── Aggregator ──

ALL_SCANNERS = {
    "architecture": scan_architecture,
    "test_coverage": scan_test_coverage,
    "docstrings": scan_docstrings,
    "duplication": scan_duplication,
    "dependencies": scan_dependencies,
}


def run_smart_scan(scanners=None):
    """Run all (or selected) scanners, return aggregated findings."""
    if scanners is None:
        scanners = list(ALL_SCANNERS.keys())

    all_findings = {}
    for name in scanners:
        if name in ALL_SCANNERS:
            findings = ALL_SCANNERS[name]()
            if findings:
                all_findings[name] = findings

    return all_findings


# ── Effect tracking ──

def _load_scan_history():
    return safe_json_load(SCAN_HISTORY_FILE, default={"scans": []})


def _save_scan_history(data):
    SCAN_HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    SCAN_HISTORY_FILE.write_text(json.dumps(data, indent=2) + "\n")


def record_scan_snapshot(findings_count):
    """Record a scan result for trend tracking."""
    from cc_flow.core import now_iso
    history = _load_scan_history()
    history["scans"].append({
        "timestamp": now_iso(),
        "findings": findings_count,
    })
    # Keep last 50 snapshots
    history["scans"] = history["scans"][-50:]
    _save_scan_history(history)


def get_scan_trend():
    """Compare current scan to previous. Returns trend direction."""
    history = _load_scan_history()
    scans = history.get("scans", [])
    if len(scans) < 2:
        return "insufficient_data"
    prev = scans[-2]["findings"]
    curr = scans[-1]["findings"]
    if curr < prev:
        return "improving"
    if curr > prev:
        return "declining"
    return "stable"
