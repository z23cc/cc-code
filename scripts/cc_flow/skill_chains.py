"""cc-flow skill chains — predefined multi-skill workflows.

Maps common development scenarios to ordered skill sequences.
Each chain defines: skills to invoke, their order, and what
context passes between them.

Used by: route (suggest chains), pipeline (execute chains).

Chain data lives in chains.json (same directory) and is loaded once at import.
"""

import json
import os

from cc_flow.core import error


def _load_skill_chains():
    """Load SKILL_CHAINS from chains.json (same directory as this module)."""
    chains_path = os.path.join(os.path.dirname(__file__), "chains.json")
    with open(chains_path, "r", encoding="utf-8") as f:
        return json.load(f)


SKILL_CHAINS = _load_skill_chains()


def find_chain(query, complexity=None):
    """Find the best matching skill chain for a query.

    Scale-adaptive: when complexity is "simple" and a -light variant exists,
    prefer the lighter chain. This skips brainstorm/plan phases for simple tasks.
    """
    ranked = _rank_chains(query)
    if not ranked:
        return None, None

    name, chain, _score = ranked[0]

    # Scale-adaptive: prefer light variant for simple tasks
    if complexity == "simple":
        light_name = f"{name}-light"
        if light_name in SKILL_CHAINS:
            return light_name, SKILL_CHAINS[light_name]

    return name, chain


def cmd_chain_list(_args):
    """List all predefined skill chains."""
    result = {}
    for name, chain in SKILL_CHAINS.items():
        result[name] = {
            "description": chain["description"],
            "skills": len(chain["skills"]),
            "required": sum(1 for s in chain["skills"] if s["required"]),
        }
    print(json.dumps({"success": True, "chains": result, "count": len(result)}))


def cmd_chain_show(args):
    """Show a skill chain's steps."""
    name = args.name
    if name not in SKILL_CHAINS:
        error(f"Chain not found: {name}. Available: {', '.join(SKILL_CHAINS.keys())}")

    chain = SKILL_CHAINS[name]
    print(json.dumps({
        "success": True,
        "name": name,
        "description": chain["description"],
        "skills": chain["skills"],
    }))


def _load_chain_metrics():
    """Load chain metrics for ranking boost. Returns {chain_name: metrics_dict}."""
    try:
        from cc_flow.skill_flow import _load_metrics
        metrics = _load_metrics()
        return metrics.get("chains", {})
    except (ImportError, Exception):
        return {}


def _rank_chains(query):
    """Rank all chains by relevance to query, boosted by historical success.

    Scoring: keyword match (0-N) + metrics bonus (0-3).
    Metrics bonus = success_rate/100 * 3 (max 3 points for 100% success rate).
    Chains with ≥3 runs get full bonus; fewer runs get proportional bonus.
    """
    query_lower = query.lower()
    words = set(query_lower.split())
    metrics = _load_chain_metrics()
    scored = []

    for name, chain in SKILL_CHAINS.items():
        score = 0
        # Keyword matching
        for trigger in chain["trigger"]:
            if trigger in query_lower:
                score += 2
            elif any(w in words for w in trigger.split()):
                score += 1

        if score > 0:
            # Metrics boost: success_rate * confidence_factor * 3
            m = metrics.get(name, {})
            runs = m.get("runs", 0)
            success_rate = m.get("success_rate", 0)
            if runs > 0:
                # Confidence grows with runs: 0.33 at 1 run, 0.67 at 2, 1.0 at 3+
                confidence = min(runs / 3.0, 1.0)
                bonus = (success_rate / 100.0) * confidence * 3.0
                score += bonus

            scored.append((name, chain, score))

    scored.sort(key=lambda x: -x[2])
    return scored


