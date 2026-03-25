"""cc-flow adversarial review — 3-engine debate (Claude × Codex × Gemini).

Three AI engines independently review the same code, then see each other's
arguments and debate. Each engine has a unique lens and mandate.

Architecture:
  Round 1: Independent review — 3 engines in parallel, each with different lens
  Round 2: Debate — each engine sees the other two's arguments, responds
  Round 3: Verdict — majority vote + surviving issues from debate
"""

import json
import re
import shutil
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor

from cc_flow.core import TASKS_DIR, atomic_write, now_iso

# ── Engine Config ──

ENGINE_CONFIG = {
    "claude": {
        "label": "Claude (Anthropic)",
        "lens": "security vulnerabilities, edge case correctness, boundary conditions",
        "role": "Security & Correctness Auditor",
        "strength": "nuanced safety reasoning, catches subtle auth/injection/race issues others miss",
        "detect": lambda: shutil.which("claude") is not None,
        "run": lambda prompt, timeout: _exec_claude(prompt, timeout),
    },
    "codex": {
        "label": "Codex (OpenAI)",
        "lens": "code patterns, bug detection, error handling completeness",
        "role": "Bug Hunter & Code Quality",
        "strength": "pattern recognition across millions of repos, spots known anti-patterns and missing error paths",
        "detect": lambda: shutil.which("codex") is not None,
        "run": lambda prompt, timeout: _exec_codex(prompt, timeout),
    },
    "gemini": {
        "label": "Gemini (Google)",
        "lens": "architecture impact, system-wide effects, design coherence",
        "role": "Architecture & Impact Analyst",
        "strength": "1M token context — sees full codebase structure, catches cross-module breakage",
        "detect": lambda: shutil.which("gemini") is not None or shutil.which("gemini-cli") is not None,
        "run": lambda prompt, timeout: _exec_gemini(prompt, timeout),
    },
}


# ── Prompts ──

R1_PROMPT = """\
You are **{label}** in a 3-engine adversarial code review debate.
Your role: **{role}**
Your unique lens: **{lens}**
Your strength: {strength}

Review these changes thoroughly from YOUR perspective. Leverage your specific
strength — don't try to cover everything, focus on what YOU are best at finding.
Be specific — cite files, functions, line patterns. Output:

## Strengths
- [what this code does well from your lens]

## Issues
| Severity | File | Issue |
|----------|------|-------|
| critical/high/medium/low | file | description |

## Position
[2-3 sentences: your overall assessment]

## Verdict: [SHIP / NEEDS_WORK / MAJOR_RETHINK]

Changed files: {files}

Diff:
```
{diff}
```"""

R2_PROMPT = """\
You are **{label}** in round 2 of a 3-engine adversarial code review.
Your lens: **{lens}**.

Two other engines have reviewed the same code. Read their arguments below,
then respond:

1. For each issue they found: **Agree** (confirm from your lens) or **Disagree** (explain why)
2. For strengths they praised: **Confirm** or **Challenge**
3. Any issues THEY MISSED that you found?
4. Has their reasoning changed your position?

---
**{other1_label}** ({other1_lens}):
{other1_text}

---
**{other2_label}** ({other2_lens}):
{other2_text}

---

Your response:
## Agreements
- [issues you confirm from other engines]

## Disagreements
- [points you challenge, with evidence]

## Missed by Others
- [issues only you caught]

## Final Verdict: [SHIP / NEEDS_WORK / MAJOR_RETHINK]
[Has your position changed? Why/why not?]"""


# ── Engine Executors ──

def _filter_noise(text):
    """Remove MCP/session/header noise from engine output."""
    return "\n".join(
        line for line in text.split("\n")
        if not any(skip in line for skip in [
            "mcp:", "session id:", "--------", "workdir:", "model:",
            "provider:", "approval:", "sandbox:", "reasoning",
            "OpenAI Codex", "tokens used",
        ])
    ).strip()


def _exec_claude(prompt, timeout=1000):
    try:
        r = subprocess.run(
            ["claude", "-p", "--output-format", "text", prompt],
            check=False, capture_output=True, text=True, timeout=timeout,
        )
        return {"success": True, "output": r.stdout.strip()}
    except subprocess.TimeoutExpired:
        return {"success": False, "error": f"Claude timed out ({timeout}s)"}
    except OSError as e:
        return {"success": False, "error": str(e)}


