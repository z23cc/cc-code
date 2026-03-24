"""cc-flow wf — cc-wf-studio workflow executor.

Runs cc-wf-studio visual workflow JSON files natively in cc-code.
Parses the DAG, topological-sorts nodes, executes each node type,
and passes context between steps.

Supported node types:
  start/end     — flow control (no-op)
  subAgent      — dispatch agent with prompt (→ Agent tool)
  skill         — invoke a cc-code skill (→ /cc-<name>)
  prompt        — display instructions to user
  askUserQuestion — interactive branch
  ifElse/switch — conditional routing
  mcp           — call MCP tool

Usage:
  cc-flow wf run <path.json>          Run a workflow
  cc-flow wf run <path.json> --dry-run  Preview execution plan
  cc-flow wf list                      List .vscode/workflows/*.json
  cc-flow wf export <chain-name>       Export cc-code chain as workflow JSON
"""

import json
import os
import uuid
from pathlib import Path

from cc_flow.core import TASKS_DIR, atomic_write, error, now_iso, safe_json_load


WORKFLOWS_DIR = Path(".vscode/workflows")


# ── Workflow parsing ──

def _load_workflow(path):
    """Load and validate a workflow JSON file."""
    p = Path(path)
    if not p.exists():
        # Try .vscode/workflows/
        p = WORKFLOWS_DIR / path
        if not p.exists():
            p = WORKFLOWS_DIR / f"{path}.json"
    if not p.exists():
        error(f"Workflow not found: {path}")
    data = safe_json_load(p, default=None)
    if not data or "nodes" not in data:
        error(f"Invalid workflow file: {p}")
    return data, p


def _topo_sort(nodes, connections):
    """Topological sort of workflow nodes by connections.

    Returns ordered list of node IDs from start to end.
    """
    # Build adjacency list and in-degree count
    adj = {}
    in_degree = {}
    node_map = {}

    for node in nodes:
        nid = node["id"]
        adj[nid] = []
        in_degree[nid] = 0
        node_map[nid] = node

    for conn in connections:
        from_id = conn["from"]
        to_id = conn["to"]
        if from_id in adj:
            adj[from_id].append((to_id, conn.get("condition", "")))
        if to_id in in_degree:
            in_degree[to_id] += 1

    # Kahn's algorithm
    queue = [nid for nid, deg in in_degree.items() if deg == 0]
    ordered = []

    while queue:
        # Prefer start node first
        queue.sort(key=lambda x: (0 if node_map.get(x, {}).get("type") == "start" else 1, x))
        nid = queue.pop(0)
        ordered.append(nid)
        for neighbor, _cond in adj.get(nid, []):
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)

    return ordered, node_map, adj


# ── Node executors ──

def _describe_node(node):
    """Generate execution instruction for a node."""
    ntype = node.get("type", "")
    data = node.get("data", {})
    name = data.get("name", node.get("name", ""))

    if ntype == "start":
        return {"action": "start", "instruction": "Workflow started."}

    elif ntype == "end":
        return {"action": "end", "instruction": "Workflow complete."}

    elif ntype == "prompt":
        prompt_text = data.get("prompt", "")
        return {
            "action": "prompt",
            "instruction": f"Display to user:\n{prompt_text}",
        }

    elif ntype == "subAgent":
        desc = data.get("description", "")
        prompt = data.get("prompt", "")
        model = data.get("model", "sonnet")
        tools = data.get("tools", "")
        return {
            "action": "agent",
            "name": name,
            "description": desc,
            "model": model,
            "tools": tools,
            "instruction": (
                f"Dispatch sub-agent '{name}' ({desc}):\n"
                f"  Model: {model}\n"
                f"  Tools: {tools or 'default'}\n\n"
                f"Agent prompt:\n{prompt}"
            ),
        }

    elif ntype == "skill":
        skill_name = data.get("name", "")
        skill_path = data.get("skillPath", "")
        exec_mode = data.get("executionMode", "execute")
        exec_prompt = data.get("executionPrompt", "")
        return {
            "action": "skill",
            "name": skill_name,
            "instruction": (
                f"Invoke skill: /{skill_name}\n"
                + (f"Execution prompt: {exec_prompt}\n" if exec_prompt else "")
                + (f"Mode: {exec_mode}" if exec_mode != "execute" else "")
            ),
        }

    elif ntype == "mcp":
        server = data.get("serverId", "")
        tool = data.get("toolName", "")
        params = data.get("parameterValues", {})
        return {
            "action": "mcp",
            "server": server,
            "tool": tool,
            "parameters": params,
            "instruction": (
                f"Call MCP tool: {server}/{tool}\n"
                f"Parameters: {json.dumps(params, indent=2)}"
            ),
        }

    elif ntype == "askUserQuestion":
        question = data.get("questionText", "")
        options = data.get("options", [])
        opts_str = "\n".join(
            f"  {i+1}. {opt.get('label', '')} — {opt.get('description', '')}"
            for i, opt in enumerate(options)
        )
        return {
            "action": "ask",
            "question": question,
            "options": [opt.get("label", "") for opt in options],
            "instruction": f"Ask user:\n{question}\n\nOptions:\n{opts_str}",
        }

    elif ntype in ("ifElse", "switch"):
        target = data.get("evaluationTarget", "")
        branches = data.get("branches", [])
        branches_str = "\n".join(
            f"  - {b.get('label', '')}: {b.get('condition', '')}"
            for b in branches
        )
        return {
            "action": "branch",
            "target": target,
            "branches": [b.get("label", "") for b in branches],
            "instruction": f"Evaluate: {target}\n\nBranches:\n{branches_str}",
        }

    elif ntype == "subAgentFlow":
        flow_name = data.get("flowName", name)
        return {
            "action": "sub_workflow",
            "name": flow_name,
            "instruction": f"Execute sub-workflow: {flow_name}",
        }

    return {"action": "unknown", "type": ntype, "instruction": f"Unknown node type: {ntype}"}


