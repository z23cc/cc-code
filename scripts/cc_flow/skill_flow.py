"""cc-flow skill flow — graph extraction, context protocol, and CLI commands.

Parses FLOWS INTO / DEPENDS ON from skills/*/SKILL.md into a queryable
graph. Provides a context protocol for passing data between skills.

Used by: skill_chains (context-aware execution), post-task-hint (next suggestions).
"""

import json
import os
import re
from pathlib import Path

from cc_flow.core import TASKS_DIR, atomic_write, error, now_iso, safe_json_load

SKILL_CTX_DIR = TASKS_DIR / "skill_ctx"
SKILL_GRAPH_CACHE = TASKS_DIR / "skill_graph.json"
CURRENT_FILE = SKILL_CTX_DIR / "_current.json"
CHAIN_STATE_FILE = SKILL_CTX_DIR / "_chain_state.json"


# ── Skill directory discovery ──

def _skills_dir():
    """Find the skills/ directory relative to plugin root or cwd."""
    # Check CLAUDE_PLUGIN_ROOT first (set when running as plugin)
    root = os.environ.get("CLAUDE_PLUGIN_ROOT", "")
    if root:
        p = Path(root) / "skills"
        if p.is_dir():
            return p
    # Fallback: walk up from cwd
    cwd = Path.cwd()
    for parent in [cwd, *cwd.parents]:
        p = parent / "skills"
        if p.is_dir():
            return p
    return None


# ── Name normalization ──

# Common aliases: directory name → shorter command form
_KNOWN_ALIASES = {
    "cc-brainstorming": ["cc-brainstorm"],
    "cc-debugging": ["cc-debug"],
    "cc-refinement": ["cc-refine"],
    "cc-readiness-audit": ["cc-audit"],
    "cc-task-tracking": ["cc-tasks"],
    "cc-python-testing": ["cc-test"],
}


def _build_alias_map(skills_dir):
    """Build bidirectional alias map from skill directory names."""
    alias_to_canonical = {}
    if not skills_dir:
        return alias_to_canonical
    for d in skills_dir.iterdir():
        if d.is_dir() and d.name.startswith("cc-"):
            canonical = d.name
            alias_to_canonical[canonical] = canonical
            # Strip /cc- prefix if present in references
            alias_to_canonical[f"/{canonical}"] = canonical
            # Add known aliases
            for alias in _KNOWN_ALIASES.get(canonical, []):
                alias_to_canonical[alias] = canonical
                alias_to_canonical[f"/{alias}"] = canonical
    return alias_to_canonical


def _normalize(name, alias_map):
    """Normalize a skill name to its canonical form."""
    name = name.strip().strip("'\"")
    # Remove leading slash
    bare = name.lstrip("/")
    # Try direct lookup
    if bare in alias_map:
        return alias_map[bare]
    if name in alias_map:
        return alias_map[name]
    # Try with cc- prefix
    if not bare.startswith("cc-"):
        prefixed = f"cc-{bare}"
        if prefixed in alias_map:
            return alias_map[prefixed]
    return bare


# ── Graph extraction ──

_FLOWS_RE = re.compile(r"FLOWS\s+INTO:\s*(.+?)(?:\.\s*(?:TRIGGER|NOT|DEPENDS|USED|$)|\.\s*$|TRIGGER|NOT\s+FOR|DEPENDS|USED|$)", re.IGNORECASE)
_DEPENDS_RE = re.compile(r"DEPENDS\s+ON:\s*(.+?)(?:\.\s*(?:TRIGGER|NOT|DEPENDS|FLOWS|USED|$)|\.\s*$|TRIGGER|NOT\s+FOR|FLOWS|USED|$)", re.IGNORECASE)
_USED_BY_RE = re.compile(r"USED\s+BY:\s*(.+?)(?:\.\s*(?:TRIGGER|NOT|DEPENDS|FLOWS|USED|$)|\.\s*$|TRIGGER|NOT\s+FOR|FLOWS|DEPENDS|$)", re.IGNORECASE)


