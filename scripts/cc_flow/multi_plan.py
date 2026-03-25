"""cc-flow multi-plan — 3-engine collaborative planning (Claude × Codex × Gemini).

Claude designs, Codex stress-tests, Gemini researches + synthesizes.

Architecture:
  Phase 0: RP Builder gathers codebase context
  Round 1: Claude produces structured plan
  Round 2: Codex finds pitfalls + Gemini researches best practices (parallel)
  Round 3: Gemini synthesizes final plan from all inputs
"""

import json
import shutil
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor

from cc_flow.core import TASKS_DIR, atomic_write, now_iso

# ── Prompts ──

CLAUDE_PLAN_PROMPT = """\
You are the **Plan Designer** (Claude). Your job is to create a comprehensive,
structured implementation plan.

Goal: {goal}

{rp_context}

Create a detailed plan with:

## Overview
[1-2 sentence summary of the approach]

## Architecture Decisions
| Decision | Choice | Rationale |
|----------|--------|-----------|
| [e.g., API style] | [REST/GraphQL/...] | [why] |

## Implementation Phases
### Phase 1: [name]
- [ ] Task 1: [description]
- [ ] Task 2: [description]

### Phase 2: [name]
- [ ] Task 3: [description]

## Data Model
[Schema changes, new tables/fields if applicable]

## API Design
[Endpoints, request/response if applicable]

## Testing Strategy
[What to test, how to verify]

## Risks & Mitigations
| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| [risk] | high/medium/low | [how to handle] |

## Estimated Complexity
[simple/medium/complex] — [why]"""

CODEX_CRITIQUE_PROMPT = """\
You are the **Engineering Experience Reviewer** (Codex/GPT). You've seen millions
of codebases. Your job is to stress-test this plan from practical experience.

The Plan Designer (Claude) created this plan:
---
{plan}
---

{rp_context}

For each part of the plan, draw on your experience:

## Pitfalls I've Seen
For each architecture decision or task, warn about real-world problems:
- "In projects using [X], the common mistake is..."
- "This pattern breaks when..."
- "Missing: you need to also handle..."

## Better Alternatives
Where you've seen better approaches:
- "Instead of [X], consider [Y] because..."
- "A simpler approach: ..."

## Missing Pieces
What the plan forgot:
- Error handling gaps
- Migration concerns
- Performance implications
- Dependency conflicts

## Verdict
[APPROVE / REVISE / RETHINK] — [why]"""

GEMINI_RESEARCH_PROMPT = """\
You are the **Research Analyst** (Gemini). Your job is to research current best
practices and validate the plan against the latest information.

The Plan Designer (Claude) created this plan:
---
{plan}
---

{rp_context}

Research and analyze:

## Current Best Practices
For each technology/pattern in the plan, what does the community recommend NOW?
- Latest library versions and breaking changes
- Deprecated patterns the plan might use
- Community consensus on the approach

## Similar Projects
Have you seen this pattern implemented well? What worked and what didn't?

## Security & Compliance
- Any security patterns missing?
- Compliance considerations?

## Scalability Assessment
- Will this design scale for 10x/100x growth?
- Bottleneck predictions

## Recommendations
Specific improvements based on research:
1. [recommendation with source/rationale]
2. [recommendation]

## Verdict
[APPROVE / REVISE / RETHINK] — [why]"""

GEMINI_SYNTHESIZE_PROMPT = """\
You are the **Final Synthesizer** (Gemini). You have three inputs:
1. Claude's original plan
2. Codex's engineering critique (pitfalls, alternatives)
3. Your own research findings

Synthesize the BEST POSSIBLE final plan by:
- Keeping Claude's structure (it's well-organized)
- Incorporating Codex's pitfall warnings as revised tasks/risks
- Adding your research findings as updated recommendations
- Resolving any conflicts between the three perspectives

Original plan by Claude:
---
{plan}
---

Codex's critique:
---
{codex_critique}
---

Your earlier research:
---
{gemini_research}
---

Output the FINAL PLAN in the same structure as Claude's original,
but improved with all three perspectives merged. Mark changes with
[REVISED], [ADDED], or [FROM CODEX]/[FROM RESEARCH] tags."""


# ── Engine Executors ──

def _filter_noise(text):
    """Remove CLI noise from engine output."""
    return "\n".join(
        line for line in text.split("\n")
        if not any(skip in line for skip in [
            "mcp:", "session id:", "--------", "workdir:", "model:",
            "provider:", "approval:", "sandbox:", "reasoning",
            "OpenAI Codex", "tokens used",
        ])
    ).strip()