def _exec_codex(prompt, timeout=1000):
    try:
        r = subprocess.run(
            ["codex", "exec", prompt],
            check=False, capture_output=True, text=True, timeout=timeout,
        )
        # Codex outputs to stderr
        raw = (r.stderr or "") + "\n" + (r.stdout or "")
        return {"success": True, "output": _filter_noise(raw)}
    except subprocess.TimeoutExpired:
        return {"success": False, "error": f"Codex timed out ({timeout}s)"}
    except OSError as e:
        return {"success": False, "error": str(e)}


def _exec_gemini(prompt, timeout=1000):
    cmd = shutil.which("gemini") or shutil.which("gemini-cli")
    if not cmd:
        return {"success": False, "error": "gemini not found"}
    try:
        r = subprocess.run(
            [cmd, "-p", prompt],
            check=False, capture_output=True, text=True, timeout=timeout,
        )
        return {"success": True, "output": _filter_noise(r.stdout)}
    except subprocess.TimeoutExpired:
        return {"success": False, "error": f"Gemini timed out ({timeout}s)"}
    except OSError as e:
        return {"success": False, "error": str(e)}


# ── Parsers ──

def _parse_verdict(text):
    """Extract verdict from engine output."""
    upper = text.upper()
    if "MAJOR_RETHINK" in upper:
        return "MAJOR_RETHINK"
    if re.search(r"VERDICT[:\s]*NEEDS[_ ]WORK", upper):
        return "NEEDS_WORK"
    if re.search(r"VERDICT[:\s]*SHIP\b", upper):
        return "SHIP"
    if "NEEDS_WORK" in upper or "NEEDS WORK" in upper:
        return "NEEDS_WORK"
    if re.search(r"\bSHIP\b", upper):
        return "SHIP"
    return "UNKNOWN"


def _parse_issues(text):
    """Extract issues from markdown table."""
    findings = []
    for match in re.finditer(
        r"\|\s*\*{0,2}(critical|high|medium|low)\*{0,2}\s*\|\s*[`]?([^|`]*)[`]?\s*\|\s*([^|]*)\|",
        text, re.IGNORECASE,
    ):
        findings.append({
            "severity": match.group(1).lower().strip("* "),
            "file": match.group(2).strip("` "),
            "description": re.sub(r'\*{1,2}', '', match.group(3).strip())[:200],
        })
    return findings


# ── Verdict Engine ──

SEVERITY_WEIGHT = {"critical": 10, "high": 5, "medium": 2, "low": 1}


def _compute_verdict(engine_results):
    """Compute final verdict from 3-engine debate.

    Rules:
    - Majority vote (2/3 agree = that verdict)
    - If split 3 ways → NEEDS_WORK (err on caution)
    - Position changes in R2 count more (someone was convinced)
    - Critical/high issues that survive R2 debate = blocking
    """
    r1_verdicts = {e: r["r1_verdict"] for e, r in engine_results.items()}
    r2_verdicts = {e: r["r2_verdict"] for e, r in engine_results.items()}

    # Count R2 verdicts (post-debate = more informed)
    r2_counts = {}
    for v in r2_verdicts.values():
        if v != "UNKNOWN":
            r2_counts[v] = r2_counts.get(v, 0) + 1

    # Majority in R2
    for verdict, count in sorted(r2_counts.items(), key=lambda x: -x[1]):
        if count >= 2:
            # Check who changed their mind
            changers = [e for e in engine_results if r1_verdicts[e] != r2_verdicts[e] and r2_verdicts[e] != "UNKNOWN"]
            reason = f"Majority ({count}/3) after debate"
            if changers:
                labels = [ENGINE_CONFIG[e]["label"] for e in changers]
                reason += f". {', '.join(labels)} changed position"
            return verdict, reason

    # No majority — collect all issues across all engines
    all_issues = []
    for r in engine_results.values():
        all_issues.extend(r.get("issues", []))
    critical_high = sum(1 for i in all_issues if i.get("severity") in ("critical", "high"))

    if critical_high > 0:
        return "NEEDS_WORK", f"No majority, but {critical_high} critical/high issues found"

    return "NEEDS_WORK", "No majority — defaulting to caution"