# ── Chain → Workflow export ──

def _chain_to_workflow(chain_name, chain_data):
    """Convert a cc-code skill chain to cc-wf-studio workflow JSON."""
    skills = chain_data.get("skills", [])
    wf_id = f"workflow-{uuid.uuid4().hex[:12]}"

    nodes = []
    connections = []

    # Start node
    start_id = "start-node"
    nodes.append({
        "id": start_id,
        "type": "start",
        "name": "start-node",
        "position": {"x": 50, "y": 200},
        "data": {"label": "Start"},
    })

    # End node
    end_id = "end-node"
    end_x = 50 + (len(skills) + 1) * 250

    prev_id = start_id
    for i, step in enumerate(skills):
        skill_cmd = step["skill"].lstrip("/").strip()
        node_id = f"skill-{i}-{skill_cmd}"
        x = 50 + (i + 1) * 250
        y = 200

        nodes.append({
            "id": node_id,
            "type": "subAgent",
            "name": skill_cmd,
            "position": {"x": x, "y": y},
            "data": {
                "description": step.get("role", ""),
                "prompt": (
                    f"Activate the {skill_cmd} skill.\n"
                    f"Role: {step.get('role', '')}\n"
                    f"Required: {step.get('required', True)}"
                ),
                "model": "inherit",
                "outputPorts": 1,
                "name": skill_cmd,
            },
        })

        connections.append({
            "id": f"conn-{prev_id}-{node_id}",
            "from": prev_id,
            "to": node_id,
            "fromPort": "output",
            "toPort": "input",
        })
        prev_id = node_id

    # End node
    nodes.append({
        "id": end_id,
        "type": "end",
        "name": "end-node",
        "position": {"x": end_x, "y": 200},
        "data": {"label": "End"},
    })
    connections.append({
        "id": f"conn-{prev_id}-{end_id}",
        "from": prev_id,
        "to": end_id,
        "fromPort": "output",
        "toPort": "input",
    })

    return {
        "id": wf_id,
        "name": chain_name,
        "description": chain_data.get("description", ""),
        "version": "1.0.0",
        "schemaVersion": "1.1.0",
        "nodes": nodes,
        "connections": connections,
        "createdAt": now_iso(),
        "updatedAt": now_iso(),
    }


# ── CLI commands ──

def cmd_wf(args):
    """Sub-dispatch for wf subcommands."""
    wf_cmd = getattr(args, "wf_cmd", "")
    if wf_cmd == "run":
        cmd_wf_run(args)
    elif wf_cmd == "list":
        cmd_wf_list(args)
    elif wf_cmd == "export":
        cmd_wf_export(args)
    elif wf_cmd == "show":
        cmd_wf_show(args)
    else:
        error("Usage: cc-flow wf {run|list|export|show}")


