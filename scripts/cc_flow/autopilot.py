"""cc-flow autopilot — 3-engine guided autonomous execution.

Three AI engines act as "command center", Claude Code acts as "executor".
The engines produce a consensus plan, Claude Code follows it step by step,
and at checkpoints the engines reconvene to review progress and steer.

Architecture:
  Phase 1: 3 engines consensus plan (multi-plan)
  Phase 2: Claude Code executes, with checkpoint callbacks
  Phase 3: At each checkpoint → 3 engines review progress → adjust
  Phase 4: 3 engines debate review → commit

This is the highest-quality execution mode — every step is guided
by multi-engine consensus, not template-based chains.
"""

import json
import shutil
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor

from cc_flow.core import TASKS_DIR, atomic_write, now_iso

# ── Checkpoint Prompt ──

CHECKPOINT_PROMPT = """\
You are **{label}** acting as a steering committee member.
Your lens: **{lens}**

The team is executing this goal: **{goal}**

Original plan:
```
{plan_summary}
```

Progress so far:
```
{progress}
```

Current status: Step {step}/{total} completed.

Evaluate and respond:

## Progress Assessment
[On track / Behind / Ahead / Blocked]

## Issues Detected
[Any problems with what's been done so far?]

## Next Step Guidance
[What should Claude Code do next? Be specific — files, commands, approach]

## Plan Adjustments
[Should the remaining plan change based on what we've learned? If so, how?]

## Verdict: [CONTINUE / ADJUST / STOP]"""


# ── Engine Helpers ──

def _detect_engines():
    """Detect available engines."""
    engines = {}
    if shutil.which("claude"):
        engines["claude"] = {"label": "Claude (Anthropic)", "lens": "security, correctness"}
    if shutil.which("codex"):
        engines["codex"] = {"label": "Codex (OpenAI)", "lens": "patterns, pitfalls"}
    if shutil.which("gemini") or shutil.which("gemini-cli"):
        engines["gemini"] = {"label": "Gemini (Google)", "lens": "architecture, best practices"}
    return engines


def _exec_engine(engine, prompt, timeout=300):
    """Execute a prompt on a specific engine."""
    from cc_flow.adversarial_review import _exec_claude, _exec_codex, _exec_gemini
    runners = {"claude": _exec_claude, "codex": _exec_codex, "gemini": _exec_gemini}
    runner = runners.get(engine)
    if not runner:
        return {"success": False, "error": f"Unknown engine: {engine}"}
    return runner(prompt, timeout)


def _parallel_consult(engines, prompt_template, template_vars, timeout=300):
    """Consult multiple engines in parallel with the same prompt template."""
    results = {}
    with ThreadPoolExecutor(max_workers=len(engines)) as pool:
        futures = {}
        for name, config in engines.items():
            prompt = prompt_template.format(
                label=config["label"], lens=config["lens"],
                **template_vars,
            )
            futures[pool.submit(_exec_engine, name, prompt, timeout)] = name

        for future in futures:
            name = futures[future]
            try:
                result = future.result()
            except Exception as e:
                result = {"success": False, "error": str(e)}
            results[name] = result.get("output", "") if result.get("success") else ""

    return results


def _parse_checkpoint_verdict(text):
    """Parse checkpoint verdict."""
    upper = text.upper()
    if "VERDICT: STOP" in upper or "VERDICT:STOP" in upper:
        return "STOP"
    if "VERDICT: ADJUST" in upper or "VERDICT:ADJUST" in upper:
        return "ADJUST"
    return "CONTINUE"


def _consensus_checkpoint(responses):
    """Build consensus from checkpoint responses."""
    verdicts = {}
    all_guidance = []
    all_adjustments = []

    for engine, text in responses.items():
        verdict = _parse_checkpoint_verdict(text)
        verdicts[engine] = verdict

        # Extract next step guidance
        import re
        guidance_match = re.search(r"## Next Step Guidance\n(.*?)(?=\n##|\Z)", text, re.DOTALL)
        if guidance_match:
            all_guidance.append(f"[{engine}] {guidance_match.group(1).strip()[:300]}")

        adjust_match = re.search(r"## Plan Adjustments\n(.*?)(?=\n##|\Z)", text, re.DOTALL)
        if adjust_match:
            adj = adjust_match.group(1).strip()
            if adj.lower() not in ("none", "no changes", "n/a", "no adjustments"):
                all_adjustments.append(f"[{engine}] {adj[:300]}")

    # Majority vote
    verdict_counts = {}
    for v in verdicts.values():
        verdict_counts[v] = verdict_counts.get(v, 0) + 1
    consensus_verdict = max(verdict_counts, key=verdict_counts.get) if verdict_counts else "CONTINUE"

    return {
        "verdict": consensus_verdict,
        "engine_verdicts": verdicts,
        "guidance": all_guidance,
        "adjustments": all_adjustments,
    }


