"""cc-flow go — one command, full automation.

Unified entry point: describe your goal → system routes, decides mode, executes.

Modes:
  chain  — lightweight skill sequence (≤ 4 required steps), auto-executed
  ralph  — autonomous goal-driven execution (complex goals, creates tasks)
  auto   — OODA improvement loop (scan → fix → test)
"""

import json
import os
import subprocess
import sys

from cc_flow.core import error, now_iso


# ── Routing ──

def _route(query):
    """Route a query to the best command. Returns route result dict."""
    try:
        from cc_flow.route_learn import ROUTE_TABLE
        query_lower = query.lower()
        words = set(query_lower.split())

        best = None
        best_score = 0
        for keywords, cmd, team, desc in ROUTE_TABLE:
            score = 0
            for kw in keywords:
                if kw in query_lower:
                    score += 2
                elif any(w in words for w in kw.split()):
                    score += 1
            if score > best_score:
                best_score = score
                best = {"command": cmd, "team": team, "description": desc, "score": score}

        return best or {"command": None, "team": None, "description": "No route match", "score": 0}
    except ImportError:
        return {"command": None, "score": 0}


def _find_chain(query):
    """Find the best matching skill chain."""
    try:
        from cc_flow.skill_chains import find_chain
        name, data = find_chain(query)
        return name, data
    except ImportError:
        return None, None


# ── Mode decision ──

AUTO_KEYWORDS = {"improve", "autoimmune", "auto", "scan", "lint", "quality",
                 "改进", "自动", "扫描", "质量"}

HOTFIX_KEYWORDS = {"hotfix", "typo", "trivial", "one-liner", "urgent", "revert",
                   "quick fix", "config change", "bump version", "emergency",
                   "紧急", "快速修复", "小改动", "回滚"}


COMPLEX_KEYWORDS = {"architecture", "system", "platform", "redesign", "rewrite",
                     "multi-service", "microservice", "monorepo", "migrate",
                     "架构", "系统", "平台", "重写", "微服务"}


def _estimate_complexity(query, chain_data):
    """Estimate task complexity: simple, medium, complex.

    Signals:
      simple  — short query, hotfix keywords, chain ≤ 3 steps
      medium  — standard chain (3-5 steps), specific task
      complex — long query, architecture keywords, no chain match, multi-system
    """
    words = set(query.lower().split())
    word_count = len(words)

    # Hotfix keywords → simple
    if words & HOTFIX_KEYWORDS:
        return "simple"

    # Complex keywords → complex
    if words & COMPLEX_KEYWORDS:
        return "complex"

    # Long queries (>10 words) tend to be complex
    if word_count > 10:
        return "complex"

    # Short queries with chain match → medium
    if chain_data:
        required = sum(1 for s in chain_data.get("skills", []) if s.get("required"))
        if required <= 3:
            return "simple"
        return "medium"

    # No chain match + moderate length → complex
    if word_count > 5:
        return "complex"

    return "medium"


def decide_mode(query, route_result, chain_name, chain_data, force_mode=""):
    """Decide execution mode based on complexity-adaptive routing.

    Simple  → hotfix chain (3 steps, skip brainstorm/plan)
    Medium  → standard chain (matched chain, ≤5 steps)
    Complex → Ralph (autonomous, creates tasks from goal)
    Auto    → OODA loop (scan/improve keywords)
    """
    if force_mode:
        return force_mode

    query_lower = query.lower()
    words = set(query_lower.split())

    # 1. Auto mode for improvement/scan keywords
    route_cmd = (route_result or {}).get("command", "") or ""
    if route_cmd in ("/autoimmune", "auto") or words & AUTO_KEYWORDS:
        return "auto"

    # 2. Estimate complexity
    complexity = _estimate_complexity(query, chain_data)

    # 3. Route by complexity
    if complexity == "simple":
        return "chain"  # hotfix or small chain

    if complexity == "medium" and chain_data:
        required = sum(1 for s in chain_data.get("skills", []) if s.get("required"))
        if required <= 5:
            return "chain"

    if complexity == "complex":
        # Complex with a matching chain → still use chain if ≤5 steps
        if chain_data:
            required = sum(1 for s in chain_data.get("skills", []) if s.get("required"))
            if required <= 5:
                return "chain"
        # Otherwise → Ralph
        return "ralph"

    # Fallback: chain if available, ralph otherwise
    if chain_data:
        return "chain"
    return "ralph"


# ── Chain auto-execution instruction builder ──

