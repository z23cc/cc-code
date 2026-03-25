"""cc-flow unified review — one command, auto-selects + auto-escalates.

Auto-escalation:
  3 engines → adversarial debate → if disputed → PUA (multi-round challenge)
  2 engines → multi-review consensus
  1 engine  → single agent lint review (fallback)

PUA auto-triggers when:
  - Verdict is NEEDS_WORK with critical/high issues
  - Engines disagree (split verdict)
  - Explicit --mode pua

RP Builder always used as Phase 0 context provider when available.
"""

import json
import shutil


def _detect_engines():
    """Detect available review engines."""
    engines = {}
    if shutil.which("claude"):
        engines["claude"] = "Claude (Anthropic)"
    if shutil.which("codex"):
        engines["codex"] = "Codex (OpenAI)"
    if shutil.which("gemini") or shutil.which("gemini-cli"):
        engines["gemini"] = "Gemini (Google)"

    rp = False
    try:
        from cc_flow.multi_review import _detect_rp
        rp = _detect_rp()
    except ImportError:
        pass

    return engines, rp


def cmd_unified_review(args):
    """Run code review — auto-selects best mode based on available engines."""
    diff_range = getattr(args, "range", "") or ""
    paths = getattr(args, "path", None)
    timeout = getattr(args, "timeout", 300)
    dry_run = getattr(args, "dry_run", False)
    mode_override = getattr(args, "mode", "") or ""

    engines, rp_available = _detect_engines()
    engine_count = len(engines)

    # Select mode
    if mode_override:
        mode = mode_override
    elif engine_count >= 3:
        mode = "adversarial"
    elif engine_count >= 2:
        mode = "multi"
    else:
        mode = "agent"

    if dry_run:
        print(json.dumps({
            "success": True,
            "dry_run": True,
            "mode": mode,
            "engines": list(engines.keys()),
            "engine_labels": engines,
            "rp_context": rp_available,
            "instruction": {
                "adversarial": (
                    f"3-Engine Review ({', '.join(engines.values())})\n"
                    + ("  Phase 0: RP gathers deep codebase context\n" if rp_available else "")
                    + "  Round 1: Independent review (parallel)\n"
                    "  Round 2: See each other's arguments, debate (parallel)\n"
                    "  Round 3: Majority vote + surviving issues\n"
                    "  Auto-PUA: if disputed/critical issues → multi-round challenge until resolved"
                ),
                "multi": (
                    f"Multi-Engine Consensus ({', '.join(engines.values())})\n"
                    "  All engines review in parallel → consensus merge"
                ),
                "agent": "Single-engine lint review (ruff + basic checks)",
                "pua": (
                    f"3-Model PUA Challenge ({', '.join(engines.values())})\n"
                    "  Models mutually challenge each other in rounds until optimal"
                ),
            }.get(mode, mode),
        }))
        return

    # Build context
    from cc_flow.multi_review import _build_review_context
    context = _build_review_context(diff_range=diff_range, paths=paths)

    if not context["diff"]:
        print(json.dumps({"success": False, "error": "No changes to review (no diff found)"}))
        return

    # Direct PUA mode
    if mode == "pua":
        from cc_flow.pua_engine import run_pua
        result = run_pua(
            content=context["diff"],
            context=f"Files: {', '.join(context.get('files', [])[:10])}",
            timeout=timeout,
        )
        if isinstance(result, dict):
            result["mode"] = "pua"
            result["engines_available"] = list(engines.keys())
        print(json.dumps(result))
        return

    # Adversarial debate
    if mode == "adversarial":
        from cc_flow.adversarial_review import run_debate
        result = run_debate(context, timeout=timeout)

        # Auto-escalate to PUA if disputed or critical issues
        if isinstance(result, dict) and _should_escalate_to_pua(result):
            print(json.dumps({
                "status": "escalating",
                "message": "Debate has unresolved disputes — escalating to PUA multi-round challenge",
            }), file=__import__("sys").stderr)

            from cc_flow.pua_engine import run_pua
            pua_result = run_pua(
                content=context["diff"],
                context=f"Files: {', '.join(context.get('files', [])[:10])}. Prior debate issues: {result.get('total_issues', 0)}",
                timeout=timeout,
            )
            if isinstance(pua_result, dict) and pua_result.get("success"):
                # Merge PUA result into review output
                result["pua_escalated"] = True
                result["pua_verdict"] = pua_result.get("verdict")
                result["pua_rounds"] = pua_result.get("rounds")
                result["verdict"] = pua_result.get("verdict", result.get("verdict"))
                result["instruction"] = (
                    result.get("instruction", "")
                    + f"\n\n## PUA Escalation ({pua_result.get('rounds', 0)} rounds)\n"
                    + pua_result.get("instruction", "")
                )

    elif mode == "multi":
        from cc_flow.multi_review import cmd_multi_review

        class Args:
            pass
        a = Args()
        a.engines = ",".join(engines.keys())
        a.timeout = timeout
        a.dry_run = False
        a.range = diff_range
        a.path = paths
        cmd_multi_review(a)
        return

    else:
        from cc_flow.multi_review import _run_agent
        raw = _run_agent(context)
        result = {
            "success": True,
            "mode": "agent",
            "verdict": raw.get("verdict", "UNKNOWN"),
            "findings": raw.get("findings", []),
            "instruction": f"Agent review: {raw.get('verdict', 'UNKNOWN')}",
        }

    # Output
    if isinstance(result, dict):
        result["mode"] = mode
        result["engines_available"] = list(engines.keys())
        result["rp_context"] = rp_available
        print(json.dumps(result))


def _should_escalate_to_pua(debate_result):
    """Decide if debate result warrants PUA escalation."""
    verdict = debate_result.get("verdict", "")
    total_issues = debate_result.get("total_issues", 0)

    # Escalate if: critical/high issues, or engines disagree
    if verdict == "NEEDS_WORK" and total_issues >= 3:
        return True

    # Check for split verdicts (engines disagree)
    engine_data = debate_result.get("engines", {})
    verdicts = set()
    for e_data in engine_data.values():
        r2 = e_data.get("r2", e_data.get("r2_verdict", ""))
        if r2 and r2 != "UNKNOWN":
            verdicts.add(r2)
    if len(verdicts) > 1:
        return True  # engines disagree

    return False