def _exec_claude(prompt, timeout=300):
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
            ["codex", "exec", "--approval-mode", "never", prompt],
            check=False, capture_output=True, text=True, timeout=timeout,
        )
        raw = (r.stderr or "") + "\n" + (r.stdout or "")
        return {"success": True, "output": _filter_noise(raw)}
    except subprocess.TimeoutExpired:
        return {"success": False, "error": f"Codex timed out ({timeout}s)"}
    except OSError as e:
        return {"success": False, "error": str(e)}


def _exec_gemini(prompt, timeout=300):
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


# ── RP Context ──

def _gather_rp_context(goal):
    """Use RP builder to gather codebase context relevant to the goal."""
    try:
        r = subprocess.run(
            ["cc-flow", "rp", "builder", f"What code is relevant to: {goal}", "--type", "question"],
            check=False, capture_output=True, text=True, timeout=120,
        )
        if r.returncode == 0 and r.stdout.strip():
            try:
                data = json.loads(r.stdout)
                review_obj = data.get("review", {})
                response = review_obj.get("response", "") if isinstance(review_obj, dict) else ""
                if not response:
                    response = data.get("response", r.stdout)
                return str(response)[:4000]
            except (json.JSONDecodeError, TypeError):
                return r.stdout[:4000]
    except (subprocess.TimeoutExpired, OSError):
        pass
    return ""


def _parse_verdict(text):
    """Extract plan verdict."""
    upper = text.upper()
    if "RETHINK" in upper:
        return "RETHINK"
    if "REVISE" in upper:
        return "REVISE"
    if "APPROVE" in upper:
        return "APPROVE"
    return "UNKNOWN"


# ── Main ──

