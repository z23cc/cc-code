"""cc-flow PUA engine — 3 models mutually challenge each other to find optimal solutions.

Not pressure on humans — models PUA each other:
  1. One engine proposes → other 2 challenge it
  2. Must improve based on challenges → re-submit
  3. 2 consecutive rounds with no new issues → PASS
  4. Stuck → 3rd engine mediates

Modes:
  pua-code:   Challenge code quality (write → challenge → improve → pass)
  pua-plan:   Challenge design decisions (propose → challenge → refine → pass)
  pua-review: Adversarial review with escalating pressure
"""

import json
import re
import shutil
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor

from cc_flow.core import TASKS_DIR, atomic_write, now_iso

# ── Engine Setup ──

ENGINES = {
    "claude": {
        "label": "Claude",
        "style": "Meticulous, safety-focused. Finds edge cases others miss.",
        "pua_tone": "Your solution has a subtle flaw that will bite you in production. Here's what you missed:",
    },
    "codex": {
        "label": "Codex",
        "style": "Practical, pattern-aware. Seen this fail in 1000 repos.",
        "pua_tone": "I've seen this exact pattern fail before. The real problem is:",
    },
    "gemini": {
        "label": "Gemini",
        "style": "Big-picture, research-driven. Questions fundamental assumptions.",
        "pua_tone": "You're solving the wrong problem. Step back and consider:",
    },
}

# ── Prompts ──

CHALLENGE_PROMPT = """\
You are **{label}** in a 3-model PUA session. Your personality: {style}

{pua_tone}

The code/plan below was written by **{author}**. Your job: find REAL problems.
Don't be nice. Don't say "looks good". Find what's WRONG.

Rules:
- Every point must be SPECIFIC (cite line, function, or decision)
- No vague "consider improving" — state what's broken and why
- If you genuinely can't find issues, say "NO_ISSUES_FOUND" (this is rare)

What to challenge:
```
{content}
```

Context: {context}

Output:
## Challenges
1. [SEVERITY: critical/high/medium] [FILE/AREA]: What's wrong and why it matters
2. ...

## Verdict: [CHALLENGED (has issues) / PASSED (genuinely clean)]"""

IMPROVE_PROMPT = """\
You are **{label}**. Two other engines challenged your work:

**{challenger1}** said:
{challenge1}

**{challenger2}** said:
{challenge2}

You MUST address every challenge. For each:
- ACCEPT: Fix it (show the fix)
- REBUT: Explain why they're wrong (with evidence)
- You cannot ignore any challenge.

Original work:
```
{content}
```

Output:
## Responses
For each challenge:
- **[Challenge]**: [ACCEPT/REBUT] — [response + fix if accepted]

## Improved Version
[Updated code/plan with all accepted fixes applied]

## Remaining Issues: [0/N — how many you couldn't fix]"""

MEDIATE_PROMPT = """\
You are **{label}** acting as MEDIATOR. The other two engines are stuck in a loop.

**{engine1}** keeps saying: {position1}
**{engine2}** keeps saying: {position2}

Original work:
```
{content}
```

As mediator, decide:
1. Who is RIGHT on each disputed point? (with reasoning)
2. What is the FINAL correct version?
3. Is this ready to ship?

Output:
## Mediation
For each disputed point:
- **[Point]**: [engine1/engine2] is right because [reason]

## Final Version
[The correct code/plan incorporating all valid points]

## Verdict: [SHIP / NEEDS_WORK]"""


# ── Executors ──

def _exec(engine, prompt, timeout=300):
    """Execute prompt on engine."""
    if engine == "claude":
        cmd = ["claude", "-p", "--output-format", "text", prompt]
    elif engine == "codex":
        cmd = ["codex", "exec", prompt]
    elif engine == "gemini":
        cmd_path = shutil.which("gemini") or shutil.which("gemini-cli")
        if not cmd_path:
            return {"success": False, "error": "gemini not found"}
        cmd = [cmd_path, "-p", prompt]
    else:
        return {"success": False, "error": f"Unknown engine: {engine}"}

    try:
        r = subprocess.run(cmd, check=False, capture_output=True, text=True, timeout=timeout)
        # Codex outputs to stderr, others to stdout
        raw = (r.stderr or "") + "\n" + (r.stdout or "") if engine == "codex" else r.stdout
        output = "\n".join(
            line for line in raw.split("\n")
            if not any(skip in line for skip in [
                "mcp:", "session id:", "--------", "workdir:", "model:",
                "provider:", "OpenAI Codex", "tokens used", "mcp startup:",
            ])
        ).strip()
        return {"success": True, "output": output}
    except subprocess.TimeoutExpired:
        return {"success": False, "error": f"Timeout ({timeout}s)"}
    except OSError as e:
        return {"success": False, "error": str(e)}