def _parse_refs(text):
    """Parse comma-separated skill references, stripping parenthetical notes."""
    refs = []
    for part in re.split(r"[,;]", text):
        # Remove parenthetical notes like "(all tasks done before epic review)"
        clean = re.sub(r"\([^)]*\)", "", part).strip()
        # Strip trailing dots/whitespace
        clean = clean.rstrip(". ")
        # Skip empty, non-skill references
        if not clean or not clean.startswith("cc-"):
            continue
        refs.append(clean)
    return refs


def _read_skill_description(skill_md_path):
    """Read the description field from a SKILL.md frontmatter."""
    try:
        content = skill_md_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return ""

    # Extract YAML frontmatter between --- markers
    if not content.startswith("---"):
        return ""
    end = content.find("---", 3)
    if end < 0:
        return ""
    frontmatter = content[3:end]

    # Extract description field (handles both inline and multi-line >)
    lines = frontmatter.split("\n")
    desc_lines = []
    in_desc = False
    for line in lines:
        if line.startswith("description:"):
            rest = line[len("description:"):].strip()
            if rest.startswith('"'):
                # Inline quoted description
                desc_lines.append(rest.strip('"'))
                break
            elif rest == ">":
                in_desc = True
                continue
            else:
                desc_lines.append(rest)
                break
        elif in_desc:
            if line and line[0] in (" ", "\t"):
                desc_lines.append(line.strip())
            else:
                break

    return " ".join(desc_lines)


def build_graph(skills_dir=None):
    """Parse all SKILL.md files and build a flow graph."""
    if skills_dir is None:
        skills_dir = _skills_dir()
    if not skills_dir or not skills_dir.is_dir():
        return {"nodes": {}, "built": now_iso(), "version": 1}

    alias_map = _build_alias_map(skills_dir)
    nodes = {}

    for skill_dir in sorted(skills_dir.iterdir()):
        if not skill_dir.is_dir() or not skill_dir.name.startswith("cc-"):
            continue

        skill_md = skill_dir / "SKILL.md"
        if not skill_md.exists():
            continue

        canonical = skill_dir.name
        desc = _read_skill_description(skill_md)

        flows_into = []
        depends_on = []
        used_by = []

        m = _FLOWS_RE.search(desc)
        if m:
            flows_into = [_normalize(r, alias_map) for r in _parse_refs(m.group(1))]

        m = _DEPENDS_RE.search(desc)
        if m:
            depends_on = [_normalize(r, alias_map) for r in _parse_refs(m.group(1))]

        m = _USED_BY_RE.search(desc)
        if m:
            used_by = [_normalize(r, alias_map) for r in _parse_refs(m.group(1))]

        # Build aliases list for this skill
        aliases = _KNOWN_ALIASES.get(canonical, [])

        nodes[canonical] = {
            "flows_into": flows_into,
            "depends_on": depends_on,
            "used_by": used_by,
            "aliases": aliases,
        }

    return {"nodes": nodes, "built": now_iso(), "version": 1}


def _max_skill_mtime(skills_dir):
    """Get the newest mtime of any SKILL.md file."""
    max_t = 0
    if not skills_dir or not skills_dir.is_dir():
        return max_t
    for skill_dir in skills_dir.iterdir():
        if skill_dir.is_dir():
            skill_md = skill_dir / "SKILL.md"
            if skill_md.exists():
                t = skill_md.stat().st_mtime
                if t > max_t:
                    max_t = t
    return max_t


def load_graph():
    """Load the graph from cache, rebuilding if stale."""
    skills_dir = _skills_dir()

    if SKILL_GRAPH_CACHE.exists():
        cache_mtime = SKILL_GRAPH_CACHE.stat().st_mtime
        newest = _max_skill_mtime(skills_dir)
        if cache_mtime >= newest:
            return safe_json_load(SKILL_GRAPH_CACHE, default=None) or build_graph(skills_dir)

    # Build and cache
    graph = build_graph(skills_dir)
    SKILL_GRAPH_CACHE.parent.mkdir(parents=True, exist_ok=True)
    atomic_write(SKILL_GRAPH_CACHE, json.dumps(graph, indent=2) + "\n")
    return graph


