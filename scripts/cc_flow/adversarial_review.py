"""cc-flow adversarial review — Ship Advocate vs Quality Gate debate.

Two agents with opposing mandates review the same code, then see each
other's arguments and respond. Produces a balanced verdict that avoids
one-sided "all SHIP" or "all NEEDS_WORK" bias.

Architecture:
  Round 1: Independent — advocate finds reasons to ship, gate finds reasons to block
  Round 2: Rebuttal — each sees the other's argument and responds
  Round 3: Verdict — weight surviving arguments, produce final decision
"""

import json
import subprocess
import sys
import time

from cc_flow.core import TASKS_DIR, atomic_write, now_iso

# ── Prompts ──

ADVOCATE_R1_PROMPT = """\
You are the **Ship Advocate** in an adversarial code review. Your job is to find
reasons WHY this code should be shipped. You must argue FOR approval.

Review these changes and build the strongest case for shipping:
1. What does this code do well?
2. Why is the design sound?
3. What risks are acceptable and why?
4. Why delaying this would be worse than shipping now?

Be specific — cite files, functions, patterns. Don't be blindly positive;
acknowledge tradeoffs but argue they're acceptable.

Output format:
## Strengths
- [strength 1]
- [strength 2]

## Acceptable Risks
- [risk]: [why it's acceptable]

## Ship Argument
[Your 2-3 sentence case for shipping this code NOW]

## Verdict: SHIP

Changed files: {files}

Diff:
```
{diff}
```"""

GATE_R1_PROMPT = """\
You are the **Quality Gate** in an adversarial code review. Your job is to find
reasons WHY this code should NOT be shipped yet. You must argue AGAINST approval.

Review these changes and build the strongest case for blocking:
1. What could break in production?
2. What edge cases are unhandled?
3. What security/performance risks exist?
4. What design decisions will cause pain later?

Be specific — cite files, lines, concrete scenarios. Don't be blindly negative;
focus on real risks, not style preferences.

Output format:
## Issues Found
| Severity | File | Issue |
|----------|------|-------|
| critical/high/medium/low | file | description |

## Block Argument
[Your 2-3 sentence case for NOT shipping this code yet]

## Verdict: NEEDS_WORK

Changed files: {files}

Diff:
```
{diff}
```"""

ADVOCATE_R2_PROMPT = """\
You are the **Ship Advocate**. The Quality Gate has argued AGAINST shipping.
Read their argument below, then REBUT their concerns point by point.

For each issue they raised:
- Accept it (if valid) and explain why it's still OK to ship
- Reject it (if overblown) with evidence from the code
- Propose a mitigation that doesn't require blocking the ship

Quality Gate's argument:
---
{gate_argument}
---

Your rebuttal:
## Rebuttals
For each issue:
- **[Issue]**: [Accept/Reject] — [Your response]

## Final Position
[Updated case for shipping, accounting for valid concerns]

## Verdict: [SHIP or NEEDS_WORK]"""

GATE_R2_PROMPT = """\
You are the **Quality Gate**. The Ship Advocate has argued FOR shipping.
Read their argument below, then CHALLENGE their reasoning.

For each strength they cited:
- Agree (if solid) but note any caveats
- Challenge (if they're glossing over real risks) with specific scenarios

Ship Advocate's argument:
---
{advocate_argument}
---

Your challenge:
## Challenges
For each strength/risk:
- **[Point]**: [Agree/Challenge] — [Your response]

## Updated Issues
Any NEW concerns based on the advocate's reasoning?

## Final Position
[Updated case for blocking, accounting for valid strengths]

## Verdict: [NEEDS_WORK or SHIP]"""


# ── Runner ──

def _run_prompt(prompt, engine="gemini", timeout=300):
    """Run a prompt through an AI engine and return the response."""
    cmd = None
    if engine == "gemini":
        cmd_path = subprocess.run(["which", "gemini"], check=False, capture_output=True, text=True).stdout.strip()
        if not cmd_path:
            cmd_path = subprocess.run(["which", "gemini-cli"], check=False, capture_output=True, text=True).stdout.strip()
        if cmd_path:
            cmd = [cmd_path, "-p", prompt]
    elif engine == "codex":
        cmd = ["codex", "exec", "--approval-mode", "never", prompt]
    elif engine == "claude":
        cmd = ["claude", "-p", "--output-format", "text", prompt]

    if not cmd:
        return {"success": False, "error": f"Engine {engine} not found"}

    try:
        r = subprocess.run(cmd, check=False, capture_output=True, text=True, timeout=timeout)
        output = r.stdout.strip()
        # Filter noise
        lines = [l for l in output.split("\n") if not any(
            skip in l for skip in ["mcp:", "session id:", "--------", "workdir:", "model:", "provider:", "OpenAI Codex"]
        )]
        return {"success": True, "output": "\n".join(lines).strip()}
    except subprocess.TimeoutExpired:
        return {"success": False, "error": f"Timeout after {timeout}s"}
    except OSError as e:
        return {"success": False, "error": str(e)}


