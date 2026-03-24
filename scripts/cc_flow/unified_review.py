"""cc-flow unified review — one command, auto-selects best review mode.

Auto-escalation:
  3 engines (claude+codex+gemini) → adversarial debate (best quality)
  2 engines                       → multi-review consensus
  1 engine                        → single agent lint review (fallback)

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
                    f"3-Engine Adversarial Debate ({', '.join(engines.values())})\n"
                    + ("  Phase 0: RP gathers deep codebase context\n" if rp_available else "")
                    + "  Round 1: Independent review (parallel)\n"
                    "  Round 2: See each other's arguments, debate (parallel)\n"
                    "  Round 3: Majority vote + surviving issues"
                ),
                "multi": (
                    f"Multi-Engine Consensus ({', '.join(engines.values())})\n"
                    "  All engines review in parallel → consensus merge"
                ),
                "agent": "Single-engine lint review (ruff + basic checks)",
            }.get(mode, mode),
        }))
        return

    # Build context
    from cc_flow.multi_review import _build_review_context
    context = _build_review_context(diff_range=diff_range, paths=paths)

    if not context["diff"]:
        print(json.dumps({"success": False, "error": "No changes to review (no diff found)"}))
        return

    # Dispatch to the right engine
    if mode == "adversarial":
        from cc_flow.adversarial_review import run_debate
        result = run_debate(context, timeout=timeout)

    elif mode == "multi":
        from cc_flow.multi_review import cmd_multi_review

        # Build a minimal args object
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
        # Agent fallback — just run ruff
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
