"""cc-flow failure engine — 3-engine methodology switching on failures.

When agents get stuck, instead of looping forever:
  1. Detect consecutive failures (track count)
  2. At threshold → 3 engines diagnose WHY stuck (parallel)
  3. Vote on best methodology switch
  4. Apply new methodology → continue
  5. Still stuck → escalate (different methodology, then halt)

Methodologies:
  RCA (Root Cause Analysis) — systematic 5-why, trace data flow
  Simplify (Musk Algorithm) — question requirements, delete, simplify, accelerate
  Invert — solve the opposite problem, work backwards
  First Principles — ignore all assumptions, rebuild from basics
  Divide — split into smallest possible subproblems
"""

import json
import shutil
import subprocess
from concurrent.futures import ThreadPoolExecutor

from cc_flow.core import TASKS_DIR, atomic_write, now_iso

# ── Failure Tracking ──

FAILURE_FILE = TASKS_DIR / "failure_state.json"

METHODOLOGIES = {
    "rca": {
        "name": "Root Cause Analysis",
        "prompt": (
            "Use the 5-Why method. Ask 'why' 5 times to find the root cause. "
            "Trace data flow step by step. Verify each hypothesis with evidence."
        ),
    },
    "simplify": {
        "name": "Simplify (Musk Algorithm)",
        "prompt": (
            "1. Question every requirement. 2. Delete unnecessary parts. "
            "3. Simplify what remains. 4. Accelerate. 5. Automate last."
        ),
    },
    "invert": {
        "name": "Inversion",
        "prompt": (
            "Solve the OPPOSITE problem. What would make this WORSE? "
            "Avoid those things. Work backwards from desired end state."
        ),
    },
    "first_principles": {
        "name": "First Principles",
        "prompt": (
            "Forget all assumptions. What are the fundamental truths? "
            "Build from scratch using only verified facts."
        ),
    },
    "divide": {
        "name": "Divide & Conquer",
        "prompt": (
            "Split into SMALLEST independent subproblems. "
            "Solve each separately. Combine. Split again if still hard."
        ),
    },
}

# Escalation chain: try these in order when stuck
METHODOLOGY_CHAIN = ["rca", "simplify", "invert", "first_principles", "divide"]


def get_failure_state():
    """Load current failure tracking state."""
    if FAILURE_FILE.exists():
        try:
            return json.loads(FAILURE_FILE.read_text())
        except (json.JSONDecodeError, OSError):
            pass
    return {"count": 0, "history": [], "current_methodology": None, "methodology_index": 0}


def record_failure(error_msg=""):
    """Record a failure. Returns current state with escalation info."""
    state = get_failure_state()
    state["count"] += 1
    state["history"].append({"time": now_iso(), "error": error_msg[:200]})
    state["history"] = state["history"][-10:]  # keep last 10

    FAILURE_FILE.parent.mkdir(parents=True, exist_ok=True)
    atomic_write(FAILURE_FILE, json.dumps(state, indent=2) + "\n")
    return state


def record_success():
    """Reset failure count on success."""
    state = {"count": 0, "history": [], "current_methodology": None, "methodology_index": 0}
    FAILURE_FILE.parent.mkdir(parents=True, exist_ok=True)
    atomic_write(FAILURE_FILE, json.dumps(state, indent=2) + "\n")


def should_switch_methodology(failure_count):
    """Check if failure count warrants methodology switch."""
    return failure_count >= 2


# ── 3-Engine Diagnosis ──

DIAGNOSIS_PROMPT = """\
You are **{label}** diagnosing why an agent is stuck.

The agent has failed {count} consecutive times on this goal: "{goal}"

Recent errors:
{errors}

Current methodology: {current_method}

Available methodologies:
{methods_list}

Analyze:
1. WHY is the agent stuck? (root cause, not symptoms)
2. Which methodology would BREAK the loop?
3. What specific first step should the agent try?

Respond with ONLY JSON:
{{"diagnosis": "why stuck in 1 sentence", "recommended_method": "<method_id>", "first_step": "specific action to try", "confidence": 0.0-1.0}}"""


def _exec_engine(engine, prompt, timeout=300):
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
        # Codex outputs to stderr
        raw = (r.stderr or "") + "\n" + (r.stdout or "") if engine == "codex" else r.stdout
        output = raw.strip()
        # Try to parse JSON from output
        import re
        json_match = re.search(r'\{[^{}]*"recommended_method"[^{}]*\}', output)
        if json_match:
            return json.loads(json_match.group())
    except (subprocess.TimeoutExpired, OSError, json.JSONDecodeError):
        pass
    return None


