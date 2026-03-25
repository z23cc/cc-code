"""cc-flow design-review — 3-engine design scoring + auto-fix to 10.

Each engine scores design dimensions 0-10. Dimensions below 8
get "what would make this a 10?" recommendations. Then auto-fix.

Dimensions:
  Visual hierarchy, Color system, Typography, Spacing/layout,
  Responsive design, Accessibility, Interaction states,
  Consistency, Performance perception, Dark mode
"""

import json
import re
import shutil
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor

from cc_flow.core import TASKS_DIR, atomic_write, now_iso

DIMENSIONS = [
    "Visual hierarchy",
    "Color system",
    "Typography",
    "Spacing & layout",
    "Responsive design",
    "Accessibility (WCAG)",
    "Interaction states",
    "Consistency",
    "Performance perception",
    "Dark mode support",
]

SCORE_PROMPT = """\
You are **{label}** reviewing UI/UX design quality.
Your lens: **{lens}**

Score each dimension 0-10 (10=perfect, 7=good, 4=mediocre, 0=missing).
For each score below 8, explain what would make it a 10.

{context}

Dimensions to score:
{dimensions}

Output as JSON:
{{
  "scores": {{
    "Visual hierarchy": {{"score": N, "fix": "what would make it 10 (empty if >=8)"}},
    "Color system": {{"score": N, "fix": "..."}},
    ...
  }},
  "overall": N,
  "summary": "one sentence overall assessment"
}}"""

ENGINES = {
    "claude": {
        "label": "Claude",
        "lens": "accessibility, edge cases, consistency",
        "detect": lambda: shutil.which("claude") is not None,
    },
    "codex": {
        "label": "Codex",
        "lens": "patterns, performance, responsive",
        "detect": lambda: shutil.which("codex") is not None,
    },
    "gemini": {
        "label": "Gemini",
        "lens": "best practices, modern trends, color theory",
        "detect": lambda: shutil.which("gemini") is not None or shutil.which("gemini-cli") is not None,
    },
}


def _exec(engine, prompt, timeout=300):
    """Run prompt on engine."""
    if engine == "claude":
        cmd = ["claude", "-p", "--output-format", "text", prompt]
    elif engine == "codex":
        cmd = ["codex", "exec", prompt]
    elif engine == "gemini":
        cmd_path = shutil.which("gemini") or shutil.which("gemini-cli")
        if not cmd_path:
            return None
        cmd = [cmd_path, "-p", prompt]
    else:
        return None

    try:
        r = subprocess.run(cmd, check=False, capture_output=True, text=True, timeout=timeout)
        raw = (r.stderr or "") + "\n" + (r.stdout or "") if engine == "codex" else r.stdout
        return raw.strip()
    except (subprocess.TimeoutExpired, OSError):
        return None


def _parse_scores(text):
    """Parse score JSON from engine output."""
    if not text:
        return None
    match = re.search(r'\{[\s\S]*"scores"[\s\S]*\}', text)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass
    return None