def _parse_verdict(text):
    """Parse challenge verdict."""
    upper = text.upper()
    if "NO_ISSUES_FOUND" in upper or "PASSED" in upper:
        return "PASSED"
    if "CHALLENGED" in upper:
        return "CHALLENGED"
    if "SHIP" in upper and "NEEDS" not in upper:
        return "SHIP"
    return "CHALLENGED"  # default: assume issues found


def _count_challenges(text):
    """Count number of challenges raised."""
    return len(re.findall(r"\d+\.\s*\[(?:SEVERITY|critical|high|medium|low)", text, re.IGNORECASE))


# ── PUA Loop ──

def run_pua(content, context="", mode="code", max_rounds=3, timeout=300, dry_run=False):
    """Run 3-model PUA loop until consensus or max rounds."""
    available = {e: c for e, c in ENGINES.items() if shutil.which(e) or (e == "gemini" and (shutil.which("gemini") or shutil.which("gemini-cli")))}

    if len(available) < 2:
        return {"success": False, "error": f"Need 2+ engines. Available: {list(available.keys())}"}

    engine_names = list(available.keys())

    if dry_run:
        return {
            "success": True, "dry_run": True, "mode": mode,
            "engines": engine_names, "max_rounds": max_rounds,
            "instruction": (
                f"3-Model PUA ({mode} mode):\n"
                + "\n".join(f"  {c['label']}: {c['style']}" for c in available.values())
                + f"\n  Max rounds: {max_rounds}\n"
                f"  Pass condition: 2 consecutive rounds with no new issues\n"
                f"  Stuck: 3rd engine mediates"
            ),
        }

    start = time.time()
    rounds = []
    current_content = content
    pass_streak = 0  # consecutive rounds with no issues

    # Rotate: who proposes, who challenges
    for round_num in range(1, max_rounds + 1):
        author_idx = (round_num - 1) % len(engine_names)
        author = engine_names[author_idx]
        challengers = [e for e in engine_names if e != author]

        print(json.dumps({
            "pua_round": round_num, "author": author,
            "challengers": challengers, "pass_streak": pass_streak,
        }), file=sys.stderr)

        # Challenge phase (parallel)
        challenges = {}
        with ThreadPoolExecutor(max_workers=len(challengers)) as pool:
            futures = {}
            for challenger in challengers:
                cfg = ENGINES[challenger]
                prompt = CHALLENGE_PROMPT.format(
                    label=cfg["label"], style=cfg["style"], pua_tone=cfg["pua_tone"],
                    author=ENGINES[author]["label"],
                    content=current_content[:8000],
                    context=context[:2000],
                )
                futures[pool.submit(_exec, challenger, prompt, timeout)] = challenger

            for future in futures:
                name = futures[future]
                try:
                    result = future.result()
                except Exception as e:
                    result = {"success": False, "error": str(e)}
                challenges[name] = result.get("output", "") if result.get("success") else ""

        # Count total challenges
        total_issues = sum(_count_challenges(text) for text in challenges.values())
        all_passed = all(_parse_verdict(text) == "PASSED" for text in challenges.values() if text)

        round_data = {
            "round": round_num,
            "author": author,
            "challenges": {e: {"verdict": _parse_verdict(t), "issues": _count_challenges(t), "text": t[:2000]} for e, t in challenges.items()},
            "total_issues": total_issues,
            "all_passed": all_passed,
        }

        if all_passed or total_issues == 0:
            pass_streak += 1
            round_data["status"] = "CLEAN"
            rounds.append(round_data)
            if pass_streak >= 2:
                break  # 2 consecutive clean rounds = done
            continue

        pass_streak = 0  # reset on any challenge

        # Improvement phase: author must address challenges
        c_list = list(challenges.items())
        improve_prompt = IMPROVE_PROMPT.format(
            label=ENGINES[author]["label"],
            challenger1=ENGINES[c_list[0][0]]["label"],
            challenge1=c_list[0][1][:3000],
            challenger2=ENGINES[c_list[1][0]]["label"] if len(c_list) > 1 else "N/A",
            challenge2=c_list[1][1][:3000] if len(c_list) > 1 else "No additional challenges",
            content=current_content[:8000],
        )
        improve_result = _exec(author, improve_prompt, timeout)
        improved = improve_result.get("output", "") if improve_result.get("success") else current_content

        # Extract improved version
        improved_match = re.search(r"## Improved Version\n(.*?)(?=\n## |\Z)", improved, re.DOTALL)
        if improved_match:
            current_content = improved_match.group(1).strip()

        round_data["improvement"] = improved[:2000]
        round_data["status"] = "IMPROVED"
        rounds.append(round_data)

    # Check if we need mediation
    elapsed = round(time.time() - start, 1)
    final_verdict = "PASS" if pass_streak >= 2 else "NEEDS_MEDIATION"

    if final_verdict == "NEEDS_MEDIATION" and len(engine_names) >= 3:
        # Pick mediator (engine that wasn't in the last round's dispute)
        last_round = rounds[-1] if rounds else {}
        last_author = last_round.get("author", engine_names[0])
        mediator = next(e for e in engine_names if e != last_author)
        disputants = [e for e in engine_names if e != mediator]

        print(json.dumps({"pua_mediation": True, "mediator": mediator}), file=sys.stderr)

        mediate_result = _exec(mediator, MEDIATE_PROMPT.format(
            label=ENGINES[mediator]["label"],
            engine1=ENGINES[disputants[0]]["label"],
            position1=rounds[-1]["challenges"].get(disputants[0], {}).get("text", "")[:2000] if rounds else "",
            engine2=ENGINES[disputants[1]]["label"] if len(disputants) > 1 else "N/A",
            position2=rounds[-1]["challenges"].get(disputants[1], {}).get("text", "")[:2000] if rounds and len(disputants) > 1 else "",
            content=current_content[:8000],
        ), timeout)

        mediation_text = mediate_result.get("output", "") if mediate_result.get("success") else ""
        final_verdict = "PASS" if "SHIP" in mediation_text.upper() else "NEEDS_WORK"

    # Save artifacts
    review_dir = TASKS_DIR / "pua"
    review_dir.mkdir(parents=True, exist_ok=True)
    ts = now_iso().replace(":", "-").replace("T", "_")[:19]
    report_path = review_dir / f"pua-{mode}-{ts}.json"
    atomic_write(report_path, json.dumps({
        "timestamp": now_iso(), "mode": mode, "verdict": final_verdict,
        "rounds": len(rounds), "pass_streak": pass_streak,
        "engines": engine_names, "elapsed_seconds": elapsed,
        "round_details": rounds,
    }, indent=2, ensure_ascii=False) + "\n")

    return {
        "success": True,
        "verdict": final_verdict,
        "rounds": len(rounds),
        "pass_streak": pass_streak,
        "elapsed_seconds": elapsed,
        "engines": engine_names,
        "total_challenges": sum(r.get("total_issues", 0) for r in rounds),
        "report": str(report_path),
        "instruction": _build_instruction(final_verdict, rounds, engine_names),
    }