def run_multi_plan(goal, timeout=300, dry_run=False):
    """Run 3-engine collaborative planning."""
    # Check engines
    engines_available = {
        "claude": shutil.which("claude") is not None,
        "codex": shutil.which("codex") is not None,
        "gemini": shutil.which("gemini") is not None or shutil.which("gemini-cli") is not None,
    }
    active = [e for e, available in engines_available.items() if available]

    rp_available = False
    try:
        from cc_flow.multi_review import _detect_rp
        rp_available = _detect_rp()
    except ImportError:
        pass

    if dry_run:
        return {
            "success": True, "dry_run": True,
            "goal": goal,
            "engines": active,
            "rp_context": rp_available,
            "instruction": (
                f"3-Engine Collaborative Plan: {goal}\n"
                + ("  Phase 0: RP gathers codebase context\n" if rp_available else "")
                + "  Round 1: Claude designs structured plan\n"
                + ("  Round 2: Codex finds pitfalls" if "codex" in active else "  Round 2: (Codex unavailable)")
                + (" + Gemini researches (parallel)\n" if "gemini" in active else "\n")
                + ("  Round 3: Gemini synthesizes final plan\n" if "gemini" in active else "  Round 3: Use Codex feedback\n")
            ),
        }

    start = time.time()
    results = {}

    # ── Phase 0: RP context ──
    rp_context_text = ""
    if rp_available:
        print(json.dumps({"status": "phase0", "message": "RP gathering context..."}), file=sys.stderr)
        rp_context_text = _gather_rp_context(goal)

    rp_section = ""
    if rp_context_text:
        rp_section = f"\nCodebase context (from RepoPrompt analysis):\n```\n{rp_context_text}\n```\n"

    # ── Round 1: Claude designs ──
    print(json.dumps({"status": "round1", "message": "Claude designing plan..."}), file=sys.stderr)

    if "claude" in active:
        claude_result = _exec_claude(
            CLAUDE_PLAN_PROMPT.format(goal=goal, rp_context=rp_section),
            timeout,
        )
    else:
        # Fallback: use gemini for plan
        claude_result = _exec_gemini(
            CLAUDE_PLAN_PROMPT.format(goal=goal, rp_context=rp_section),
            timeout,
        )

    plan_text = claude_result.get("output", "") if claude_result.get("success") else ""
    if not plan_text:
        return {"success": False, "error": f"Plan generation failed: {claude_result.get('error', 'no output')}"}

    results["plan"] = {"text": plan_text[:6000], "success": claude_result.get("success")}

    # ── Round 2: Codex + Gemini critique (PARALLEL) ──
    print(json.dumps({"status": "round2", "message": "Codex critiquing + Gemini researching..."}), file=sys.stderr)

    codex_critique = ""
    gemini_research = ""

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = {}
        if "codex" in active:
            futures[pool.submit(
                _exec_codex,
                CODEX_CRITIQUE_PROMPT.format(plan=plan_text[:5000], rp_context=rp_section),
                timeout,
            )] = "codex"
        if "gemini" in active:
            futures[pool.submit(
                _exec_gemini,
                GEMINI_RESEARCH_PROMPT.format(plan=plan_text[:5000], rp_context=rp_section),
                timeout,
            )] = "gemini"

        for future in futures:
            name = futures[future]
            try:
                result = future.result()
            except Exception as e:
                result = {"success": False, "error": str(e)}

            text = result.get("output", "") if result.get("success") else ""
            if name == "codex":
                codex_critique = text
                results["codex"] = {
                    "verdict": _parse_verdict(text),
                    "text": text[:4000],
                    "success": result.get("success"),
                }
            else:
                gemini_research = text
                results["gemini_research"] = {
                    "verdict": _parse_verdict(text),
                    "text": text[:4000],
                    "success": result.get("success"),
                }

    # ── Round 3: Gemini synthesizes ──
    final_plan = plan_text  # default: original plan
    if "gemini" in active and (codex_critique or gemini_research):
        print(json.dumps({"status": "round3", "message": "Gemini synthesizing final plan..."}), file=sys.stderr)

        synth_result = _exec_gemini(
            GEMINI_SYNTHESIZE_PROMPT.format(
                plan=plan_text[:5000],
                codex_critique=codex_critique[:4000] if codex_critique else "(Codex unavailable)",
                gemini_research=gemini_research[:4000] if gemini_research else "(No prior research)",
            ),
            timeout,
        )
        if synth_result.get("success") and synth_result.get("output"):
            final_plan = synth_result["output"]
            results["synthesis"] = {"text": final_plan[:6000], "success": True}

    elapsed = round(time.time() - start, 1)

    # Determine overall verdict
    verdicts = {}
    if results.get("codex"):
        verdicts["codex"] = results["codex"].get("verdict", "UNKNOWN")
    if results.get("gemini_research"):
        verdicts["gemini"] = results["gemini_research"].get("verdict", "UNKNOWN")
    overall = "APPROVE"
    if any(v == "RETHINK" for v in verdicts.values()):
        overall = "RETHINK"
    elif any(v == "REVISE" for v in verdicts.values()):
        overall = "REVISE"

    # Save artifacts
    review_dir = TASKS_DIR / "plans"
    review_dir.mkdir(parents=True, exist_ok=True)
    ts = now_iso().replace(":", "-").replace("T", "_")[:19]

    report = {
        "timestamp": now_iso(),
        "goal": goal,
        "verdict": overall,
        "verdicts": verdicts,
        "rp_context_used": bool(rp_context_text),
        "elapsed_seconds": elapsed,
        "rounds": results,
        "final_plan": final_plan[:8000],
    }
    report_path = review_dir / f"multi-plan-{ts}.json"
    atomic_write(report_path, json.dumps(report, indent=2, ensure_ascii=False) + "\n")

    # Also save final plan as markdown
    plan_path = review_dir / f"plan-{ts}.md"
    atomic_write(plan_path, f"# Plan: {goal}\n\n{final_plan}\n")

    return {
        "success": True,
        "goal": goal,
        "verdict": overall,
        "verdicts": verdicts,
        "elapsed_seconds": elapsed,
        "engines_used": [e for e in ["claude", "codex", "gemini"] if e in active],
        "rp_context": bool(rp_context_text),
        "plan_file": str(plan_path),
        "report": str(report_path),
        "plan_preview": final_plan[:2000],
        "instruction": (
            f"# Multi-Engine Plan: {overall}\n\n"
            + (f"Codex verdict: {verdicts.get('codex', 'N/A')}\n" if 'codex' in verdicts else "")
            + (f"Gemini verdict: {verdicts.get('gemini', 'N/A')}\n" if 'gemini' in verdicts else "")
            + f"\nFull plan saved to: {plan_path}\n"
            + f"Report saved to: {report_path}\n\n"
            + ("Next: Review the plan, then `/cc-work` to execute\n" if overall == "APPROVE"
               else "Next: Address feedback, then re-run `cc-flow multi-plan`\n")
        ),
    }


# ── CLI ──

def cmd_multi_plan(args):
    """Run 3-engine collaborative planning."""
    goal = " ".join(args.goal) if args.goal else ""
    if not goal:
        print(json.dumps({"success": False, "error": "Describe your goal: cc-flow multi-plan \"build user auth\""}))
        return

    dry_run = getattr(args, "dry_run", False)
    timeout = getattr(args, "timeout", 300)

    result = run_multi_plan(goal, timeout=timeout, dry_run=dry_run)
    print(json.dumps(result))
