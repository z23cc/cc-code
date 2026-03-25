"""cc-flow skill executor — run skills as subprocess via claude -p.

Each skill step:
  1. Read SKILL.md → extract prompt
  2. Inject context (goal, prev step output, codebase info)
  3. claude -p "prompt" → subprocess execution
  4. Parse result → save context → advance chain

Phase-aware execution:
  observe/design → claude -p (read-only, fast)
  mutate → claude -p --dangerously-skip-permissions (writes code)
  verify → subprocess (cc-flow verify / cc-flow review)
  gate → subprocess (auto_ops commit)
"""

import json
import os
import subprocess
import sys
import time
from pathlib import Path

from cc_flow.core import TASKS_DIR, atomic_write, now_iso


def _read_skill_prompt(skill_name):
    """Read SKILL.md and extract the skill prompt."""
    # Find skill directory
    plugin_root = os.environ.get("CLAUDE_PLUGIN_ROOT", "")
    candidates = [
        Path(plugin_root) / "skills" / skill_name / "SKILL.md",
        Path("skills") / skill_name / "SKILL.md",
    ]
    for path in candidates:
        if path.exists():
            content = path.read_text()
            # Strip YAML frontmatter
            if content.startswith("---"):
                end = content.find("---", 3)
                if end != -1:
                    content = content[end + 3:].strip()
            return content[:4000]  # cap to avoid huge prompts
    return None


def _build_step_prompt(skill_name, goal, role, prev_context=None, phase="mutate"):
    """Build a complete prompt for skill execution."""
    skill_prompt = _read_skill_prompt(skill_name)

    parts = [
        f"# Task: {goal}",
        f"# Your Role: {role}",
        "",
    ]

    if prev_context:
        parts.append("# Context from previous step:")
        parts.append(f"```json\n{json.dumps(prev_context, indent=2)[:2000]}\n```")
        parts.append("")

    if skill_prompt:
        parts.append(f"# Skill Instructions ({skill_name}):")
        parts.append(skill_prompt)
        parts.append("")

    if phase in ("observe", "design"):
        parts.append("# Output: Write your analysis/design as structured markdown.")
        parts.append("# Do NOT modify any files — this is a read-only analysis phase.")
    elif phase == "mutate":
        parts.append("# Execute: Implement the changes described above.")
        parts.append("# Write code, create files, run tests as needed.")
        parts.append("# Run `cc-flow verify` when done to confirm everything passes.")

    return "\n".join(parts)


def execute_step(skill_name, goal, role, phase="mutate", prev_context=None, timeout=600):
    """Execute a single skill step via claude -p subprocess.

    Returns: {success, output, duration_seconds}
    """
    prompt = _build_step_prompt(skill_name, goal, role, prev_context, phase)

    # Build claude command
    cmd = ["claude", "-p", "--output-format", "text"]

    # mutate phase needs file access
    if phase == "mutate":
        cmd.append("--dangerously-skip-permissions")

    cmd.append(prompt)

    start = time.time()
    try:
        r = subprocess.run(
            cmd, check=False, capture_output=True, text=True,
            timeout=timeout, cwd=os.getcwd(),
        )
        elapsed = round(time.time() - start, 1)
        return {
            "success": r.returncode == 0,
            "output": r.stdout[:5000],
            "error": r.stderr[:1000] if r.returncode != 0 else "",
            "duration_seconds": elapsed,
        }
    except subprocess.TimeoutExpired:
        return {"success": False, "error": f"Timeout after {timeout}s", "duration_seconds": timeout}
    except OSError as e:
        return {"success": False, "error": str(e), "duration_seconds": 0}