# ── Graph queries ──

def next_skills(name):
    """Return the list of skills that follow the given skill."""
    graph = load_graph()
    alias_map = _build_alias_map(_skills_dir())
    canonical = _normalize(name, alias_map)
    node = graph.get("nodes", {}).get(canonical)
    if node:
        return node.get("flows_into", [])
    return []


def prev_skills(name):
    """Return the list of skills that must precede the given skill."""
    graph = load_graph()
    alias_map = _build_alias_map(_skills_dir())
    canonical = _normalize(name, alias_map)
    node = graph.get("nodes", {}).get(canonical)
    if node:
        return node.get("depends_on", [])
    return []


# ── Skill context protocol ──

def save_skill_ctx(name, data):
    """Save context data for a skill."""
    alias_map = _build_alias_map(_skills_dir())
    canonical = _normalize(name, alias_map)
    SKILL_CTX_DIR.mkdir(parents=True, exist_ok=True)
    ctx = {"skill": canonical, "timestamp": now_iso(), **data}
    atomic_write(SKILL_CTX_DIR / f"{canonical}.json", json.dumps(ctx, indent=2) + "\n")
    return ctx


def load_skill_ctx(name):
    """Load context data for a skill. Returns None if not found."""
    alias_map = _build_alias_map(_skills_dir())
    canonical = _normalize(name, alias_map)
    path = SKILL_CTX_DIR / f"{canonical}.json"
    if not path.exists():
        return None
    return safe_json_load(path, default=None)


def set_current(name, chain_name=None):
    """Set the currently active skill."""
    alias_map = _build_alias_map(_skills_dir())
    canonical = _normalize(name, alias_map)
    SKILL_CTX_DIR.mkdir(parents=True, exist_ok=True)
    data = {"skill": canonical, "started": now_iso()}
    if chain_name:
        data["chain"] = chain_name
    atomic_write(CURRENT_FILE, json.dumps(data, indent=2) + "\n")
    return data


def get_current():
    """Get the currently active skill. Returns None if not set."""
    if not CURRENT_FILE.exists():
        return None
    return safe_json_load(CURRENT_FILE, default=None)


def clear_current():
    """Clear the currently active skill."""
    if CURRENT_FILE.exists():
        CURRENT_FILE.unlink()


# ── Chain state ──

def save_chain_state(chain_name, steps, current_step=0):
    """Save chain execution state for resume."""
    SKILL_CTX_DIR.mkdir(parents=True, exist_ok=True)
    state = {
        "chain": chain_name,
        "current_step": current_step,
        "total_steps": len(steps),
        "steps": [s.get("skill", "") for s in steps],
        "started": now_iso(),
    }
    atomic_write(CHAIN_STATE_FILE, json.dumps(state, indent=2) + "\n")
    return state


def load_chain_state():
    """Load chain execution state. Returns None if not found."""
    if not CHAIN_STATE_FILE.exists():
        return None
    return safe_json_load(CHAIN_STATE_FILE, default=None)


def advance_chain_state():
    """Advance chain state to the next step. Returns updated state or None if complete."""
    state = load_chain_state()
    if not state:
        return None
    state["current_step"] += 1
    if state["current_step"] >= state["total_steps"]:
        # Chain complete — clean up
        CHAIN_STATE_FILE.unlink(missing_ok=True)
        return {"complete": True, "chain": state["chain"]}
    atomic_write(CHAIN_STATE_FILE, json.dumps(state, indent=2) + "\n")
    return state


# ── Dependency check ──

def check_deps(name):
    """Check if a skill's dependencies have context available.

    Returns {"ready": bool, "missing": [...], "available": [...]}.
    """
    deps = prev_skills(name)
    if not deps:
        return {"ready": True, "missing": [], "available": []}

    missing = []
    available = []
    for dep in deps:
        ctx = load_skill_ctx(dep)
        if ctx:
            available.append(dep)
        else:
            missing.append(dep)

    return {"ready": len(missing) == 0, "missing": missing, "available": available}