def cmd_chain_suggest(args):
    """Suggest the best skill chain(s) for a task description."""
    query = " ".join(args.query) if args.query else ""
    if not query:
        error("Provide a task description")

    ranked = _rank_chains(query)
    if not ranked:
        print(json.dumps({
            "success": True,
            "suggestion": None,
            "message": "No matching chain. Try: cc-flow chain list",
        }))
        return

    best_name, best_chain, best_score = ranked[0]

    # Include metrics for best chain
    metrics = _load_chain_metrics()
    best_metrics = metrics.get(best_name, {})

    result = {
        "success": True,
        "chain": best_name,
        "description": best_chain["description"],
        "score": round(best_score, 1),
        "steps": [
            f"{'[required]' if s['required'] else '[optional]'} {s['skill']} — {s['role']}"
            for s in best_chain["skills"]
        ],
        "instruction": f"Run: cc-flow go \"{query}\"  (or: cc-flow chain run {best_name})",
    }

    if best_metrics:
        result["history"] = {
            "runs": best_metrics.get("runs", 0),
            "success_rate": best_metrics.get("success_rate", 0),
            "last_completed": best_metrics.get("last_completed", ""),
        }

    # Show alternatives if close in score
    if len(ranked) > 1:
        alts = []
        for name, chain, score in ranked[1:3]:
            if score >= best_score * 0.5:
                alt = {"chain": name, "description": chain["description"], "score": round(score, 1)}
                m = metrics.get(name, {})
                if m:
                    alt["success_rate"] = m.get("success_rate", 0)
                alts.append(alt)
        if alts:
            result["alternatives"] = alts

    print(json.dumps(result))


def _skill_name_from_cmd(cmd):
    """Extract skill name from command string like '/cc-brainstorm'."""
    return cmd.lstrip("/").strip()


def cmd_chain_run(args):
    """Execute a skill chain — context-aware step-by-step instructions.

    Each step includes context loaded from the previous step's output.
    Chain state is persisted for resume via `cc-flow chain advance`.
    """
    name = args.name
    if name not in SKILL_CHAINS:
        error(f"Chain not found: {name}. Available: {', '.join(SKILL_CHAINS.keys())}")

    chain = SKILL_CHAINS[name]
    only_required = getattr(args, "required_only", False)

    steps = chain["skills"]
    if only_required:
        steps = [s for s in steps if s["required"]]

    # Load context from previous skills and save chain state
    try:
        from cc_flow.skill_flow import (
            load_skill_ctx,
            record_chain_start,
            save_chain_state,
            set_current,
        )
        # Save chain state for resume
        save_chain_state(name, steps, current_step=0)
        # Set first skill as current
        first_skill = _skill_name_from_cmd(steps[0]["skill"])
        set_current(first_skill, chain_name=name)
        # Record metrics
        record_chain_start(name)
    except ImportError:
        pass

    execute_steps = []
    for i, s in enumerate(steps):
        skill_name = _skill_name_from_cmd(s["skill"])
        step_info = {
            "step": i + 1,
            "skill": s["skill"],
            "role": s["role"],
            "required": s["required"],
            "instruction": f"Run: {s['skill']}",
        }

        # Load context from previous step
        if i > 0:
            prev_skill = _skill_name_from_cmd(steps[i - 1]["skill"])
            try:
                prev_ctx = load_skill_ctx(prev_skill)
                if prev_ctx:
                    step_info["prev_context"] = prev_ctx
            except (ImportError, Exception):
                pass

        # Add context-save reminder
        step_info["on_completion"] = (
            f"After completing this step, save context:\n"
            f"  cc-flow skill ctx save {skill_name} --data '{{...}}'\n"
            f"Then advance the chain:\n"
            f"  cc-flow chain advance"
        )

        execute_steps.append(step_info)

    print(json.dumps({
        "success": True,
        "chain": name,
        "description": chain["description"],
        "execute": execute_steps,
        "total_steps": len(steps),
        "instruction": (
            f"Execute this {name} chain step by step:\n"
            + "\n".join(
                f"  {i + 1}. {s['skill']} — {s['role']}"
                for i, s in enumerate(steps)
            )
            + "\n\nAfter each step: save context with `cc-flow skill ctx save <name> --data '{{...}}'`"
            + "\nThen advance: `cc-flow chain advance`"
        ),
    }))


