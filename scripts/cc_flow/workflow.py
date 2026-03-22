"""cc-flow workflow — define and run multi-step task pipelines.

A workflow is a named sequence of cc-flow commands executed in order.
Built-in workflows cover common development patterns.
Custom workflows are stored in .tasks/workflows/.
"""

import json
import subprocess
import sys

from cc_flow.core import TASKS_DIR, error, now_iso

WORKFLOWS_DIR = TASKS_DIR / "workflows"

BUILTIN_WORKFLOWS = {
    "feature": {
        "description": "Full feature development cycle",
        "steps": [
            {"name": "scan", "command": "scan"},
            {"name": "verify-before", "command": "verify"},
            {"name": "validate", "command": "validate"},
        ],
    },
    "release": {
        "description": "Pre-release checklist",
        "steps": [
            {"name": "verify", "command": "verify"},
            {"name": "validate", "command": "validate"},
            {"name": "changelog", "command": "changelog"},
            {"name": "report", "command": "report"},
        ],
    },
    "health": {
        "description": "Project health check",
        "steps": [
            {"name": "doctor", "command": "doctor --format json"},
            {"name": "verify", "command": "verify"},
            {"name": "stats", "command": "stats"},
        ],
    },
}


def _load_custom_workflows():
    """Load custom workflow definitions from .tasks/workflows/."""
    workflows = {}
    if WORKFLOWS_DIR.exists():
        from cc_flow.core import safe_json_load
        for f in sorted(WORKFLOWS_DIR.glob("*.json")):
            data = safe_json_load(f, default=None)
            if data:
                workflows[f.stem] = data
    return workflows


def _all_workflows():
    """Merge built-in and custom workflows."""
    workflows = dict(BUILTIN_WORKFLOWS)
    workflows.update(_load_custom_workflows())
    return workflows


def cmd_workflow_list(_args):
    """List all available workflows."""
    workflows = _all_workflows()
    result = {}
    for name, wf in workflows.items():
        source = "built-in" if name in BUILTIN_WORKFLOWS else "custom"
        result[name] = {
            "description": wf.get("description", ""),
            "steps": len(wf.get("steps", [])),
            "source": source,
        }
    print(json.dumps({"success": True, "workflows": result, "count": len(result)}))


def cmd_workflow_show(args):
    """Show workflow details."""
    name = args.name
    workflows = _all_workflows()
    if name not in workflows:
        error(f"Workflow not found: {name}. Run 'cc-flow workflow list'.")
    wf = workflows[name]
    print(json.dumps({
        "success": True, "name": name,
        "description": wf.get("description", ""),
        "steps": wf.get("steps", []),
    }))


def cmd_workflow_run(args):
    """Execute a workflow — run each step in sequence, stop on failure."""
    name = args.name
    workflows = _all_workflows()
    if name not in workflows:
        error(f"Workflow not found: {name}")

    wf = workflows[name]
    steps = wf.get("steps", [])
    dry_run = getattr(args, "dry_run", False)

    results = []
    for i, step in enumerate(steps):
        step_name = step.get("name", f"step-{i + 1}")
        command = step["command"]
        full_cmd = [sys.executable, "-m", "cc_flow", *command.split()]

        if dry_run:
            results.append({"step": step_name, "command": command, "status": "dry-run"})
            continue

        result = subprocess.run(full_cmd, check=False, capture_output=True, text=True, timeout=120)
        passed = result.returncode == 0
        results.append({
            "step": step_name, "command": command,
            "status": "pass" if passed else "fail",
            "output": result.stdout[-300:] if not passed else "",
        })
        if not passed:
            break

    all_passed = all(r["status"] in ("pass", "dry-run") for r in results)
    print(json.dumps({
        "success": all_passed,
        "workflow": name,
        "steps": results,
        "completed": len(results),
        "total": len(steps),
    }))
    if not all_passed:
        sys.exit(1)


def cmd_workflow_create(args):
    """Create a custom workflow."""
    name = args.name
    steps_raw = args.steps.split(",")
    steps = [{"name": s.strip(), "command": s.strip()} for s in steps_raw]
    description = args.description or f"Custom workflow: {name}"

    WORKFLOWS_DIR.mkdir(parents=True, exist_ok=True)
    data = {"description": description, "steps": steps, "created": now_iso()}
    (WORKFLOWS_DIR / f"{name}.json").write_text(json.dumps(data, indent=2) + "\n")

    print(json.dumps({"success": True, "name": name, "steps": len(steps)}))