def _build_auto_exec_instruction(chain_name, chain_data, query, steps):
    """Build a self-contained instruction that Claude follows step by step.

    The key insight: Claude reads this instruction and executes each step
    automatically, calling cc-flow commands between steps. No manual
    intervention needed.
    """
    lines = [
        f"# AUTO-EXECUTE: {chain_name} chain",
        f"Goal: {query}",
        "",
        "Execute these steps IN ORDER. After each step, save context and advance.",
        "Do NOT stop between steps — continue automatically until all steps are done.",
        "",
    ]

    for i, s in enumerate(steps):
        skill_name = s["skill"].lstrip("/").strip()
        required_tag = "REQUIRED" if s["required"] else "OPTIONAL"
        outputs = s.get("outputs", [])
        reads = s.get("reads", [])

        lines.append(f"## Step {i+1}/{len(steps)}: {s['skill']} [{required_tag}]")
        lines.append(f"Role: {s['role']}")

        if reads:
            lines.append(f"Reads from previous step: {', '.join(reads)}")
            lines.append(f"Load context: `cc-flow skill ctx load {steps[i-1]['skill'].lstrip('/').strip()}`")

        lines.append(f"Action: Activate the {skill_name} skill and execute it for: {query}")

        if outputs:
            ctx_json = ", ".join(f'"{k}": "..."' for k in outputs)
            lines.append(f"On completion, save: `cc-flow skill ctx save {skill_name} --data '{{{ctx_json}}}'`")
        else:
            lines.append(f"On completion: `cc-flow skill ctx save {skill_name} --data '{{\"done\": true}}'`")

        lines.append(f"Then advance: `cc-flow chain advance`")
        lines.append("")

    lines.append("## On Chain Complete")
    lines.append(f"All {len(steps)} steps done. The chain will auto-report completion.")
    lines.append(f"Record learning: `cc-flow learn --task '{chain_name}: {query}' --outcome success`")

    return "\n".join(lines)


# ── Resume logic ──

def _check_resume():
    """Check if there's an interrupted chain to resume. Returns state or None."""
    try:
        from cc_flow.skill_flow import load_chain_state, load_skill_ctx, CHAIN_STATE_FILE
        if not CHAIN_STATE_FILE.exists():
            return None
        state = load_chain_state()
        if state and not state.get("complete"):
            return state
    except ImportError:
        pass
    return None


def _execute_resume(state):
    """Resume an interrupted chain from the current step."""
    from cc_flow.skill_flow import set_current, load_skill_ctx
    from cc_flow.skill_chains import SKILL_CHAINS

    chain_name = state.get("chain", "")
    current_step = state.get("current_step", 0)
    total_steps = state.get("total_steps", 0)
    step_skills = state.get("steps", [])

    chain_data = SKILL_CHAINS.get(chain_name)
    if not chain_data:
        print(json.dumps({
            "success": False,
            "error": f"Chain '{chain_name}' not found. Clear with: cc-flow skill ctx clear",
        }))
        return

    steps = chain_data["skills"]
    remaining = steps[current_step:]

    # Set current skill
    if remaining:
        skill_name = remaining[0]["skill"].lstrip("/").strip()
        set_current(skill_name, chain_name=chain_name)

    # Load previous step context if available
    prev_ctx = None
    if current_step > 0:
        prev_skill = steps[current_step - 1]["skill"].lstrip("/").strip()
        prev_ctx = load_skill_ctx(prev_skill)

    instruction = _build_auto_exec_instruction(
        chain_name, chain_data, f"(resumed from step {current_step + 1})", remaining
    )

    result = {
        "success": True,
        "mode": "chain",
        "resumed": True,
        "chain": chain_name,
        "resumed_from_step": current_step + 1,
        "total_steps": total_steps,
        "remaining_steps": len(remaining),
        "instruction": instruction,
    }

    if prev_ctx:
        result["prev_context"] = prev_ctx

    print(json.dumps(result))


# ── Executors ──

def _execute_chain(chain_name, chain_data, query, dry_run=False, complexity="medium"):
    """Execute a skill chain with full auto-execution protocol."""
    steps = chain_data["skills"]

    # Set up chain state via skill_flow
    try:
        from cc_flow.skill_flow import (
            save_chain_state, set_current, load_skill_ctx, record_chain_start,
        )
    except ImportError:
        save_chain_state = set_current = load_skill_ctx = record_chain_start = None

    if not dry_run and save_chain_state:
        save_chain_state(chain_name, steps)
        first_skill = steps[0]["skill"].lstrip("/").strip()
        set_current(first_skill, chain_name=chain_name)
        if record_chain_start:
            record_chain_start(chain_name)

    # Build step list with context
    execute_steps = []
    for i, s in enumerate(steps):
        step_info = {
            "step": i + 1,
            "skill": s["skill"],
            "role": s["role"],
            "required": s["required"],
        }
        if "outputs" in s:
            step_info["outputs"] = s["outputs"]
        if "reads" in s:
            step_info["reads"] = s["reads"]

        # Load prev context
        if i > 0 and load_skill_ctx:
            prev_skill = steps[i - 1]["skill"].lstrip("/").strip()
            prev_ctx = load_skill_ctx(prev_skill)
            if prev_ctx:
                step_info["prev_context"] = prev_ctx

        execute_steps.append(step_info)

    # Build auto-execution instruction
    instruction = _build_auto_exec_instruction(chain_name, chain_data, query, steps)

    result = {
        "success": True,
        "mode": "chain",
        "complexity": complexity,
        "chain": chain_name,
        "description": chain_data.get("description", ""),
        "goal": query,
        "dry_run": dry_run,
        "steps": execute_steps,
        "total_steps": len(steps),
        "required_steps": sum(1 for s in steps if s["required"]),
        "instruction": instruction,
    }

    print(json.dumps(result))


