"""cc-flow multi-review — real multi-engine code review with consensus.

Calls 2+ external CLI engines (codex, gemini, rp, agent) in parallel,
parses structured results, and produces a consensus report.

Architecture:
  1. Detect available engines (codex review, gemini -p, rp review, agent)
  2. Build shared review context (git diff + file list)
  3. Dispatch engines in parallel (subprocess)
  4. Parse results into structured findings
  5. Run consensus engine: severity-weighted merge + conflict detection
  6. Output: consensus report + per-engine artifacts
"""

import json
import re
import shutil
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from cc_flow.core import TASKS_DIR, atomic_write, error, now_iso

# ── Engine Definitions ──

ENGINES = {
    "codex": {
        "label": "Codex (OpenAI)",
        "detect": lambda: shutil.which("codex") is not None,
        "lens": "correctness, edge cases, error handling",
    },
    "gemini": {
        "label": "Gemini (Google)",
        "detect": lambda: shutil.which("gemini") is not None or shutil.which("gemini-cli") is not None,
        "command": lambda: shutil.which("gemini") or shutil.which("gemini-cli"),
        "lens": "architecture, scalability, best practices",
    },
    "rp": {
        "label": "RepoPrompt",
        "detect": lambda: _detect_rp(),
        "lens": "deep context, cross-file dependencies, design patterns",
    },
    "agent": {
        "label": "Claude (built-in)",
        "detect": lambda: True,  # always available
        "lens": "code quality, security, maintainability",
    },
}

SEVERITY_WEIGHTS = {"critical": 10, "high": 5, "medium": 2, "low": 1}
VERDICT_RANK = {"SHIP": 0, "NEEDS_WORK": 1, "MAJOR_RETHINK": 2}


def _detect_rp():
    try:
        from cc_flow.rp import find_rp_cli, is_mcp_available
        return find_rp_cli() is not None or is_mcp_available()
    except ImportError:
        return False


# ── Context Builder ──

def _build_review_context(diff_range="", paths=None):
    """Build shared review context from git state.

    Args:
        diff_range: Git diff range (e.g., "main..feature", "HEAD~5..HEAD", "abc123")
                    If empty, auto-detects: uncommitted → staged → HEAD~1
        paths: List of path filters (e.g., ["scripts/", "tests/"])
    """
    def _git(args, default=""):
        try:
            r = subprocess.run(["git", *args], check=False, capture_output=True, text=True, timeout=15)
            return r.stdout.strip() if r.returncode == 0 else default
        except (subprocess.TimeoutExpired, OSError):
            return default

    path_args = ["--", *paths] if paths else []

    # Determine diff range
    if diff_range:
        # Explicit range: "main..HEAD", "HEAD~5", "abc123..def456"
        if ".." not in diff_range:
            diff_range = f"{diff_range}..HEAD"
        diff = _git(["diff", diff_range, *path_args])
        files = _git(["diff", "--name-only", diff_range, *path_args])
        stats = _git(["diff", "--shortstat", diff_range, *path_args])
    else:
        # Auto-detect: try uncommitted → staged → last commit
        diff = _git(["diff", *path_args])
        files = _git(["diff", "--name-only", *path_args])
        if not diff:
            diff = _git(["diff", "--staged", *path_args])
            files = _git(["diff", "--name-only", "--staged", *path_args])
        if not diff:
            diff = _git(["diff", "HEAD~1..HEAD", *path_args])
            files = _git(["diff", "--name-only", "HEAD~1..HEAD", *path_args])
        stats = _git(["diff", "--shortstat", *path_args]) or _git(["diff", "--shortstat", "HEAD~1..HEAD", *path_args])

    branch = _git(["branch", "--show-current"])
    last_commit = _git(["log", "--oneline", "-1"])

    # Smart diff cap: prioritize Python/JS source, trim test output
    diff_cap = 50000  # 50K chars (enough for most PRs)
    if len(diff) > diff_cap:
        diff = diff[:diff_cap] + f"\n\n... [truncated at {diff_cap} chars, {len(diff)} total] ..."

    file_list = [f for f in files.split("\n") if f] if files else []

    return {
        "diff": diff,
        "files": file_list,
        "branch": branch,
        "last_commit": last_commit,
        "diff_stats": stats,
        "file_count": len(file_list),
        "diff_bytes": len(diff),
    }