# ── Main Runner ──

def _gather_rp_context(context, timeout=1000):
    """Phase 0: Use RP builder to gather deep codebase context.

    RP auto-selects related files, analyzes cross-file dependencies,
    and produces architectural context that the diff alone can't show.
    This context is injected into each engine's Round 1 prompt.
    """
    try:
        files_str = ", ".join(context.get("files", [])[:10])
        summary = (
            f"Analyze the architectural context for these changed files: {files_str}. "
            "Focus on: what modules are affected, cross-file dependencies, "
            "contracts that could break, and design patterns in use. "
            "Output a concise architectural summary (not a review)."
        )
        r = subprocess.run(
            ["cc-flow", "rp", "builder", summary, "--type", "question"],
            check=False, capture_output=True, text=True, timeout=timeout,
        )
        if r.returncode == 0 and r.stdout.strip():
            # Extract response from RP JSON
            try:
                data = json.loads(r.stdout)
                review_obj = data.get("review", {})
                response = review_obj.get("response", "") if isinstance(review_obj, dict) else ""
                if not response:
                    response = data.get("response", r.stdout)
                return str(response)[:3000]
            except (json.JSONDecodeError, TypeError):
                return r.stdout[:3000]
    except (subprocess.TimeoutExpired, OSError):
        pass
    return ""