def _execute_ralph(query, max_iterations=25, dry_run=False):
    """Launch Ralph in goal-driven autonomous mode."""
    if dry_run:
        print(json.dumps({
            "success": True,
            "mode": "ralph",
            "goal": query,
            "max_iterations": max_iterations,
            "dry_run": True,
            "instruction": (
                f"Ralph will autonomously execute: {query}\n"
                f"  - Creates epic + tasks from goal\n"
                f"  - Fresh Claude session per iteration\n"
                f"  - Self-healing on failures\n"
                f"  - Max {max_iterations} iterations\n"
                f"  - Receipt-based proof-of-work"
            ),
        }))
        return

    # Delegate to ralph_cmd
    try:
        from cc_flow.ralph_cmd import _find_ralph_sh, _init_ralph
    except ImportError:
        error("Ralph module not available")

    ralph_dir = _init_ralph(query)
    ralph_sh = ralph_dir / "ralph.sh"

    if not ralph_sh.is_file():
        sh = _find_ralph_sh()
        if not sh:
            error("Ralph not found. Install: cc-flow ralph --init")
        ralph_sh = sh

    env = os.environ.copy()
    env["GOAL"] = query
    env["SELF_HEAL"] = "1"
    env["GOAL_VERIFY"] = "tests"
    env["MAX_ITERATIONS"] = str(max_iterations)
    env["YOLO"] = "1"

    print(json.dumps({
        "starting": True,
        "mode": "ralph",
        "goal": query,
        "max_iterations": max_iterations,
        "instruction": (
            f"Launching Ralph autonomous execution for: {query}\n"
            f"Ralph will create tasks and execute until goal achieved or {max_iterations} iterations.\n"
            f"Monitor: tail -f scripts/ralph/runs/latest/progress.log\n"
            f"Pause: touch scripts/ralph/PAUSE\n"
            f"Stop: touch scripts/ralph/STOP"
        ),
    }))

    try:
        result = subprocess.run(["bash", str(ralph_sh)], env=env, cwd=os.getcwd())
        sys.exit(result.returncode)
    except KeyboardInterrupt:
        print("\nRalph interrupted.")
        sys.exit(130)


def _execute_auto(query, dry_run=False):
    """Run OODA auto-improvement loop."""
    if dry_run:
        print(json.dumps({
            "success": True,
            "mode": "auto",
            "goal": query,
            "dry_run": True,
            "instruction": (
                f"Auto-improvement loop for: {query}\n"
                f"  Phase 1: OBSERVE — scan for lint, type, test issues\n"
                f"  Phase 2: DECIDE — pick next task, recommend team\n"
                f"  Phase 3: ACT — auto-fix lint, run tests\n"
                f"  Loop until clean"
            ),
        }))
        return

    # Delegate to auto full
    cmd = [sys.executable, "-m", "cc_flow", "auto", "full"]
    print(json.dumps({
        "starting": True,
        "mode": "auto",
        "goal": query,
        "instruction": "Running: cc-flow auto full (scan → fix → test)",
    }))

    try:
        result = subprocess.run(cmd, cwd=os.getcwd())
        sys.exit(result.returncode)
    except KeyboardInterrupt:
        sys.exit(130)


# ── Main command ──

def cmd_go(args):
    """One command, full automation: describe your goal, everything runs."""
    query = " ".join(args.goal) if args.goal else ""
    force_mode = getattr(args, "mode", "") or ""
    max_iter = getattr(args, "max", 25)
    dry_run = getattr(args, "dry_run", False)
    resume = getattr(args, "resume", False)

    # Resume mode: continue interrupted chain
    if resume:
        state = _check_resume()
        if state:
            _execute_resume(state)
            return
        print(json.dumps({"success": False, "error": "No interrupted chain to resume."}))
        return

    if not query:
        # Check for interrupted chain even without --resume
        state = _check_resume()
        if state:
            chain = state.get("chain", "?")
            step = state.get("current_step", 0) + 1
            total = state.get("total_steps", 0)
            print(json.dumps({
                "success": False,
                "error": f"No goal specified. (Interrupted chain '{chain}' at step {step}/{total} — use --resume to continue)",
            }))
            return
        error("Describe your goal: cc-flow go \"what you want to achieve\"")

    # 1. Route
    route_result = _route(query)
    chain_name, chain_data = _find_chain(query)

    # 2. Decide
    complexity = _estimate_complexity(query, chain_data)
    mode = decide_mode(query, route_result, chain_name, chain_data, force_mode)

    # 3. Execute (pass complexity for output)
    if mode == "chain" and chain_data:
        _execute_chain(chain_name, chain_data, query, dry_run, complexity=complexity)
    elif mode == "auto":
        _execute_auto(query, dry_run)
    else:
        # ralph (default for anything complex)
        _execute_ralph(query, max_iter, dry_run)