def cmd_check_deps(args):
    """CLI: check if a skill's dependencies are satisfied."""
    name = getattr(args, "skill", "") or getattr(args, "name", "")
    if not name:
        current = get_current()
        if current:
            name = current.get("skill", "")
    if not name:
        error("Specify skill: cc-flow skill check-deps --skill <name>")

    alias_map = _build_alias_map(_skills_dir())
    canonical = _normalize(name, alias_map)
    result = check_deps(canonical)
    result["skill"] = canonical
    result["success"] = True

    if result["missing"]:
        result["message"] = (
            f"Missing context from: {', '.join(result['missing'])}. "
            f"Run these skills first, or use: cc-flow skill ctx save <name> --data '{{}}'"
        )
    else:
        result["message"] = "All dependencies satisfied."

    print(json.dumps(result))


# ── Chain metrics ──

CHAIN_METRICS_FILE = TASKS_DIR / "chain_metrics.json"


def _load_metrics():
    """Load chain metrics."""
    return safe_json_load(CHAIN_METRICS_FILE, default={"chains": {}, "total_runs": 0})


def record_chain_start(chain_name):
    """Record chain execution start."""
    metrics = _load_metrics()
    if chain_name not in metrics["chains"]:
        metrics["chains"][chain_name] = {
            "runs": 0, "completions": 0, "failures": 0,
            "total_steps_completed": 0, "avg_steps": 0,
        }
    metrics["chains"][chain_name]["runs"] += 1
    metrics["chains"][chain_name]["last_started"] = now_iso()
    metrics["total_runs"] += 1
    CHAIN_METRICS_FILE.parent.mkdir(parents=True, exist_ok=True)
    atomic_write(CHAIN_METRICS_FILE, json.dumps(metrics, indent=2) + "\n")


def record_chain_complete(chain_name, steps_completed, total_steps):
    """Record chain completion."""
    metrics = _load_metrics()
    if chain_name not in metrics["chains"]:
        metrics["chains"][chain_name] = {
            "runs": 1, "completions": 0, "failures": 0,
            "total_steps_completed": 0, "avg_steps": 0,
        }
    m = metrics["chains"][chain_name]
    m["completions"] += 1
    m["total_steps_completed"] += steps_completed
    m["last_completed"] = now_iso()
    total_runs = m["completions"] + m["failures"]
    if total_runs > 0:
        m["avg_steps"] = round(m["total_steps_completed"] / total_runs, 1)
    m["success_rate"] = round(m["completions"] / max(m["runs"], 1) * 100)
    CHAIN_METRICS_FILE.parent.mkdir(parents=True, exist_ok=True)
    atomic_write(CHAIN_METRICS_FILE, json.dumps(metrics, indent=2) + "\n")



def cmd_chain_stats(args):
    """Show chain execution metrics."""
    metrics = _load_metrics()
    if not metrics["chains"]:
        print(json.dumps({"success": True, "total_runs": 0, "message": "No chain metrics yet."}))
        return

    print(json.dumps({
        "success": True,
        "total_runs": metrics["total_runs"],
        "chains": metrics["chains"],
    }))


# ── CLI commands ──

def cmd_next(args):
    """Suggest next skill(s) based on flow graph and current state."""
    skill_name = getattr(args, "skill", "") or ""

    # If no skill specified, check _current.json
    if not skill_name:
        current = get_current()
        if current:
            skill_name = current.get("skill", "")

    if not skill_name:
        print(json.dumps({"success": False, "error": "No active skill. Use --skill <name> or run a skill first."}))
        return

    nxt = next_skills(skill_name)
    chain_state = load_chain_state()

    result = {
        "success": True,
        "current_skill": skill_name,
        "next_skills": nxt,
    }

    if chain_state:
        result["chain"] = chain_state.get("chain")
        step_idx = chain_state.get("current_step", 0)
        steps = chain_state.get("steps", [])
        if step_idx + 1 < len(steps):
            result["chain_next"] = steps[step_idx + 1]

    # Build human-friendly message
    if nxt:
        skills_str = ", ".join(f"/{s}" for s in nxt)
        result["message"] = f"NEXT -> {skills_str}"
    else:
        result["message"] = "No declared next skill. This may be a terminal step."

    print(json.dumps(result))