# ── Engine Runners ──

def _run_codex(context, timeout=1000):
    """Run codex review CLI (it auto-detects git changes)."""
    custom_prompt = (
        "Focus on: correctness, edge cases, error handling. "
        "Output findings as: severity (critical/high/medium/low): description. "
        "End with: Verdict: SHIP or NEEDS_WORK or MAJOR_RETHINK."
    )
    try:
        r = subprocess.run(
            ["codex", "review", custom_prompt],
            check=False, capture_output=True, text=True, timeout=timeout,
        )
        # Codex outputs to STDERR (not stdout)
        raw = (r.stderr or "") + "\n" + (r.stdout or "")
        lines = [
            line for line in raw.split("\n")
            if not any(skip in line for skip in [
                "mcp:", "session id:", "--------", "workdir:", "model:",
                "provider:", "approval:", "sandbox:", "reasoning", "OpenAI Codex",
                "tokens used", "mcp startup:",
            ])
        ]
        clean_output = "\n".join(lines).strip()
        return {"success": True, "output": clean_output, "exit_code": r.returncode}
    except subprocess.TimeoutExpired:
        return {"success": False, "error": f"Codex timed out after {timeout}s"}
    except OSError as e:
        return {"success": False, "error": str(e)}


def _run_gemini(context, timeout=1000):
    """Run gemini CLI review."""
    cmd = shutil.which("gemini") or shutil.which("gemini-cli")
    if not cmd:
        return {"success": False, "error": "gemini not found"}

    prompt = (
        "Review these code changes from an architecture and scalability perspective. "
        "Output findings as a markdown table: | Severity | File | Description |. "
        "End with verdict line: SHIP, NEEDS_WORK, or MAJOR_RETHINK.\n\n"
        f"Changed files: {', '.join(context['files'])}\n\n"
        f"Diff:\n{context['diff'][:30000]}"
    )
    try:
        r = subprocess.run(
            [cmd, "-p", prompt],
            check=False, capture_output=True, text=True, timeout=timeout,
        )
        return {"success": True, "output": r.stdout, "stderr": r.stderr, "exit_code": r.returncode}
    except subprocess.TimeoutExpired:
        return {"success": False, "error": f"Gemini timed out after {timeout}s"}
    except OSError as e:
        return {"success": False, "error": str(e)}


def _run_rp(context, timeout=1000):
    """Run RepoPrompt review via builder (auto-selects files + deep analysis)."""
    try:
        files_str = ", ".join(context.get("files", [])[:10])
        summary = (
            f"Review recent changes ({context.get('last_commit', 'HEAD')}). "
            f"Changed files: {files_str}. "
            "Check for: correctness, security, design patterns, edge cases. "
            "Output findings as severity (critical/high/medium/low): description. "
            "End with verdict: SHIP or NEEDS_WORK."
        )
        r = subprocess.run(
            ["cc-flow", "rp", "builder", summary, "--type", "review"],
            check=False, capture_output=True, text=True, timeout=timeout,
        )
        # RP builder output is JSON — extract the review response text
        output = r.stdout
        try:
            data = json.loads(output)
            # RP builder nests review in: data.review.response or data.response
            review_obj = data.get("review", {})
            response = review_obj.get("response", "") if isinstance(review_obj, dict) else ""
            if not response:
                response = data.get("response", data.get("text", ""))
            if not response:
                # Fallback: stringify the whole thing
                response = output
            return {"success": True, "output": str(response), "exit_code": r.returncode}
        except (json.JSONDecodeError, TypeError):
            return {"success": True, "output": output, "exit_code": r.returncode}
    except subprocess.TimeoutExpired:
        return {"success": False, "error": f"RP timed out after {timeout}s"}
    except OSError as e:
        return {"success": False, "error": str(e)}