def diagnose_and_switch(goal, timeout=300):
    """3 engines diagnose why stuck and vote on methodology switch.

    Returns: {methodology, diagnosis, first_step, engine_votes}
    """
    state = get_failure_state()
    current_idx = state.get("methodology_index", 0)
    current_method = METHODOLOGY_CHAIN[current_idx] if current_idx < len(METHODOLOGY_CHAIN) else "rca"

    errors = "\n".join(
        f"  - {h.get('error', '?')}" for h in state.get("history", [])[-5:]
    ) or "  (no error details)"

    methods_list = "\n".join(
        f"  - {mid}: {m['name']} — {m['prompt'][:80]}..."
        for mid, m in METHODOLOGIES.items()
    )

    # Detect available engines
    engines = {}
    if shutil.which("claude"):
        engines["claude"] = "Claude"
    if shutil.which("codex"):
        engines["codex"] = "Codex"
    if shutil.which("gemini") or shutil.which("gemini-cli"):
        engines["gemini"] = "Gemini"

    if not engines:
        # No engines — just advance methodology chain
        next_idx = min(current_idx + 1, len(METHODOLOGY_CHAIN) - 1)
        next_method = METHODOLOGY_CHAIN[next_idx]
        state["methodology_index"] = next_idx
        state["current_methodology"] = next_method
        atomic_write(FAILURE_FILE, json.dumps(state, indent=2) + "\n")
        return {
            "methodology": next_method,
            "methodology_name": METHODOLOGIES[next_method]["name"],
            "prompt_injection": METHODOLOGIES[next_method]["prompt"],
            "diagnosis": "No engines available for diagnosis",
            "first_step": "Try a different approach",
        }

    # 3-engine parallel diagnosis
    votes = {}
    with ThreadPoolExecutor(max_workers=len(engines)) as pool:
        futures = {}
        for engine_name, label in engines.items():
            prompt = DIAGNOSIS_PROMPT.format(
                label=label, count=state["count"], goal=goal,
                errors=errors, current_method=METHODOLOGIES.get(current_method, {}).get("name", "none"),
                methods_list=methods_list,
            )
            futures[pool.submit(_exec_engine, engine_name, prompt, timeout)] = engine_name

        for future in futures:
            engine_name = futures[future]
            try:
                result = future.result()
                if result:
                    votes[engine_name] = result
            except Exception:
                pass

    # Tally votes
    method_votes = {}
    diagnoses = []
    first_steps = []
    for engine_name, vote in votes.items():
        method = vote.get("recommended_method", "")
        if method in METHODOLOGIES:
            method_votes[method] = method_votes.get(method, 0) + 1
        if vote.get("diagnosis"):
            diagnoses.append(f"[{engine_name}] {vote['diagnosis']}")
        if vote.get("first_step"):
            first_steps.append(vote["first_step"])

    # Pick winner (majority, or advance chain if no consensus)
    if method_votes:
        winner = max(method_votes, key=method_votes.get)
    else:
        next_idx = min(current_idx + 1, len(METHODOLOGY_CHAIN) - 1)
        winner = METHODOLOGY_CHAIN[next_idx]

    # Update state
    state["current_methodology"] = winner
    state["methodology_index"] = METHODOLOGY_CHAIN.index(winner) if winner in METHODOLOGY_CHAIN else 0
    state["count"] = 0  # reset on methodology switch
    atomic_write(FAILURE_FILE, json.dumps(state, indent=2) + "\n")

    return {
        "methodology": winner,
        "methodology_name": METHODOLOGIES[winner]["name"],
        "prompt_injection": METHODOLOGIES[winner]["prompt"],
        "diagnosis": " | ".join(diagnoses) if diagnoses else "Engines could not diagnose",
        "first_step": first_steps[0] if first_steps else "Try the new methodology",
        "engine_votes": method_votes,
        "engines_consulted": list(votes.keys()),
    }


# ── CLI ──

def cmd_failure(args):
    """Failure engine: track failures and trigger methodology switch."""
    subcmd = args.failure_cmd if hasattr(args, "failure_cmd") else ""

    if subcmd == "status":
        state = get_failure_state()
        state["threshold"] = 2
        print(json.dumps({"success": True, **state}))
    elif subcmd == "record":
        error_msg = getattr(args, "error", "") or ""
        state = record_failure(error_msg)
        if should_switch_methodology(state["count"]):
            print(json.dumps({"success": True, "escalation": True, "count": state["count"],
                              "message": "Failure threshold reached. Run: cc-flow failure diagnose --goal 'your goal'"}))
        else:
            print(json.dumps({"success": True, "count": state["count"]}))
    elif subcmd == "diagnose":
        goal = getattr(args, "goal", "") or "unknown"
        result = diagnose_and_switch(goal)
        print(json.dumps({"success": True, **result}))
    elif subcmd == "reset":
        record_success()
        print(json.dumps({"success": True, "message": "Failure state reset"}))
    else:
        state = get_failure_state()
        print(json.dumps({"success": True, **state}))