# ── Main Runner ──

def run_autopilot(goal, timeout=300, max_checkpoints=5, dry_run=False):
    """Run 3-engine guided autonomous execution."""
    engines = _detect_engines()

    if len(engines) < 2:
        return {"success": False, "error": f"Need 2+ engines. Available: {list(engines.keys())}"}

    if dry_run:
        return {
            "success": True, "dry_run": True,
            "goal": goal,
            "engines": list(engines.keys()),
            "max_checkpoints": max_checkpoints,
            "instruction": (
                f"# Autopilot: 3-Engine Guided Execution\n"
                f"Goal: {goal}\n\n"
                f"Engines: {', '.join(e['label'] for e in engines.values())}\n\n"
                f"## Flow\n"
                f"1. **Plan**: 3 engines create consensus plan (multi-plan)\n"
                f"2. **Execute**: Claude Code follows the plan step by step\n"
                f"3. **Checkpoint**: Every major phase → 3 engines review + steer\n"
                f"4. **Review**: 3 engines adversarial debate on final code\n"
                f"5. **Commit**: If debate verdict = SHIP\n\n"
                f"Max checkpoints: {max_checkpoints}\n"
                f"Timeout per engine: {timeout}s\n"
                f"Worktree: auto-created for code isolation"
            ),
        }

    start = time.time()
    log = {"goal": goal, "started": now_iso(), "phases": []}

    # ── Phase 1: Multi-Plan ──
    print(json.dumps({"autopilot": "phase1", "message": "3-engine planning..."}), file=sys.stderr)

    from cc_flow.multi_plan import run_multi_plan
    plan_result = run_multi_plan(goal, timeout=timeout)

    if not plan_result.get("success"):
        return {"success": False, "error": f"Planning failed: {plan_result.get('error', 'unknown')}"}

    plan_text = plan_result.get("plan_preview", "")
    plan_file = plan_result.get("plan_file", "")
    log["phases"].append({"phase": "plan", "result": plan_result.get("verdict", ""), "elapsed": plan_result.get("elapsed_seconds", 0)})

    # ── Phase 2: Build execution instruction from plan ──
    execution_instruction = (
        f"# AUTOPILOT EXECUTION — Follow this plan exactly\n\n"
        f"Goal: {goal}\n\n"
        f"This plan was created by 3-engine consensus (Claude + Codex + Gemini).\n"
        f"Execute it step by step. After each major phase, report progress.\n\n"
        f"## Plan\n{plan_text}\n\n"
        f"## Execution Rules\n"
        f"## Worktree Isolation\n"
        f"Create an isolated worktree before making changes:\n"
        f"```bash\n"
        f"cc-flow worktree create autopilot-{goal.split()[0][:10].lower()}\n"
        f"cd $(git rev-parse --show-toplevel)/.claude/worktrees/autopilot-{goal.split()[0][:10].lower()}\n"
        f"```\n\n"
        f"## Execution Rules\n"
        f"1. Follow the plan phases IN ORDER\n"
        f"2. After completing each phase, save progress:\n"
        f"   `cc-flow skill ctx save autopilot --data '{{\"phase\": N, \"status\": \"done\", \"files_changed\": [...]}}'`\n"
        f"3. Run `cc-flow verify` after code changes\n"
        f"4. Do NOT deviate from the plan without checkpoint approval\n"
    )

    # ── Phase 3: Checkpoint template (for use during execution) ──
    # Save checkpoint data so Claude Code can trigger checkpoints
    checkpoint_data = {
        "goal": goal,
        "plan_summary": plan_text[:2000],
        "engines": {name: config for name, config in engines.items()},
        "total_phases": max_checkpoints,
        "timeout": timeout,
    }

    checkpoint_dir = TASKS_DIR / "autopilot"
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    atomic_write(
        checkpoint_dir / "active.json",
        json.dumps(checkpoint_data, indent=2, ensure_ascii=False) + "\n",
    )

    # Add checkpoint instruction
    execution_instruction += (
        "\n## Checkpoints\n"
        "After each major phase, run: `cc-flow autopilot checkpoint`\n"
        "This consults the 3-engine steering committee for guidance.\n"
        "If they say ADJUST, follow their updated instructions.\n"
        "If they say STOP, halt and report to user.\n\n"
        "## When Done\n"
        "After all phases complete:\n"
        "1. `cc-flow verify` — ensure everything passes\n"
        "2. `cc-flow review` — 3-engine adversarial debate\n"
        "3. `cc-flow commit` — if review passes\n"
        f"4. Merge worktree: `git checkout main && git merge autopilot-{goal.split()[0][:10].lower()}`\n"
        f"5. Cleanup: `cc-flow worktree remove autopilot-{goal.split()[0][:10].lower()}`\n"
    )

    elapsed = round(time.time() - start, 1)

    return {
        "success": True,
        "mode": "autopilot",
        "goal": goal,
        "engines": list(engines.keys()),
        "plan_verdict": plan_result.get("verdict", ""),
        "plan_file": plan_file,
        "elapsed_seconds": elapsed,
        "instruction": execution_instruction,
    }