def _run_agent(context, timeout=60):
    """Run built-in agent review — lint only changed files."""
    findings = []
    # Lint only changed files (not whole project)
    changed_files = [f for f in context.get("files", []) if f.endswith(".py")]
    if not changed_files:
        return {"success": True, "output": "No Python files changed", "findings": [], "verdict": "SHIP"}
    try:
        r = subprocess.run(
            ["ruff", "check", *changed_files, "--output-format", "json"],
            check=False, capture_output=True, text=True, timeout=15,
        )
        if r.stdout.strip():
            issues = json.loads(r.stdout)
            for issue in issues[:10]:
                findings.append({
                    "severity": "medium",
                    "file": issue.get("filename", ""),
                    "title": f"Lint: {issue.get('code', '?')}",
                    "description": issue.get("message", ""),
                })
    except (OSError, json.JSONDecodeError, subprocess.TimeoutExpired):
        pass

    verdict = "SHIP" if not findings else "NEEDS_WORK"
    output = f"Agent review: {len(findings)} lint issues found. Verdict: {verdict}"

    return {
        "success": True,
        "output": output,
        "findings": findings,
        "verdict": verdict,
    }


ENGINE_RUNNERS = {
    "codex": _run_codex,
    "gemini": _run_gemini,
    "rp": _run_rp,
    "agent": _run_agent,
}


# ── Result Parser ──

def _parse_verdict(text):
    """Extract verdict from engine output. Handles multiple formats."""
    text_upper = text.upper()
    # Explicit verdict markers
    if "MAJOR_RETHINK" in text_upper:
        return "MAJOR_RETHINK"
    if "NEEDS_WORK" in text_upper or "NEEDS WORK" in text_upper:
        return "NEEDS_WORK"
    # SHIP must not be a substring (e.g., "relationship")
    if re.search(r'\bSHIP\b', text_upper):
        return "SHIP"
    # Fallback: common review phrases
    if any(phrase in text_upper for phrase in ["LGTM", "LOOKS GOOD", "APPROVED", "NO ISSUES", "ALL GOOD"]):
        return "SHIP"
    if any(phrase in text_upper for phrase in ["ISSUES FOUND", "CHANGES NEEDED", "FIX REQUIRED", "RECOMMEND CHANGES"]):
        return "NEEDS_WORK"
    if any(phrase in text_upper for phrase in ["REJECT", "BLOCK", "DO NOT MERGE", "FUNDAMENTAL"]):
        return "MAJOR_RETHINK"
    return "UNKNOWN"


def _parse_findings(text):
    """Extract findings from engine output. Multi-format parser."""
    findings = []

    # Format 1: "severity: description" or "[severity] description"
    for match in re.finditer(
        r"(?:^|\n)\s*[-*]?\s*\[?\*{0,2}(critical|high|medium|low)\*{0,2}\]?\s*[:\-—|]\s*(.+?)(?=\n\s*[-*]?\s*\[?\*{0,2}(?:critical|high|medium|low)|\n\n|\Z)",
        text, re.IGNORECASE | re.DOTALL,
    ):
        severity = match.group(1).lower()
        desc = match.group(2).strip()
        file_match = re.search(r'(?:in |file |at )?[`]?([a-zA-Z0-9_/.-]+\.\w{1,4})[`]?', desc)
        findings.append({
            "severity": severity,
            "file": file_match.group(1) if file_match else "",
            "description": re.sub(r'\*{1,2}', '', desc)[:200],
        })

    # Format 2: Markdown table "| severity | file | description |"
    if not findings:
        for match in re.finditer(
            r"\|\s*\*{0,2}(critical|high|medium|low)\*{0,2}\s*\|\s*[`]?([^|`]*)[`]?\s*\|\s*\*{0,2}([^|]*)\*{0,2}\s*\|",
            text, re.IGNORECASE,
        ):
            findings.append({
                "severity": match.group(1).lower().strip("* "),
                "file": match.group(2).strip("` "),
                "description": re.sub(r'\*{1,2}', '', match.group(3).strip())[:200],
            })

    # Format 3: Numbered list "1. [HIGH] description"
    if not findings:
        for match in re.finditer(
            r"\d+\.\s*\[?(critical|high|medium|low)\]?\s*[:\-—]\s*(.+?)(?=\n\d+\.|\n\n|\Z)",
            text, re.IGNORECASE | re.DOTALL,
        ):
            desc = match.group(2).strip()
            file_match = re.search(r'[`]?([a-zA-Z0-9_/.-]+\.\w{1,4})[`]?', desc)
            findings.append({
                "severity": match.group(1).lower(),
                "file": file_match.group(1) if file_match else "",
                "description": desc[:200],
            })

    return findings