def cmd_wf_run(args):
    """Execute a cc-wf-studio workflow JSON file."""
    path = getattr(args, "path", "")
    dry_run = getattr(args, "dry_run", False)

    workflow, filepath = _load_workflow(path)
    name = workflow.get("name", filepath.stem)
    desc = workflow.get("description", "")
    nodes = workflow.get("nodes", [])
    connections = workflow.get("connections", [])

    # Topological sort
    ordered_ids, node_map, adj = _topo_sort(nodes, connections)

    # Build execution plan
    steps = []
    for nid in ordered_ids:
        node = node_map.get(nid)
        if not node:
            continue
        step = _describe_node(node)
        step["node_id"] = nid
        step["node_type"] = node.get("type", "")
        steps.append(step)

    # Filter out start/end for instruction
    exec_steps = [s for s in steps if s["action"] not in ("start", "end")]

    # Build auto-execute instruction
    instruction_lines = [
        f"# AUTO-EXECUTE: {name} workflow",
        f"Description: {desc}",
        f"Source: {filepath}",
        "",
        "Execute these steps IN ORDER. Do NOT stop between steps.",
        "",
    ]

    for i, step in enumerate(exec_steps):
        instruction_lines.append(f"## Step {i+1}/{len(exec_steps)}: [{step['node_type']}] {step.get('name', '')}")
        instruction_lines.append(step["instruction"])
        instruction_lines.append("")

    instruction_lines.append("## Workflow Complete")
    instruction_lines.append(f"All {len(exec_steps)} steps executed.")

    result = {
        "success": True,
        "workflow": name,
        "description": desc,
        "source": str(filepath),
        "dry_run": dry_run,
        "total_nodes": len(nodes),
        "executable_steps": len(exec_steps),
        "steps": exec_steps,
        "instruction": "\n".join(instruction_lines),
    }

    print(json.dumps(result))


def cmd_wf_list(args):
    """List available workflow files."""
    workflows = []

    # Check .vscode/workflows/
    if WORKFLOWS_DIR.exists():
        for f in sorted(WORKFLOWS_DIR.glob("*.json")):
            data = safe_json_load(f, default=None)
            if data and "nodes" in data:
                workflows.append({
                    "name": data.get("name", f.stem),
                    "description": data.get("description", ""),
                    "nodes": len(data.get("nodes", [])),
                    "path": str(f),
                })

    print(json.dumps({"success": True, "workflows": workflows, "count": len(workflows)}))


def cmd_wf_show(args):
    """Show workflow details."""
    path = getattr(args, "path", "")
    workflow, filepath = _load_workflow(path)

    nodes = workflow.get("nodes", [])
    connections = workflow.get("connections", [])
    ordered_ids, node_map, adj = _topo_sort(nodes, connections)

    node_summary = []
    for nid in ordered_ids:
        node = node_map.get(nid, {})
        ntype = node.get("type", "?")
        data = node.get("data", {})
        name = data.get("name", node.get("name", ""))
        desc = data.get("description", data.get("prompt", ""))[:80]
        node_summary.append({
            "id": nid, "type": ntype, "name": name, "description": desc,
        })

    print(json.dumps({
        "success": True,
        "name": workflow.get("name", ""),
        "description": workflow.get("description", ""),
        "nodes": node_summary,
        "connections": len(connections),
        "path": str(filepath),
    }))


def cmd_wf_export(args):
    """Export a cc-code chain as cc-wf-studio workflow JSON."""
    chain_name = getattr(args, "name", "")
    if not chain_name:
        error("Specify chain: cc-flow wf export <chain-name>")

    try:
        from cc_flow.skill_chains import SKILL_CHAINS
    except ImportError:
        error("skill_chains module not available")

    if chain_name == "all":
        # Export all chains
        WORKFLOWS_DIR.mkdir(parents=True, exist_ok=True)
        exported = []
        for name, data in SKILL_CHAINS.items():
            wf = _chain_to_workflow(name, data)
            out_path = WORKFLOWS_DIR / f"{name}.json"
            atomic_write(out_path, json.dumps(wf, indent=2) + "\n")
            exported.append(name)
        print(json.dumps({
            "success": True,
            "exported": exported,
            "count": len(exported),
            "directory": str(WORKFLOWS_DIR),
        }))
        return

    if chain_name not in SKILL_CHAINS:
        error(f"Chain not found: {chain_name}. Use 'all' to export all chains.")

    wf = _chain_to_workflow(chain_name, SKILL_CHAINS[chain_name])
    WORKFLOWS_DIR.mkdir(parents=True, exist_ok=True)
    out_path = WORKFLOWS_DIR / f"{chain_name}.json"
    atomic_write(out_path, json.dumps(wf, indent=2) + "\n")

    print(json.dumps({
        "success": True,
        "chain": chain_name,
        "workflow": wf["name"],
        "nodes": len(wf["nodes"]),
        "path": str(out_path),
    }))