def cmd_graph_show(args):
    """Show the skill flow graph."""
    graph = load_graph()
    skill_name = getattr(args, "for_skill", "") or ""

    if skill_name:
        alias_map = _build_alias_map(_skills_dir())
        canonical = _normalize(skill_name, alias_map)
        node = graph.get("nodes", {}).get(canonical)
        if not node:
            error(f"Skill not found in graph: {skill_name}")
        print(json.dumps({
            "success": True,
            "skill": canonical,
            **node,
            "predecessors_ctx": {
                dep: bool(load_skill_ctx(dep)) for dep in node.get("depends_on", [])
            },
        }))
    else:
        # Summary: only skills with edges
        connected = {
            name: node for name, node in graph.get("nodes", {}).items()
            if node.get("flows_into") or node.get("depends_on") or node.get("used_by")
        }
        total = len(graph.get("nodes", {}))
        print(json.dumps({
            "success": True,
            "total_skills": total,
            "connected_skills": len(connected),
            "orphan_skills": total - len(connected),
            "graph": connected,
            "built": graph.get("built"),
        }))


def cmd_graph_build(args):
    """Force rebuild the skill flow graph."""
    graph = build_graph()
    SKILL_GRAPH_CACHE.parent.mkdir(parents=True, exist_ok=True)
    atomic_write(SKILL_GRAPH_CACHE, json.dumps(graph, indent=2) + "\n")
    total = len(graph.get("nodes", {}))
    connected = sum(
        1 for n in graph.get("nodes", {}).values()
        if n.get("flows_into") or n.get("depends_on") or n.get("used_by")
    )
    print(json.dumps({
        "success": True,
        "total_skills": total,
        "connected_skills": connected,
        "cache": str(SKILL_GRAPH_CACHE),
    }))


def cmd_ctx(args):
    """Sub-dispatch for skill ctx save/load/current/clear."""
    ctx_cmd = getattr(args, "ctx_cmd", "")
    if ctx_cmd == "save":
        cmd_ctx_save(args)
    elif ctx_cmd == "load":
        cmd_ctx_load(args)
    elif ctx_cmd == "current":
        cmd_ctx_current(args)
    elif ctx_cmd == "clear":
        cmd_ctx_clear(args)
    else:
        error("Usage: cc-flow skill ctx {save|load|current|clear}")


def cmd_ctx_save(args):
    """Save context for a skill."""
    name = args.name
    data_str = getattr(args, "data", "{}")
    try:
        data = json.loads(data_str)
    except json.JSONDecodeError:
        error(f"Invalid JSON: {data_str}")
    ctx = save_skill_ctx(name, data)
    print(json.dumps({"success": True, "skill": ctx["skill"], "keys": list(data.keys())}))


def cmd_ctx_load(args):
    """Load context for a skill."""
    name = args.name
    ctx = load_skill_ctx(name)
    if ctx:
        print(json.dumps({"success": True, **ctx}))
    else:
        print(json.dumps({"success": False, "error": f"No context found for {name}"}))


def cmd_ctx_current(args):
    """Show the currently active skill."""
    current = get_current()
    if current:
        nxt = next_skills(current.get("skill", ""))
        print(json.dumps({"success": True, **current, "next_skills": nxt}))
    else:
        print(json.dumps({"success": False, "error": "No active skill"}))


def cmd_ctx_clear(args):
    """Clear current skill and optionally all skill context."""
    clear_all = getattr(args, "all", False)
    clear_current()
    cleared = ["_current.json"]
    if clear_all and SKILL_CTX_DIR.exists():
        for f in SKILL_CTX_DIR.glob("*.json"):
            if f.name != "_chain_state.json":
                f.unlink()
                cleared.append(f.name)
    print(json.dumps({"success": True, "cleared": cleared}))