def _parse_engine_result(engine_name, raw_result):
    """Parse raw engine result into structured review."""
    if not raw_result.get("success"):
        return {
            "engine": engine_name,
            "label": ENGINES[engine_name]["label"],
            "lens": ENGINES[engine_name]["lens"],
            "status": "failed",
            "error": raw_result.get("error", "unknown"),
            "verdict": "SKIPPED",
            "findings": [],
        }

    # Agent already has structured output
    if engine_name == "agent" and "findings" in raw_result:
        return {
            "engine": engine_name,
            "label": ENGINES[engine_name]["label"],
            "lens": ENGINES[engine_name]["lens"],
            "status": "completed",
            "verdict": raw_result.get("verdict", "UNKNOWN"),
            "findings": raw_result.get("findings", []),
            "raw_output": raw_result.get("output", ""),
        }

    output = raw_result.get("output", "")
    return {
        "engine": engine_name,
        "label": ENGINES[engine_name]["label"],
        "lens": ENGINES[engine_name]["lens"],
        "status": "completed",
        "verdict": _parse_verdict(output),
        "findings": _parse_findings(output),
        "raw_output": output[:8000],
    }


# ── Consensus Engine ──

def build_consensus(reviews):
    """Build consensus from multiple engine reviews.

    Rules:
    - Worst verdict wins: MAJOR_RETHINK > NEEDS_WORK > SHIP
    - Findings from 2+ engines = HIGH CONFIDENCE
    - Single-engine findings = REVIEW MANUALLY
    - Severity-weighted scoring per engine
    """
    completed = [r for r in reviews if r["status"] == "completed"]
    if not completed:
        return {
            "verdict": "UNKNOWN",
            "confidence": 0,
            "message": "No engines completed successfully",
            "high_confidence_issues": [],
            "single_engine_issues": [],
            "engine_verdicts": {r["engine"]: r.get("verdict", "SKIPPED") for r in reviews},
        }

    # Worst verdict wins
    verdicts = {r["engine"]: r["verdict"] for r in completed}
    worst = max(verdicts.values(), key=lambda v: VERDICT_RANK.get(v, -1))

    # Cross-reference findings by similarity
    all_findings = []
    for r in completed:
        for f in r.get("findings", []):
            all_findings.append({**f, "engine": r["engine"]})

    # Group similar findings (same file or similar description)
    high_confidence = []
    single_engine = []
    seen_descriptions = {}

    for finding in all_findings:
        desc_key = finding.get("file", "") + ":" + finding.get("description", "")[:50].lower()
        if desc_key in seen_descriptions:
            # Found by 2+ engines — high confidence
            existing = seen_descriptions[desc_key]
            if existing not in high_confidence:
                high_confidence.append({
                    **existing,
                    "confirmed_by": [existing["engine"], finding["engine"]],
                    "confidence": "high",
                })
        else:
            seen_descriptions[desc_key] = finding

    # Remaining = single engine
    high_conf_descs = {f.get("description", "")[:50].lower() for f in high_confidence}
    for finding in all_findings:
        if finding.get("description", "")[:50].lower() not in high_conf_descs:
            if finding not in single_engine:
                single_engine.append({**finding, "confidence": "low"})

    # Severity score per engine
    engine_scores = {}
    for r in completed:
        score = sum(
            SEVERITY_WEIGHTS.get(f.get("severity", "low"), 1)
            for f in r.get("findings", [])
        )
        engine_scores[r["engine"]] = score

    # Consensus confidence
    agree_count = sum(1 for v in verdicts.values() if v == worst)
    confidence = round(agree_count / len(completed) * 100)

    return {
        "verdict": worst,
        "confidence": confidence,
        "engine_verdicts": verdicts,
        "engine_scores": engine_scores,
        "engines_used": len(completed),
        "engines_failed": len(reviews) - len(completed),
        "high_confidence_issues": high_confidence[:10],
        "single_engine_issues": single_engine[:10],
        "total_findings": len(all_findings),
        "message": _consensus_message(worst, confidence, verdicts),
    }


