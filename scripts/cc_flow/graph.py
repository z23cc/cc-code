"""Dependency graph rendering — Mermaid, ASCII, DOT formats."""

import json

from cc_flow.core import EPICS_DIR, all_tasks, error

STATUS_STYLE = {
    "todo": {"mermaid": ":::todo", "icon": "○"},
    "in_progress": {"mermaid": ":::inprog", "icon": "◐"},
    "done": {"mermaid": ":::done", "icon": "●"},
    "blocked": {"mermaid": ":::blocked", "icon": "✗"},
}


def cmd_graph(args):
    """Generate dependency graph in Mermaid, ASCII, or DOT format."""
    tasks = all_tasks()
    epic_filter = getattr(args, "epic", "") or ""
    fmt = getattr(args, "format", "mermaid") or "mermaid"

    filtered = {tid: t for tid, t in tasks.items() if not epic_filter or t.get("epic") == epic_filter}
    if not filtered:
        error("No tasks found")

    edges = [(dep, tid) for tid, t in filtered.items() for dep in t.get("depends_on", []) if dep in filtered]

    if fmt == "mermaid":
        _mermaid(filtered, edges, getattr(args, "json", False))
    elif fmt == "ascii":
        _ascii(filtered, edges)
    elif fmt == "dot":
        _dot(filtered, edges)
    else:
        error(f"Unknown format: {fmt}. Use: mermaid, ascii, dot")


def _mermaid(filtered, edges, as_json=False):
    lines = [
        "graph TD",
        "    classDef todo fill:#f9f9f9,stroke:#999,color:#333",
        "    classDef inprog fill:#fff3cd,stroke:#ffc107,color:#333",
        "    classDef done fill:#d4edda,stroke:#28a745,color:#333",
        "    classDef blocked fill:#f8d7da,stroke:#dc3545,color:#333",
    ]
    for tid, t in sorted(filtered.items()):
        label = t.get("title", tid)[:40]
        size = f" [{t.get('size', '')}]" if t.get("size") else ""
        style = STATUS_STYLE.get(t.get("status", "todo"), {}).get("mermaid", "")
        lines.append(f'    {tid.replace(".", "_")}["{tid}: {label}{size}"]{style}')
    for src, dst in edges:
        lines.append(f"    {src.replace('.', '_')} --> {dst.replace('.', '_')}")
    lines.append("\n    %% Legend: todo=gray, in_progress=yellow, done=green, blocked=red")
    text = "\n".join(lines)

    if as_json:
        print(json.dumps({"success": True, "format": "mermaid",
                          "nodes": len(filtered), "edges": len(edges), "mermaid": text}))
    else:
        print(f"```mermaid\n{text}\n```")


def _ascii(filtered, edges):
    has_incoming = {dst for _, dst in edges}
    roots = [tid for tid in filtered if tid not in has_incoming] or sorted(filtered.keys())[:1]
    children = {}
    for src, dst in edges:
        children.setdefault(src, []).append(dst)

    printed = set()

    def print_tree(tid, prefix="", is_last=True):
        icon = STATUS_STYLE.get(filtered[tid]["status"], {}).get("icon", "?")
        connector = "└── " if is_last else "├── "
        if tid in printed:
            print(f"{prefix}{connector}{icon} {tid} (↻ ref)")
            return
        printed.add(tid)
        t = filtered[tid]
        title = t.get("title", "")[:35]
        size = f" [{t.get('size', '')}]" if t.get("size") else ""
        print(f"{prefix}{connector}{icon} {tid}: {title}{size}")
        kids = children.get(tid, [])
        for i, kid in enumerate(kids):
            print_tree(kid, prefix + ("    " if is_last else "│   "), i == len(kids) - 1)

    for i, root in enumerate(sorted(roots)):
        if i > 0:
            print()
        epic_id = filtered[root].get("epic", "")
        if i == 0 and epic_id:
            epic_spec = EPICS_DIR / f"{epic_id}.md"
            if epic_spec.exists():
                title = epic_spec.read_text().split("\n", 1)[0].lstrip("# ").replace("Epic:", "").strip()
                print(f"📋 {title}" if title else f"📋 {epic_id}")
        print_tree(root, "", i == len(roots) - 1)

    done = sum(1 for t in filtered.values() if t["status"] == "done")
    print(f"\n── {done}/{len(filtered)} done, {len(edges)} dependencies ──")


def _dot(filtered, edges):
    fill = {"todo": "#f9f9f9", "in_progress": "#fff3cd", "done": "#d4edda", "blocked": "#f8d7da"}
    lines = ["digraph tasks {", "    rankdir=LR;", '    node [shape=box, style=filled];']
    for tid, t in sorted(filtered.items()):
        label = f"{tid}\\n{t.get('title', '')[:30]}"
        color = fill.get(t.get("status", "todo"), "#f9f9f9")
        lines.append(f'    "{tid}" [label="{label}", fillcolor="{color}"];')
    for src, dst in edges:
        lines.append(f'    "{src}" -> "{dst}";')
    lines.append("}")
    print("\n".join(lines))


def cmd_critical_path(args):
    """Find the longest dependency chain (critical path) in an epic."""
    tasks = all_tasks()
    epic_filter = getattr(args, "epic", "") or ""

    filtered = {tid: t for tid, t in tasks.items() if not epic_filter or t.get("epic") == epic_filter}
    if not filtered:
        error("No tasks found")

    # Build adjacency: task → deps
    def _longest_path(tid, memo=None):
        if memo is None:
            memo = {}
        if tid in memo:
            return memo[tid]
        deps = filtered.get(tid, {}).get("depends_on", [])
        valid_deps = [d for d in deps if d in filtered]
        if not valid_deps:
            memo[tid] = [tid]
            return [tid]
        best = max((_longest_path(d, memo) for d in valid_deps), key=len)
        memo[tid] = [*best, tid]
        return memo[tid]

    # Find the longest path across all tasks
    all_paths = [_longest_path(tid) for tid in filtered]
    critical = max(all_paths, key=len)

    path_details = [
        {"id": tid, "title": filtered[tid].get("title", ""), "status": filtered[tid]["status"]}
        for tid in critical
    ]
    remaining = sum(1 for p in path_details if p["status"] != "done")

    print(json.dumps({
        "success": True,
        "critical_path": path_details,
        "length": len(critical),
        "remaining": remaining,
        "total_tasks": len(filtered),
    }))