def cmd_chain_advance(args):
    """Advance chain to the next step after current step completes.

    Optionally saves context data from the completed step.
    Returns the next step info or signals chain completion.
    """
    try:
        from cc_flow.skill_flow import (
            advance_chain_state,
            load_chain_state,
            load_skill_ctx,
            record_chain_complete,
            save_skill_ctx,
            set_current,
        )
    except ImportError:
        error("skill_flow module not available")

    state = load_chain_state()
    if not state:
        error("No active chain. Start one with: cc-flow chain run <name>")

    chain_name = state.get("chain", "")
    current_step = state.get("current_step", 0)
    step_skills = state.get("steps", [])

    # Save context from completed step if --data provided
    data_str = getattr(args, "data", "{}")
    saved_keys = []
    if data_str and data_str != "{}":
        try:
            data = json.loads(data_str)
            if current_step < len(step_skills):
                completed_skill = _skill_name_from_cmd(step_skills[current_step])
                save_skill_ctx(completed_skill, data)
                saved_keys = list(data.keys())
        except (json.JSONDecodeError, Exception):
            pass

    # Schema validation: check if saved context has expected output keys
    schema_warnings = []
    if chain_name in SKILL_CHAINS and current_step < len(SKILL_CHAINS[chain_name]["skills"]):
        step_def = SKILL_CHAINS[chain_name]["skills"][current_step]
        expected_outputs = step_def.get("outputs", [])
        if expected_outputs and saved_keys:
            missing = [k for k in expected_outputs if k not in saved_keys]
            if missing:
                schema_warnings.append(
                    f"Missing expected context keys: {', '.join(missing)} "
                    f"(expected: {', '.join(expected_outputs)})",
                )

    # Advance to next step
    new_state = advance_chain_state()
    if not new_state:
        error("No active chain state")

    if new_state.get("complete"):
        # Record metrics
        total = state.get("total_steps", 0)
        try:
            record_chain_complete(chain_name, total, total)
        except Exception:
            pass

        # Auto-record wisdom
        try:
            from cc_flow.wisdom import record_chain_wisdom
            record_chain_wisdom(chain_name, "success", total)
        except (ImportError, Exception):
            pass

        # Auto-learn: feed all subsystems
        try:
            from cc_flow.auto_learn import on_chain_complete
            on_chain_complete(chain_name, chain_name, total, total, "success")
        except (ImportError, Exception):
            pass

        # Auto-ops: verify + commit on chain completion
        verify_ok = False
        commit_ok = False
        try:
            from cc_flow.auto_ops import auto_commit, auto_verify
            verify_ok = auto_verify()
            if verify_ok:
                commit_ok = auto_commit(f"feat: {chain_name} chain completed ({total} steps)")
        except (ImportError, Exception):
            pass

        print(json.dumps({
            "success": True,
            "complete": True,
            "chain": chain_name,
            "message": f"Chain '{chain_name}' complete! All steps finished.",
            "auto_verify": verify_ok,
            "auto_commit": commit_ok,
            "wisdom_recorded": True,
        }))
        return

    # Checkpoint gate: run quality check at configured intervals
    checkpoint_result = None
    try:
        from cc_flow.wisdom import run_checkpoint, should_checkpoint
        total = state.get("total_steps", 0)
        if should_checkpoint(chain_name, current_step, total):
            checkpoint_result = run_checkpoint(chain_name, current_step)
    except (ImportError, Exception):
        pass

    # Get next step info from chain definition
    next_step_idx = new_state["current_step"]
    if chain_name in SKILL_CHAINS:
        chain = SKILL_CHAINS[chain_name]
        steps = chain["skills"]
        if next_step_idx < len(steps):
            next_step = steps[next_step_idx]
            next_skill = _skill_name_from_cmd(next_step["skill"])

            # Set as current skill
            set_current(next_skill, chain_name=chain_name)

            # Load context from previous step
            prev_ctx = None
            if next_step_idx > 0:
                prev_skill = _skill_name_from_cmd(steps[next_step_idx - 1]["skill"])
                prev_ctx = load_skill_ctx(prev_skill)

            # Check if next step's reads are satisfied
            reads_check = []
            next_reads = next_step.get("reads", [])
            if next_reads and prev_ctx:
                missing_reads = [k for k in next_reads if k not in prev_ctx]
                if missing_reads:
                    reads_check.append(
                        f"Next step expects: {', '.join(next_reads)}. "
                        f"Missing: {', '.join(missing_reads)}",
                    )

            result = {
                "success": True,
                "chain": chain_name,
                "step": next_step_idx + 1,
                "total_steps": len(steps),
                "skill": next_step["skill"],
                "role": next_step["role"],
                "required": next_step["required"],
                "instruction": f"NEXT -> Run: {next_step['skill']} — {next_step['role']}",
            }
            if prev_ctx:
                result["prev_context"] = prev_ctx
            if schema_warnings:
                result["schema_warnings"] = schema_warnings
            if reads_check:
                result["reads_warnings"] = reads_check
            if checkpoint_result:
                result["checkpoint"] = checkpoint_result

            print(json.dumps(result))
            return

    # Fallback: just show step number
    print(json.dumps({
        "success": True,
        "chain": chain_name,
        "step": next_step_idx + 1,
        "message": f"Advanced to step {next_step_idx + 1}",
    }))