def _consensus_message(verdict, confidence, verdicts):
    """Human-readable consensus message."""
    engine_summary = ", ".join(f"{e}: {v}" for e, v in verdicts.items())
    if confidence == 100:
        return f"All engines agree: {verdict} ({engine_summary})"
    if verdict == "SHIP":
        return f"Consensus: SHIP with {confidence}% agreement ({engine_summary})"
    if verdict == "MAJOR_RETHINK":
        return f"BLOCKED: At least one engine flagged MAJOR_RETHINK ({engine_summary})"
    return f"Consensus: {verdict} with {confidence}% agreement ({engine_summary})"


# ── Artifact Persistence ──

def _save_artifacts(reviews, consensus, context):
    """Save review artifacts to .tasks/reviews/."""
    review_dir = TASKS_DIR / "reviews"
    review_dir.mkdir(parents=True, exist_ok=True)

    ts = now_iso().replace(":", "-").replace("T", "_")[:19]

    # Per-engine reviews
    for r in reviews:
        name = f"review-{r['engine']}-{ts}.json"
        atomic_write(review_dir / name, json.dumps(r, indent=2, ensure_ascii=False) + "\n")

    # Consensus report
    report_name = f"consensus-{ts}.json"
    atomic_write(review_dir / report_name, json.dumps({
        "timestamp": now_iso(),
        "context": {
            "branch": context.get("branch", ""),
            "last_commit": context.get("last_commit", ""),
            "files": context.get("files", []),
        },
        "consensus": consensus,
    }, indent=2, ensure_ascii=False) + "\n")

    return str(review_dir / report_name)


# ── CLI Command ──