def run_debate(context, engines=None, timeout=300, dry_run=False):
    """Run 3-engine adversarial debate with RP deep context."""
    # Detect available engines
    if engines:
        active = {e: ENGINE_CONFIG[e] for e in engines if e in ENGINE_CONFIG and ENGINE_CONFIG[e]["detect"]()}
    else:
        active = {e: c for e, c in ENGINE_CONFIG.items() if c["detect"]()}

    if len(active) < 2:
        return {"success": False, "error": f"Need 2+ engines. Available: {list(active.keys())}"}

    # Check if RP is available for deep context
    rp_available = False
    try:
        from cc_flow.multi_review import _detect_rp
        rp_available = _detect_rp()
    except ImportError:
        pass

    engine_names = list(active.keys())
    files_str = ", ".join(context.get("files", [])[:15])
    diff = context.get("diff", "")[:30000]

    if dry_run:
        return {
            "success": True, "dry_run": True,
            "engines": engine_names,
            "rp_context": rp_available,
            "engine_details": {e: {"label": c["label"], "lens": c["lens"]} for e, c in active.items()},
            "files": context.get("files", []),
            "diff_bytes": len(diff),
            "instruction": (
                "3-Engine Adversarial Debate:\n"
                + ("  Phase 0: RP Builder gathers deep codebase context\n" if rp_available else "")
                + "\n".join(f"  {c['label']} — {c['lens']}" for c in active.values())
                + "\n  Round 1: Independent review (parallel)"
                + (" + RP context injected" if rp_available else "")
                + f"\n  Round 2: See each other's arguments, debate (parallel)\n"
                f"  Round 3: Majority vote + surviving issues\n"
                f"  Reviewing {len(context.get('files', []))} files"
            ),
        }

    start = time.time()
    engine_results = {}

    # ── Phase 0: RP deep context (if available) ──
    rp_context = ""
    if rp_available:
        print(json.dumps({"status": "phase0", "message": "RP gathering deep context..."}), file=sys.stderr)
        rp_context = _gather_rp_context(context)
        if rp_context:
            print(json.dumps({"status": "phase0_done", "context_chars": len(rp_context)}), file=sys.stderr)

    # ── Round 1: Independent (PARALLEL) — with RP context injected ──
    print(json.dumps({"status": "round1", "engines": engine_names, "rp_context": bool(rp_context)}), file=sys.stderr)

    rp_section = ""
    if rp_context:
        rp_section = (
            "\n\nArchitectural context from RepoPrompt (deep codebase analysis):\n"
            f"```\n{rp_context}\n```\n"
            "Use this context to inform your review — it shows cross-file dependencies "
            "and design patterns that the diff alone doesn't reveal."
        )

    with ThreadPoolExecutor(max_workers=len(active)) as pool:
        futures = {}
        for name, config in active.items():
            prompt = R1_PROMPT.format(
                label=config["label"], lens=config["lens"],
                role=config.get("role", "Reviewer"),
                strength=config.get("strength", "general code review"),
                files=files_str, diff=diff,
            ) + rp_section
            futures[pool.submit(config["run"], prompt, timeout)] = name

        for future in futures:
            name = futures[future]
            try:
                result = future.result()
            except Exception as e:
                result = {"success": False, "error": str(e)}

            text = result.get("output", "") if result.get("success") else ""
            engine_results[name] = {
                "r1_text": text[:4000],
                "r1_verdict": _parse_verdict(text),
                "r1_success": result.get("success", False),
                "issues": _parse_issues(text),
            }

    r1_verdicts = {e: r["r1_verdict"] for e, r in engine_results.items()}
    known_verdicts = {v for v in r1_verdicts.values() if v != "UNKNOWN"}

    print(json.dumps({"status": "round1_done", "verdicts": r1_verdicts}), file=sys.stderr)

    # Dashboard events
    try:
        from cc_flow.dashboard_events import emit_debate_round, emit_engine_complete
        for e, r in engine_results.items():
            emit_engine_complete(e, r["r1_verdict"], len(r.get("issues", [])), phase="review")
        emit_debate_round(1, r1_verdicts, sum(len(r.get("issues", [])) for r in engine_results.values()))
    except ImportError:
        pass

    # Early exit: if all engines agree in Round 1, skip Round 2
    if len(known_verdicts) == 1 and len(known_verdicts) <= len(engine_results):
        unanimous = known_verdicts.pop()
        total_issues = sum(len(r.get("issues", [])) for r in engine_results.values())
        # Skip Round 2 if unanimous SHIP with few issues, or unanimous MAJOR_RETHINK
        if (unanimous == "SHIP" and total_issues <= 2) or unanimous == "MAJOR_RETHINK":
            elapsed = round(time.time() - start, 1)
            all_issues = []
            for r in engine_results.values():
                all_issues.extend(r.get("issues", []))

            print(json.dumps({"status": "early_exit", "unanimous": unanimous}), file=sys.stderr)

            for r in engine_results.values():
                r["r2_text"] = ""
                r["r2_verdict"] = r["r1_verdict"]
                r["r2_success"] = True

            return _build_result(engine_results, all_issues, elapsed, rp_context, "Unanimous in Round 1 — skipped Round 2")

    # ── Round 2: Debate (PARALLEL — each sees the other two) ──
    print(json.dumps({"status": "round2", "engines": engine_names}), file=sys.stderr)

    with ThreadPoolExecutor(max_workers=len(active)) as pool:
        futures = {}
        for name, config in active.items():
            others = [(e, c) for e, c in active.items() if e != name]
            other1_name, other1_config = others[0]
            other2_name = others[1][0] if len(others) > 1 else other1_name
            other2_config = others[1][1] if len(others) > 1 else other1_config

            prompt = R2_PROMPT.format(
                label=config["label"], lens=config["lens"],
                other1_label=other1_config["label"], other1_lens=other1_config["lens"],
                other1_text=engine_results[other1_name]["r1_text"][:3000],
                other2_label=other2_config["label"], other2_lens=other2_config["lens"],
                other2_text=engine_results[other2_name]["r1_text"][:3000],
            )
            futures[pool.submit(config["run"], prompt, timeout)] = name

        for future in futures:
            name = futures[future]
            try:
                result = future.result()
            except Exception as e:
                result = {"success": False, "error": str(e)}

            text = result.get("output", "") if result.get("success") else ""
            engine_results[name]["r2_text"] = text[:4000]
            engine_results[name]["r2_verdict"] = _parse_verdict(text)
            engine_results[name]["r2_success"] = result.get("success", False)
            # Merge R2 issues
            engine_results[name]["issues"].extend(_parse_issues(text))

    # ── Round 3: Build result ──
    _verdict, _reason = _compute_verdict(engine_results)  # computed inside _build_result

    all_issues = []
    seen = set()
    for r in engine_results.values():
        for issue in r.get("issues", []):
            key = issue.get("file", "") + issue.get("description", "")[:50]
            if key not in seen:
                seen.add(key)
                all_issues.append(issue)
    all_issues.sort(key=lambda x: SEVERITY_WEIGHT.get(x.get("severity", "low"), 1), reverse=True)

    elapsed = round(time.time() - start, 1)
    return _build_result(engine_results, all_issues, elapsed, rp_context)


