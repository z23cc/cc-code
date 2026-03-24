"""cc-flow go — one command, full automation.

Unified entry point: describe your goal → system routes, decides mode, executes.

Modes:
  chain  — lightweight skill sequence (≤ 3 required steps)
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
        from cc_flow.route_learn import _keyword_route, _q_route, ROUTE_TABLE
        # Simple keyword matching (avoid heavy imports)
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


def decide_mode(query, route_result, chain_name, chain_data, force_mode=""):
    """Decide execution mode: chain, ralph, or auto."""
    if force_mode:
        return force_mode

    query_lower = query.lower()
    words = set(query_lower.split())

    # 1. Auto mode for improvement/scan keywords
    route_cmd = (route_result or {}).get("command", "") or ""
    if route_cmd in ("/autoimmune", "auto") or words & AUTO_KEYWORDS:
        return "auto"

    # 2. Chain mode if chain found and lightweight (≤ 4 required steps)
    if chain_data:
        required = sum(1 for s in chain_data.get("skills", []) if s.get("required"))
        if required <= 4:
            return "chain"

    # 3. Ralph for everything else (complex, needs task generation)
    return "ralph"


# ── Executors ──

def _execute_chain(chain_name, chain_data, query, dry_run=False):
    """Execute a skill chain with context protocol."""
    steps = chain_data["skills"]

    # Set up chain state via skill_flow
    try:
        from cc_flow.skill_flow import save_chain_state, set_current, load_skill_ctx
    except ImportError:
        save_chain_state = set_current = load_skill_ctx = None

    if not dry_run and save_chain_state:
        save_chain_state(chain_name, steps)
        first_skill = steps[0]["skill"].lstrip("/").strip()
        set_current(first_skill, chain_name=chain_name)

    # Build step list with context
    execute_steps = []
    for i, s in enumerate(steps):
        skill_name = s["skill"].lstrip("/").strip()
        step_info = {
            "step": i + 1,
            "skill": s["skill"],
            "role": s["role"],
            "required": s["required"],
        }

        # Load prev context
        if i > 0 and load_skill_ctx:
            prev_skill = steps[i - 1]["skill"].lstrip("/").strip()
            prev_ctx = load_skill_ctx(prev_skill)
            if prev_ctx:
                step_info["prev_context"] = prev_ctx

        execute_steps.append(step_info)

    result = {
        "success": True,
        "mode": "chain",
        "chain": chain_name,
        "description": chain_data.get("description", ""),
        "goal": query,
        "dry_run": dry_run,
        "steps": execute_steps,
        "total_steps": len(steps),
        "required_steps": sum(1 for s in steps if s["required"]),
        "instruction": (
            f"Execute the '{chain_name}' chain for: {query}\n\n"
            + "\n".join(
                f"  {'[required]' if s['required'] else '[optional]'} "
                f"Step {i+1}. {s['skill']} — {s['role']}"
                for i, s in enumerate(steps)
            )
            + "\n\nStart with step 1. After each step:\n"
            + "  1. Save context: cc-flow skill ctx save <skill> --data '{...}'\n"
            + "  2. Advance: cc-flow chain advance\n"
            + "  3. Run next step"
        ),
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
    if not query:
        error("Describe your goal: cc-flow go \"what you want to achieve\"")

    force_mode = getattr(args, "mode", "") or ""
    max_iter = getattr(args, "max", 25)
    dry_run = getattr(args, "dry_run", False)

    # 1. Route
    route_result = _route(query)
    chain_name, chain_data = _find_chain(query)

    # 2. Decide
    mode = decide_mode(query, route_result, chain_name, chain_data, force_mode)

    # 3. Execute
    if mode == "chain" and chain_data:
        _execute_chain(chain_name, chain_data, query, dry_run)
    elif mode == "auto":
        _execute_auto(query, dry_run)
    else:
        # ralph (default for anything complex)
        _execute_ralph(query, max_iter, dry_run)