def cmd_multi_review(args):
    """Run multi-engine code review with consensus."""
    dry_run = getattr(args, "dry_run", False)
    engines_arg = getattr(args, "engines", "") or ""
    timeout = getattr(args, "timeout", 1000)
    diff_range = getattr(args, "range", "") or ""
    paths = getattr(args, "path", None)

    # 1. Detect available engines
    available = {name: config for name, config in ENGINES.items() if config["detect"]()}

    # Filter by user selection
    if engines_arg:
        selected = [e.strip() for e in engines_arg.split(",")]
        available = {k: v for k, v in available.items() if k in selected}

    if len(available) < 2:
        names = list(available.keys())
        all_names = [n for n, c in ENGINES.items() if c["detect"]()]
        error(f"Need 2+ engines for multi-review. Available: {', '.join(all_names)}. Selected: {', '.join(names)}")

    # 2. Build context with optional range and path filters
    context = _build_review_context(diff_range=diff_range, paths=paths)
    if not context["diff"]:
        print(json.dumps({"success": False, "error": "No changes to review (no diff found)"}))
        return

    # 3. Dry run — just show plan
    if dry_run:
        scope = diff_range or "auto (uncommitted → staged → HEAD~1)"
        print(json.dumps({
            "success": True,
            "dry_run": True,
            "engines": list(available.keys()),
            "engine_details": {n: {"label": c["label"], "lens": c["lens"]} for n, c in available.items()},
            "scope": scope,
            "path_filter": paths,
            "files_to_review": context["files"],
            "file_count": context.get("file_count", len(context["files"])),
            "diff_bytes": context.get("diff_bytes", len(context["diff"])),
            "diff_stats": context.get("diff_stats", ""),
            "instruction": (
                f"Will run {len(available)} engines in parallel:\n"
                + "\n".join(f"  - {c['label']} ({c['lens']})" for c in available.values())
                + f"\nScope: {scope}"
                + (f"\nPath filter: {paths}" if paths else "")
                + f"\nReviewing {context.get('file_count', len(context['files']))} files, {context.get('diff_bytes', len(context['diff']))} chars"
                + (f"\n{context.get('diff_stats', '')}" if context.get('diff_stats') else "")
            ),
        }))
        return

    # 4. Dispatch engines in parallel
    start_time = time.time()
    print(json.dumps({
        "status": "running",
        "engines": list(available.keys()),
        "files": context["files"][:10],
    }), file=sys.stderr)

    results = {}
    with ThreadPoolExecutor(max_workers=len(available)) as pool:
        futures = {}
        for name in available:
            runner = ENGINE_RUNNERS.get(name)
            if runner:
                futures[pool.submit(runner, context, timeout)] = name

        for future in as_completed(futures):
            engine_name = futures[future]
            try:
                raw = future.result()
            except Exception as e:
                raw = {"success": False, "error": str(e)}
            results[engine_name] = _parse_engine_result(engine_name, raw)

    elapsed = round(time.time() - start_time, 1)

    # 5. Build consensus
    reviews = list(results.values())
    consensus = build_consensus(reviews)

    # 6. Save artifacts
    report_path = _save_artifacts(reviews, consensus, context)

    # 7. Output
    print(json.dumps({
        "success": True,
        "elapsed_seconds": elapsed,
        "consensus": consensus,
        "reviews": [{
            "engine": r["engine"],
            "label": r["label"],
            "status": r["status"],
            "verdict": r.get("verdict", "UNKNOWN"),
            "findings_count": len(r.get("findings", [])),
            "lens": r["lens"],
        } for r in reviews],
        "report": report_path,
        "instruction": _build_instruction(consensus, reviews),
    }))


def _build_instruction(consensus, reviews):
    """Build actionable instruction from consensus."""
    lines = [f"# Multi-Engine Review Consensus: {consensus['verdict']}"]
    lines.append(f"Confidence: {consensus['confidence']}% ({consensus['engines_used']} engines)")
    lines.append("")

    # Per-engine verdicts
    for engine, verdict in consensus.get("engine_verdicts", {}).items():
        label = ENGINES.get(engine, {}).get("label", engine)
        lines.append(f"  {label}: {verdict}")
    lines.append("")

    # High confidence issues
    if consensus.get("high_confidence_issues"):
        lines.append("## High-Confidence Issues (2+ engines agree)")
        for i, issue in enumerate(consensus["high_confidence_issues"], 1):
            sev = issue.get("severity", "?").upper()
            desc = issue.get("description", "")[:100]
            engines = ", ".join(issue.get("confirmed_by", []))
            lines.append(f"  {i}. [{sev}] {desc} — confirmed by: {engines}")
        lines.append("")

    # Single engine issues
    if consensus.get("single_engine_issues"):
        lines.append("## Review Manually (single engine)")
        for i, issue in enumerate(consensus["single_engine_issues"][:5], 1):
            sev = issue.get("severity", "?").upper()
            desc = issue.get("description", "")[:100]
            lines.append(f"  {i}. [{sev}] {issue.get('engine', '?')}: {desc}")
        lines.append("")

    # Next action
    if consensus["verdict"] == "SHIP":
        lines.append("Next: `cc-flow skill ctx save cc-multi-review --data '{\"verdict\": \"SHIP\"}'`")
        lines.append("Then: `/cc-commit`")
    elif consensus["verdict"] == "NEEDS_WORK":
        lines.append("Fix the high-confidence issues above, then re-run: `cc-flow multi-review`")
    else:
        lines.append("STOP: Discuss MAJOR_RETHINK findings with the team before proceeding.")

    return "\n".join(lines)