def run_design_review(context, timeout=300, dry_run=False):
    """3-engine design scoring."""
    available = {e: c for e, c in ENGINES.items() if c["detect"]()}

    if dry_run:
        return {
            "success": True, "dry_run": True,
            "engines": list(available.keys()),
            "dimensions": DIMENSIONS,
            "instruction": (
                f"3-Engine Design Review ({len(DIMENSIONS)} dimensions)\n"
                + "\n".join(f"  {d}" for d in DIMENSIONS)
                + "\nEach engine scores 0-10. Below 8 → auto-fix recommendation."
            ),
        }

    if not available:
        return {"success": False, "error": "No engines available"}

    dimensions_text = "\n".join(f"- {d}" for d in DIMENSIONS)
    start = time.time()

    # 3-engine parallel scoring
    engine_results = {}
    with ThreadPoolExecutor(max_workers=len(available)) as pool:
        futures = {}
        for name, config in available.items():
            prompt = SCORE_PROMPT.format(
                label=config["label"], lens=config["lens"],
                context=context[:5000],
                dimensions=dimensions_text,
            )
            futures[pool.submit(_exec, name, prompt, timeout)] = name

        for future in futures:
            name = futures[future]
            try:
                output = future.result()
                parsed = _parse_scores(output) if output else None
                engine_results[name] = parsed
            except Exception:
                engine_results[name] = None

    # Average scores across engines
    avg_scores = {}
    for dim in DIMENSIONS:
        scores = []
        fixes = []
        for engine, data in engine_results.items():
            if data and "scores" in data:
                dim_data = data["scores"].get(dim, {})
                if isinstance(dim_data, dict) and "score" in dim_data:
                    scores.append(dim_data["score"])
                    fix = dim_data.get("fix", "")
                    if fix:
                        fixes.append(f"[{engine}] {fix}")

        avg = round(sum(scores) / len(scores), 1) if scores else 0
        avg_scores[dim] = {
            "average": avg,
            "engine_scores": {e: engine_results[e]["scores"].get(dim, {}).get("score", 0)
                              for e in engine_results if engine_results[e] and "scores" in engine_results[e]},
            "needs_fix": avg < 8,
            "fixes": fixes if avg < 8 else [],
        }

    overall = round(sum(d["average"] for d in avg_scores.values()) / len(avg_scores), 1) if avg_scores else 0
    needs_fix = [dim for dim, data in avg_scores.items() if data["needs_fix"]]

    elapsed = round(time.time() - start, 1)

    # Save report
    report_dir = TASKS_DIR / "design_reviews"
    report_dir.mkdir(parents=True, exist_ok=True)
    ts = now_iso().replace(":", "-").replace("T", "_")[:19]
    report_path = report_dir / f"design-{ts}.json"
    atomic_write(report_path, json.dumps({
        "timestamp": now_iso(), "overall": overall,
        "scores": avg_scores, "engines": list(engine_results.keys()),
        "elapsed_seconds": elapsed,
    }, indent=2, ensure_ascii=False) + "\n")

    return {
        "success": True,
        "overall": overall,
        "grade": "A" if overall >= 9 else "B" if overall >= 8 else "C" if overall >= 6 else "D",
        "scores": avg_scores,
        "needs_fix_count": len(needs_fix),
        "needs_fix": needs_fix,
        "engines": list(engine_results.keys()),
        "elapsed_seconds": elapsed,
        "report": str(report_path),
        "instruction": _build_instruction(overall, avg_scores, needs_fix),
    }


def _build_instruction(overall, scores, needs_fix):
    """Build design review summary."""
    lines = [f"# Design Review: {overall}/10", ""]
    lines.append("## Scores")
    for dim, data in scores.items():
        avg = data["average"]
        marker = "✅" if avg >= 8 else "⚠️" if avg >= 6 else "❌"
        lines.append(f"  {marker} {dim}: {avg}/10")
        if data.get("fixes"):
            for fix in data["fixes"][:2]:
                lines.append(f"      → {fix[:80]}")
    lines.append("")
    if needs_fix:
        lines.append(f"## Fix {len(needs_fix)} dimensions to reach 10:")
        for dim in needs_fix:
            lines.append(f"  - {dim} ({scores[dim]['average']}/10)")
    else:
        lines.append("All dimensions ≥8. Design is production-ready.")
    return "\n".join(lines)


def cmd_design_review(args):
    """Run 3-engine design scoring."""
    context = getattr(args, "context", "") or ""
    timeout = getattr(args, "timeout", 300)
    dry_run = getattr(args, "dry_run", False)
    url = getattr(args, "url", "") or ""

    if not context and not dry_run:
        # Try to gather context from git diff (CSS/UI files)
        try:
            r = subprocess.run(
                ["git", "diff", "HEAD~1..HEAD", "--", "*.css", "*.tsx", "*.jsx", "*.vue", "*.svelte", "*.html"],
                check=False, capture_output=True, text=True, timeout=10,
            )
            context = r.stdout[:5000] if r.stdout else ""
        except (subprocess.TimeoutExpired, OSError):
            pass

    if not context and not dry_run:
        context = f"URL: {url}" if url else "No design context available. Score based on general assessment."

    result = run_design_review(context, timeout=timeout, dry_run=dry_run)
    print(json.dumps(result))