def _build_instruction(verdict, rounds, engines):
    """Build PUA session summary."""
    lines = [f"# PUA Session: {verdict}", ""]
    for r in rounds:
        status = r.get("status", "?")
        issues = r.get("total_issues", 0)
        author = r.get("author", "?")
        challengers = list(r.get("challenges", {}).keys())
        challenger_labels = ", ".join(ENGINES.get(c, {}).get("label", c) for c in challengers)
        author_label = ENGINES.get(author, {}).get("label", author)
        lines.append(f"Round {r['round']}: {author_label} → {challenger_labels} challenged → {issues} issues → {status}")
    lines.append("")
    if verdict == "PASS":
        lines.append("All engines satisfied. Code/plan passed PUA gauntlet.")
    else:
        lines.append("Issues remain. Review the challenges and fix before proceeding.")
    return "\n".join(lines)


# ── CLI ──

def cmd_pua(args):
    """Run 3-model PUA challenge session."""
    from cc_flow.multi_review import _build_review_context

    mode = getattr(args, "mode", "code") or "code"
    max_rounds = getattr(args, "rounds", 3)
    timeout = getattr(args, "timeout", 300)
    dry_run = getattr(args, "dry_run", False)
    diff_range = getattr(args, "range", "") or ""

    # Get content to PUA
    context = _build_review_context(diff_range=diff_range)
    content = context.get("diff", "")

    if not content and not dry_run:
        print(json.dumps({"success": False, "error": "No changes to PUA (no diff found)"}))
        return

    result = run_pua(
        content=content,
        context=f"Files: {', '.join(context.get('files', [])[:10])}",
        mode=mode, max_rounds=max_rounds, timeout=timeout, dry_run=dry_run,
    )
    print(json.dumps(result))
