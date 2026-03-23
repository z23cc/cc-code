"""cc-flow pipeline — skill orchestration with context passing.

Unlike workflows (which just chain CLI commands), pipelines pass
context between steps. Each step can read previous step's output
and contribute to a shared context object.

Pipeline context is stored in .tasks/pipeline_ctx.json during execution.
"""

import json
import subprocess
import sys

from cc_flow.core import TASKS_DIR, atomic_write, error, now_iso, safe_json_load

PIPELINE_CTX_FILE = TASKS_DIR / "pipeline_ctx.json"

BUILTIN_PIPELINES = {
    "review-and-fix": {
        "description": "Scan → create tasks from findings → show next steps",
        "steps": [
            {"name": "scan", "command": "auto deep", "capture": "findings"},
            {"name": "create-tasks", "action": "findings_to_tasks"},
            {"name": "show-plan", "command": "dashboard"},
        ],
    },
    "quality-gate": {
        "description": "Verify → health → evolve → pass/fail gate",
        "steps": [
            {"name": "verify", "command": "verify", "capture": "verify_result"},
            {"name": "health", "command": "health", "capture": "health_result"},
            {"name": "evolve", "command": "evolve", "capture": "evolve_result"},
            {"name": "gate", "action": "quality_gate"},
        ],
    },
    "full-audit": {
        "description": "Doctor → verify → deep scan → health → report",
        "steps": [
            {"name": "doctor", "command": "doctor --format json", "capture": "doctor_result"},
            {"name": "verify", "command": "verify", "capture": "verify_result"},
            {"name": "deep-scan", "command": "auto deep", "capture": "scan_result"},
            {"name": "health", "command": "health", "capture": "health_result"},
            {"name": "report", "command": "report"},
            {"name": "summary", "action": "audit_summary"},
        ],
    },
}


def _run_step(command, timeout=120):
    """Run a cc-flow command and capture JSON output."""
    cmd = [sys.executable, "-m", "cc_flow", *command.split()]
    try:
        result = subprocess.run(cmd, check=False, capture_output=True, text=True, timeout=timeout)
        # Try to parse last JSON line
        for line in reversed(result.stdout.split("\n")):
            if line.strip().startswith("{"):
                try:
                    return json.loads(line), result.returncode == 0
                except json.JSONDecodeError:
                    continue
        return {"output": result.stdout[-500:]}, result.returncode == 0
    except subprocess.TimeoutExpired:
        return {"error": "timeout"}, False


def _load_ctx():
    """Load pipeline context."""
    return safe_json_load(PIPELINE_CTX_FILE, default={"steps": {}, "started": now_iso()})


def _save_ctx(ctx):
    """Save pipeline context."""
    PIPELINE_CTX_FILE.parent.mkdir(parents=True, exist_ok=True)
    atomic_write(PIPELINE_CTX_FILE, json.dumps(ctx, indent=2) + "\n")


# ── Built-in actions (steps that process context, not CLI commands) ──

def _action_findings_to_tasks(ctx):
    """Convert scan findings into cc-flow tasks."""
    findings = ctx["steps"].get("scan", {}).get("findings", {})
    total = sum(v if isinstance(v, int) else len(v) for v in findings.values())
    return {"action": "findings_to_tasks", "total_findings": total,
            "instruction": f"Run: cc-flow auto scan --create-tasks ({total} findings)"}


def _action_quality_gate(ctx):
    """Check if quality metrics pass the gate."""
    verify = ctx["steps"].get("verify_result", {})
    health = ctx["steps"].get("health_result", {})

    verify_ok = verify.get("success", False)
    health_score = health.get("score", 0)

    passed = verify_ok and health_score >= 80
    return {
        "gate": "pass" if passed else "fail",
        "verify": verify_ok,
        "health_score": health_score,
        "threshold": 80,
    }


def _action_audit_summary(ctx):
    """Summarize the full audit results."""
    doctor = ctx["steps"].get("doctor_result", {})
    health = ctx["steps"].get("health_result", {})
    verify = ctx["steps"].get("verify_result", {})

    doctor_pass = sum(1 for c in doctor.get("checks", []) if c.get("status") == "pass")
    doctor_total = len(doctor.get("checks", []))

    return {
        "audit_summary": {
            "doctor": f"{doctor_pass}/{doctor_total} checks passed",
            "verify": verify.get("summary", "?"),
            "health": f"{health.get('score', '?')}/100 ({health.get('grade', '?')})",
        },
    }


_ACTIONS = {
    "findings_to_tasks": _action_findings_to_tasks,
    "quality_gate": _action_quality_gate,
    "audit_summary": _action_audit_summary,
}


# ── Pipeline runner ──

def cmd_pipeline_list(_args):
    """List available pipelines (built-in + custom)."""
    pipelines = _all_pipelines()
    result = {}
    for name, p in pipelines.items():
        source = "built-in" if name in BUILTIN_PIPELINES else "custom"
        result[name] = {"description": p["description"], "steps": len(p["steps"]), "source": source}
    print(json.dumps({"success": True, "pipelines": result, "count": len(result)}))


PIPELINES_DIR = TASKS_DIR / "pipelines"


def _all_pipelines():
    """Merge built-in and custom pipelines."""
    pipelines = dict(BUILTIN_PIPELINES)
    if PIPELINES_DIR.exists():
        for f in sorted(PIPELINES_DIR.glob("*.json")):
            data = safe_json_load(f, default=None)
            if data:
                pipelines[f.stem] = data
    return pipelines


def cmd_pipeline_create(args):
    """Create a custom pipeline."""
    name = args.name
    steps_raw = [s.strip() for s in args.steps.split(",") if s.strip()]
    steps = [{"name": s, "command": s, "capture": f"step_{i}"} for i, s in enumerate(steps_raw)]
    description = args.description or f"Custom pipeline: {name}"

    PIPELINES_DIR.mkdir(parents=True, exist_ok=True)
    data = {"description": description, "steps": steps, "created": now_iso()}
    atomic_write(PIPELINES_DIR / f"{name}.json", json.dumps(data, indent=2) + "\n")
    print(json.dumps({"success": True, "name": name, "steps": len(steps)}))


def cmd_pipeline_run(args):
    """Execute a pipeline with context passing between steps."""
    name = args.name
    pipelines = _all_pipelines()
    if name not in pipelines:
        error(f"Pipeline not found: {name}. Available: {', '.join(pipelines.keys())}")

    pipeline = pipelines[name]
    ctx = {"steps": {}, "started": now_iso(), "pipeline": name}
    results = []

    for step in pipeline["steps"]:
        step_name = step["name"]

        if "command" in step:
            data, passed = _run_step(step["command"])
            capture_key = step.get("capture", step_name)
            ctx["steps"][capture_key] = data
            results.append({"step": step_name, "type": "command",
                            "command": step["command"], "passed": passed})
        elif "action" in step:
            action_fn = _ACTIONS.get(step["action"])
            if action_fn:
                data = action_fn(ctx)
                ctx["steps"][step_name] = data
                results.append({"step": step_name, "type": "action", "data": data})

        _save_ctx(ctx)

    # Clean up context file
    if PIPELINE_CTX_FILE.exists():
        PIPELINE_CTX_FILE.unlink()

    all_passed = all(r.get("passed", True) for r in results)
    print(json.dumps({
        "success": all_passed,
        "pipeline": name,
        "steps": results,
        "completed": len(results),
        "total": len(pipeline["steps"]),
    }))