def _parse_verdict(text):
    """Extract verdict from debate output."""
    upper = text.upper()
    if "VERDICT: SHIP" in upper or "VERDICT:SHIP" in upper:
        return "SHIP"
    if "VERDICT: NEEDS_WORK" in upper or "VERDICT:NEEDS_WORK" in upper or "VERDICT: NEEDS WORK" in upper:
        return "NEEDS_WORK"
    if "VERDICT: MAJOR_RETHINK" in upper:
        return "MAJOR_RETHINK"
    # Fallback
    if "SHIP" in upper and "NEEDS_WORK" not in upper:
        return "SHIP"
    if "NEEDS_WORK" in upper:
        return "NEEDS_WORK"
    return "UNKNOWN"


def _parse_issues_from_table(text):
    """Extract issues from markdown table in gate output."""
    import re
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

def _final_verdict(advocate_r1, gate_r1, advocate_r2, gate_r2):
    """Determine final verdict from the debate.

    Rules:
    - If advocate concedes (R2 verdict = NEEDS_WORK) → NEEDS_WORK (advocate convinced)
    - If gate concedes (R2 verdict = SHIP) → SHIP (gate convinced)
    - If both hold positions → weight by issue severity
    - Tie → NEEDS_WORK (err on caution)
    """
    adv_r1_v = _parse_verdict(advocate_r1)
    gate_r1_v = _parse_verdict(gate_r1)
    adv_r2_v = _parse_verdict(advocate_r2)
    gate_r2_v = _parse_verdict(gate_r2)

    verdicts = {
        "advocate_r1": adv_r1_v,
        "gate_r1": gate_r1_v,
        "advocate_r2": adv_r2_v,
        "gate_r2": gate_r2_v,
    }

    # If advocate concedes after seeing gate's argument → strong signal
    if adv_r2_v == "NEEDS_WORK":
        return "NEEDS_WORK", "Advocate conceded after seeing Gate's arguments", verdicts

    # If gate concedes after seeing advocate's argument → strong signal
    if gate_r2_v == "SHIP":
        return "SHIP", "Gate conceded after seeing Advocate's arguments", verdicts

    # Both hold → check issue severity from gate
    issues = _parse_issues_from_table(gate_r1)
    critical_high = sum(1 for i in issues if i["severity"] in ("critical", "high"))

    if critical_high > 0:
        return "NEEDS_WORK", f"Gate holds with {critical_high} critical/high issues unresolved", verdicts

    # No critical issues, both hold → slight lean to SHIP
    if len(issues) <= 2:
        return "SHIP", "Gate's remaining concerns are low severity, Advocate's case is stronger", verdicts

    return "NEEDS_WORK", f"Gate holds with {len(issues)} unresolved issues", verdicts


# ── Main ──