# ── Checkpoint Command ──

def run_checkpoint(progress="", step=0, total=0):
    """Run a checkpoint — consult 3 engines on progress."""
    checkpoint_file = TASKS_DIR / "autopilot" / "active.json"
    if not checkpoint_file.exists():
        return {"success": False, "error": "No active autopilot session. Start with: cc-flow autopilot 'goal'"}

    data = json.loads(checkpoint_file.read_text())
    engines_config = data.get("engines", {})
    engines = {name: config for name, config in engines_config.items()}
    goal = data.get("goal", "")
    plan_summary = data.get("plan_summary", "")
    timeout = data.get("timeout", 300)

    if not engines:
        engines = _detect_engines()

    # Auto-gather progress if not provided
    if not progress:
        try:
            r = subprocess.run(
                ["git", "diff", "--shortstat"],
                check=False, capture_output=True, text=True, timeout=5,
            )
            git_status = r.stdout.strip() if r.returncode == 0 else "unknown"
            r2 = subprocess.run(
                ["git", "log", "--oneline", "-3"],
                check=False, capture_output=True, text=True, timeout=5,
            )
            recent = r2.stdout.strip() if r2.returncode == 0 else ""
            progress = f"Git: {git_status}\nRecent commits:\n{recent}"
        except (subprocess.TimeoutExpired, OSError):
            progress = "Unable to gather git status"

    if not total:
        total = data.get("total_phases", 5)

    print(json.dumps({"autopilot": "checkpoint", "step": step, "total": total}), file=sys.stderr)

    # Consult engines in parallel
    responses = _parallel_consult(
        engines,
        CHECKPOINT_PROMPT,
        {"goal": goal, "plan_summary": plan_summary, "progress": progress, "step": step, "total": total},
        timeout=min(timeout, 120),
    )

    consensus = _consensus_checkpoint(responses)

    # Build instruction for Claude Code
    guidance_text = "\n".join(consensus["guidance"]) if consensus["guidance"] else "Continue with the plan as-is."
    adjustments_text = "\n".join(consensus["adjustments"]) if consensus["adjustments"] else "No adjustments needed."

    instruction = (
        f"# Checkpoint {step}/{total}: {consensus['verdict']}\n\n"
        f"## Engine Verdicts\n"
        + "\n".join(f"  {e}: {v}" for e, v in consensus["engine_verdicts"].items())
        + f"\n\n## Next Step Guidance\n{guidance_text}"
        + f"\n\n## Plan Adjustments\n{adjustments_text}"
    )

    if consensus["verdict"] == "STOP":
        instruction += "\n\n**STOP**: Engines recommend halting. Report to user before continuing."
    elif consensus["verdict"] == "ADJUST":
        instruction += "\n\n**ADJUST**: Follow the adjusted guidance above, then continue."
    else:
        instruction += "\n\n**CONTINUE**: Proceed with the next phase of the plan."

    return {
        "success": True,
        "verdict": consensus["verdict"],
        "engine_verdicts": consensus["engine_verdicts"],
        "guidance": consensus["guidance"],
        "adjustments": consensus["adjustments"],
        "instruction": instruction,
    }


# ── CLI ──

def cmd_autopilot(args):
    """Run 3-engine guided autopilot, checkpoint, or status."""
    goal_parts = getattr(args, "goal", []) or []
    goal = " ".join(goal_parts)
    dry_run = getattr(args, "dry_run", False)
    timeout = getattr(args, "timeout", 300)

    # Subcommand detection from goal
    if goal == "checkpoint":
        progress = getattr(args, "progress", "") or ""
        step = getattr(args, "step", 0)
        total = getattr(args, "total", 0)
        result = run_checkpoint(progress=progress, step=step, total=total)
        print(json.dumps(result))
        return

    if goal == "status":
        checkpoint_file = TASKS_DIR / "autopilot" / "active.json"
        if checkpoint_file.exists():
            data = json.loads(checkpoint_file.read_text())
            print(json.dumps({"success": True, "active": True, "goal": data.get("goal", ""), "engines": list(data.get("engines", {}).keys())}))
        else:
            print(json.dumps({"success": True, "active": False}))
        return

    if not goal:
        print(json.dumps({"success": False, "error": "Usage: cc-flow autopilot 'build user auth' | cc-flow autopilot checkpoint | cc-flow autopilot status"}))
        return

    result = run_autopilot(goal, timeout=timeout, dry_run=dry_run)
    print(json.dumps(result))