def _build_result(engine_results, all_issues, elapsed, rp_context, reason_override=None):
    """Build the final debate result dict."""
    final_verdict, reason = _compute_verdict(engine_results)
    if reason_override:
        reason = reason_override

    review_dir = TASKS_DIR / "reviews"
    review_dir.mkdir(parents=True, exist_ok=True)
    ts = now_iso().replace(":", "-").replace("T", "_")[:19]
    report = {
        "timestamp": now_iso(),
        "verdict": final_verdict,
        "reason": reason,
        "engines": {e: {
            "label": ENGINE_CONFIG[e]["label"],
            "r1_verdict": r["r1_verdict"],
            "r2_verdict": r.get("r2_verdict", r["r1_verdict"]),
            "issues": r["issues"][:5],
            "changed_position": r["r1_verdict"] != r.get("r2_verdict", r["r1_verdict"]) and r.get("r2_verdict") != "UNKNOWN",
        } for e, r in engine_results.items()},
        "all_issues": all_issues[:10],
        "rp_context_used": bool(rp_context),
        "elapsed_seconds": elapsed,
    }
    report_path = review_dir / f"debate-{ts}.json"
    atomic_write(report_path, json.dumps(report, indent=2, ensure_ascii=False) + "\n")

    return {
        "success": True,
        "verdict": final_verdict,
        "reason": reason,
        "elapsed_seconds": elapsed,
        "engines": {e: {
            "label": ENGINE_CONFIG[e]["label"],
            "r1": r["r1_verdict"],
            "r2": r.get("r2_verdict", r["r1_verdict"]),
            "changed": r["r1_verdict"] != r.get("r2_verdict", r["r1_verdict"]) and r.get("r2_verdict") != "UNKNOWN",
            "issues_found": len(r["issues"]),
        } for e, r in engine_results.items()},
        "total_issues": len(all_issues),
        "top_issues": all_issues[:5],
        "report": str(report_path),
        "instruction": _build_instruction(final_verdict, reason, engine_results, all_issues),
    }


def _build_instruction(verdict, reason, engine_results, issues):
    """Build debate summary."""
    lines = [f"# 3-Engine Debate: {verdict}", f"Reason: {reason}", ""]

    lines.append("## Timeline")
    for e, r in engine_results.items():
        label = ENGINE_CONFIG[e]["label"]
        changed = " → CHANGED" if r["r1_verdict"] != r["r2_verdict"] and r["r2_verdict"] != "UNKNOWN" else ""
        lines.append(f"  {label}: R1={r['r1_verdict']} → R2={r['r2_verdict']}{changed}")
    lines.append("")

    if issues:
        lines.append(f"## Issues ({len(issues)} total)")
        for i, issue in enumerate(issues[:7], 1):
            lines.append(f"  {i}. [{issue['severity'].upper()}] {issue.get('file', '')}: {issue['description'][:80]}")
        lines.append("")

    if verdict == "SHIP":
        lines.append("Debate concluded: safe to ship. Next: `/cc-commit`")
    else:
        lines.append("Debate concluded: fix issues before shipping.")
        lines.append("Next: Fix issues, then `cc-flow adversarial-review`")

    return "\n".join(lines)


# ── CLI ──

def cmd_adversarial_review(args):
    """Run 3-engine adversarial debate review."""
    from cc_flow.multi_review import _build_review_context

    dry_run = getattr(args, "dry_run", False)
    timeout = getattr(args, "timeout", 300)
    diff_range = getattr(args, "range", "") or ""
    paths = getattr(args, "path", None)

    # Parse engines
    engines_arg = getattr(args, "engines", "") or ""
    engines = [e.strip() for e in engines_arg.split(",") if e.strip()] if engines_arg else None

    context = _build_review_context(diff_range=diff_range, paths=paths)
    if not context["diff"]:
        print(json.dumps({"success": False, "error": "No changes to review"}))
        return

    result = run_debate(context, engines=engines, timeout=timeout, dry_run=dry_run)
    print(json.dumps(result))