def run_adversarial_review(context, advocate_engine="gemini", gate_engine="gemini", timeout=300, dry_run=False):
    """Run a full adversarial review debate."""
    files_str = ", ".join(context.get("files", [])[:15])
    diff = context.get("diff", "")[:30000]

    if dry_run:
        return {
            "success": True,
            "dry_run": True,
            "advocate_engine": advocate_engine,
            "gate_engine": gate_engine,
            "files": context.get("files", []),
            "diff_bytes": len(diff),
            "instruction": (
                f"Adversarial Review Debate:\n"
                f"  Ship Advocate ({advocate_engine}) vs Quality Gate ({gate_engine})\n"
                f"  Round 1: Independent arguments\n"
                f"  Round 2: Rebuttals after seeing opponent's case\n"
                f"  Round 3: Final verdict from surviving arguments\n"
                f"  Reviewing {len(context.get('files', []))} files"
            ),
        }

    start = time.time()
    debate = {"rounds": []}

    # ── Round 1: Independent arguments (PARALLEL) ──
    print(json.dumps({"status": "round1", "message": "Independent arguments..."}), file=sys.stderr)

    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=2) as pool:
        adv_future = pool.submit(
            _run_prompt,
            ADVOCATE_R1_PROMPT.format(files=files_str, diff=diff),
            advocate_engine, timeout,
        )
        gate_future = pool.submit(
            _run_prompt,
            GATE_R1_PROMPT.format(files=files_str, diff=diff),
            gate_engine, timeout,
        )
        advocate_r1 = adv_future.result()
        gate_r1 = gate_future.result()

    adv_r1_text = advocate_r1.get("output", "") if advocate_r1.get("success") else f"[FAILED: {advocate_r1.get('error')}]"
    gate_r1_text = gate_r1.get("output", "") if gate_r1.get("success") else f"[FAILED: {gate_r1.get('error')}]"

    debate["rounds"].append({
        "round": 1,
        "advocate": {"verdict": _parse_verdict(adv_r1_text), "text": adv_r1_text[:3000]},
        "gate": {"verdict": _parse_verdict(gate_r1_text), "text": gate_r1_text[:3000]},
    })

    # ── Round 2: Rebuttals (PARALLEL — each sees the other's R1) ──
    print(json.dumps({"status": "round2", "message": "Rebuttals..."}), file=sys.stderr)

    with ThreadPoolExecutor(max_workers=2) as pool:
        adv_r2_future = pool.submit(
            _run_prompt,
            ADVOCATE_R2_PROMPT.format(gate_argument=gate_r1_text[:5000]),
            advocate_engine, timeout,
        )
        gate_r2_future = pool.submit(
            _run_prompt,
            GATE_R2_PROMPT.format(advocate_argument=adv_r1_text[:5000]),
            gate_engine, timeout,
        )
        advocate_r2 = adv_r2_future.result()
        gate_r2 = gate_r2_future.result()

    adv_r2_text = advocate_r2.get("output", "") if advocate_r2.get("success") else f"[FAILED: {advocate_r2.get('error')}]"
    gate_r2_text = gate_r2.get("output", "") if gate_r2.get("success") else f"[FAILED: {gate_r2.get('error')}]"

    debate["rounds"].append({
        "round": 2,
        "advocate": {"verdict": _parse_verdict(adv_r2_text), "text": adv_r2_text[:3000]},
        "gate": {"verdict": _parse_verdict(gate_r2_text), "text": gate_r2_text[:3000]},
    })

    # ── Round 3: Final verdict ──
    final_verdict, reason, all_verdicts = _final_verdict(adv_r1_text, gate_r1_text, adv_r2_text, gate_r2_text)

    issues = _parse_issues_from_table(gate_r1_text)
    elapsed = round(time.time() - start, 1)

    # Save artifacts
    review_dir = TASKS_DIR / "reviews"
    review_dir.mkdir(parents=True, exist_ok=True)
    ts = now_iso().replace(":", "-").replace("T", "_")[:19]
    report = {
        "timestamp": now_iso(),
        "verdict": final_verdict,
        "reason": reason,
        "verdicts": all_verdicts,
        "issues": issues,
        "debate": debate,
        "elapsed_seconds": elapsed,
        "engines": {"advocate": advocate_engine, "gate": gate_engine},
    }
    report_path = review_dir / f"adversarial-{ts}.json"
    atomic_write(report_path, json.dumps(report, indent=2, ensure_ascii=False) + "\n")

    return {
        "success": True,
        "verdict": final_verdict,
        "reason": reason,
        "elapsed_seconds": elapsed,
        "verdicts": all_verdicts,
        "issues_found": len(issues),
        "issues": issues[:5],
        "debate_summary": {
            "round1": {
                "advocate": debate["rounds"][0]["advocate"]["verdict"],
                "gate": debate["rounds"][0]["gate"]["verdict"],
            },
            "round2": {
                "advocate": debate["rounds"][1]["advocate"]["verdict"],
                "gate": debate["rounds"][1]["gate"]["verdict"],
            },
        },
        "report": str(report_path),
        "instruction": _build_instruction(final_verdict, reason, issues, debate),
    }


def _build_instruction(verdict, reason, issues, debate):
    """Build human-readable debate summary."""
    lines = [
        f"# Adversarial Review: {verdict}",
        f"Reason: {reason}",
        "",
        "## Debate Timeline",
        f"  Round 1: Advocate={debate['rounds'][0]['advocate']['verdict']}, Gate={debate['rounds'][0]['gate']['verdict']}",
        f"  Round 2: Advocate={debate['rounds'][1]['advocate']['verdict']}, Gate={debate['rounds'][1]['gate']['verdict']}",
        "",
    ]
    if issues:
        lines.append("## Gate's Issues")
        for i, issue in enumerate(issues[:5], 1):
            lines.append(f"  {i}. [{issue['severity'].upper()}] {issue.get('file', '')}: {issue['description'][:80]}")
        lines.append("")

    if verdict == "SHIP":
        lines.append("Advocate's case survived the debate. Safe to ship.")
        lines.append("Next: `/cc-commit`")
    else:
        lines.append("Gate's concerns survived the debate. Fix issues before shipping.")
        lines.append("Next: Fix the issues above, then re-run `cc-flow adversarial-review`")

    return "\n".join(lines)


# ── CLI ──

def cmd_adversarial_review(args):
    """Run adversarial code review: Ship Advocate vs Quality Gate."""
    from cc_flow.multi_review import _build_review_context

    dry_run = getattr(args, "dry_run", False)
    advocate_engine = getattr(args, "advocate", "gemini")
    gate_engine = getattr(args, "gate", "gemini")
    timeout = getattr(args, "timeout", 300)
    diff_range = getattr(args, "range", "") or ""
    paths = getattr(args, "path", None)

    context = _build_review_context(diff_range=diff_range, paths=paths)
    if not context["diff"]:
        print(json.dumps({"success": False, "error": "No changes to review"}))
        return

    result = run_adversarial_review(
        context,
        advocate_engine=advocate_engine,
        gate_engine=gate_engine,
        timeout=timeout,
        dry_run=dry_run,
    )
    print(json.dumps(result))