def execute_chain_auto(chain_name, chain_data, goal, dry_run=False, timeout=600):
    """Execute an entire chain automatically — all steps as subprocess.

    This is the fully autonomous mode: every skill step runs as a
    subprocess (claude -p), with auto-verify and auto-commit at the end.
    """
    from cc_flow.go import _group_into_phases

    steps = chain_data["skills"]
    phases = _group_into_phases(steps)

    if dry_run:
        phase_plan = []
        for pi, phase in enumerate(phases):
            method = {
                "observe": "claude -p (read-only)",
                "design": "claude -p (read-only)",
                "mutate": "claude -p --dangerously-skip-permissions",
                "verify": "cc-flow review (3-engine subprocess)",
                "gate": "auto_ops (git commit subprocess)",
            }.get(phase["phase"], "claude -p")
            skills = [s["skill"] for s in phase["steps"]]
            parallel = "PARALLEL" if phase.get("parallel") else "sequential"
            phase_plan.append(f"Phase {pi+1}: [{phase['phase'].upper()}] {parallel} → {', '.join(skills)} via {method}")

        return {
            "success": True, "dry_run": True, "chain": chain_name,
            "total_steps": len(steps), "phases": len(phases),
            "phase_plan": phase_plan,
            "instruction": (
                f"# Full Auto Execution: {chain_name}\n"
                f"Goal: {goal}\n\n"
                + "\n".join(phase_plan)
                + "\n\nEvery step runs as subprocess. Zero manual intervention."
            ),
        }

    # ── Real execution ──
    start = time.time()
    results = []
    prev_ctx = None

    print(json.dumps({"auto_exec": "start", "chain": chain_name, "steps": len(steps)}), file=sys.stderr)

    for pi, phase in enumerate(phases):
        phase_type = phase["phase"]
        phase_steps = phase["steps"]

        print(json.dumps({"auto_exec": "phase", "phase": pi + 1, "type": phase_type, "steps": len(phase_steps)}), file=sys.stderr)
        try:
            from cc_flow.dashboard_events import emit_pipeline_stage
            emit_pipeline_stage(phase_type, "started", f"Phase {pi+1}: {len(phase_steps)} steps")
        except ImportError:
            pass

        if phase_type == "verify":
            # Use unified review (3-engine subprocess)
            from cc_flow.auto_ops import auto_verify
            verify_ok = auto_verify()
            results.append({"phase": pi + 1, "type": "verify", "success": verify_ok})
            if not verify_ok:
                print(json.dumps({"auto_exec": "verify_failed"}), file=sys.stderr)
            continue

        if phase_type == "gate":
            # Auto-commit
            from cc_flow.auto_ops import auto_commit
            commit_ok = auto_commit(f"feat({chain_name}): {goal}")
            results.append({"phase": pi + 1, "type": "gate", "success": commit_ok})
            continue

        # observe/design/mutate → execute via claude -p (with failure detection)
        if phase.get("parallel") and len(phase_steps) > 1:
            # Parallel execution with ThreadPoolExecutor
            from concurrent.futures import ThreadPoolExecutor
            with ThreadPoolExecutor(max_workers=min(len(phase_steps), 3)) as pool:
                futures = {}
                for s in phase_steps:
                    skill_name = s["skill"].lstrip("/").strip()
                    futures[pool.submit(
                        execute_step, skill_name, goal, s["role"],
                        phase_type, prev_ctx, timeout,
                    )] = skill_name

                for future in futures:
                    skill_name = futures[future]
                    try:
                        step_result = future.result()
                    except Exception as e:
                        step_result = {"success": False, "error": str(e)}
                    step_result["skill"] = skill_name
                    step_result["phase"] = pi + 1
                    results.append(step_result)
        else:
            # Sequential execution with failure detection
            for s in phase_steps:
                skill_name = s["skill"].lstrip("/").strip()
                step_result = execute_step(skill_name, goal, s["role"], phase_type, prev_ctx, timeout)
                step_result["skill"] = skill_name
                step_result["phase"] = pi + 1

                if step_result.get("success"):
                    # Success → reset failures, pass context
                    try:
                        from cc_flow.failure_engine import record_success
                        record_success()
                    except ImportError:
                        pass
                    prev_ctx = {"skill": skill_name, "output_summary": step_result["output"][:1000]}
                else:
                    # Failure → record + check if methodology switch needed
                    try:
                        from cc_flow.failure_engine import diagnose_and_switch, record_failure, should_switch_methodology
                        state = record_failure(step_result.get("error", ""))
                        if should_switch_methodology(state["count"]):
                            print(json.dumps({"auto_exec": "methodology_switch", "failures": state["count"]}), file=sys.stderr)
                            switch = diagnose_and_switch(goal, timeout=120)
                            step_result["methodology_switch"] = switch
                            # Retry with new methodology injected into context
                            prev_ctx = {
                                "skill": skill_name,
                                "methodology": switch.get("methodology_name", ""),
                                "methodology_prompt": switch.get("prompt_injection", ""),
                                "first_step": switch.get("first_step", ""),
                                "diagnosis": switch.get("diagnosis", ""),
                            }
                            # Retry the step with new methodology
                            retry_result = execute_step(skill_name, goal, s["role"], phase_type, prev_ctx, timeout)
                            if retry_result.get("success"):
                                step_result = retry_result
                                step_result["retried_with"] = switch.get("methodology", "")
                    except ImportError:
                        pass

                step_result["skill"] = skill_name
                step_result["phase"] = pi + 1
                results.append(step_result)

    elapsed = round(time.time() - start, 1)
    success_count = sum(1 for r in results if r.get("success"))
    total_count = len(results)

    # Auto-learn
    try:
        from cc_flow.auto_learn import on_chain_complete
        verdict = "success" if success_count == total_count else "partial"
        on_chain_complete(chain_name, goal, success_count, total_count, verdict)
    except (ImportError, Exception):
        pass

    # Save execution log
    log_dir = TASKS_DIR / "auto_exec"
    log_dir.mkdir(parents=True, exist_ok=True)
    ts = now_iso().replace(":", "-").replace("T", "_")[:19]
    log_path = log_dir / f"{chain_name}-{ts}.json"
    atomic_write(log_path, json.dumps({
        "chain": chain_name, "goal": goal, "timestamp": now_iso(),
        "elapsed_seconds": elapsed, "results": results,
        "success": success_count, "total": total_count,
    }, indent=2, ensure_ascii=False) + "\n")

    return {
        "success": success_count == total_count,
        "chain": chain_name,
        "goal": goal,
        "elapsed_seconds": elapsed,
        "steps_success": success_count,
        "steps_total": total_count,
        "results": [{
            "skill": r.get("skill", ""),
            "phase": r.get("phase", 0),
            "success": r.get("success", False),
            "duration": r.get("duration_seconds", 0),
        } for r in results],
        "log": str(log_path),
    }
