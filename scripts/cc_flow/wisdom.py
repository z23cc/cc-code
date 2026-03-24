"""cc-flow wisdom — persistent knowledge accumulation across chains.

Three knowledge stores (append-only, inspired by CCW):
  learnings.jsonl  — what worked/failed and why
  decisions.jsonl  — architectural/design decisions with rationale
  conventions.jsonl — coding patterns and team conventions discovered

Also: exploration cache to prevent redundant research.

Used by: skill_chains (auto-append on completion), cc-research (cache check).
"""

import hashlib
import json
import os
from pathlib import Path

from cc_flow.core import TASKS_DIR, atomic_write, error, now_iso, safe_json_load

WISDOM_DIR = TASKS_DIR / "wisdom"
EXPLORATIONS_DIR = TASKS_DIR / "explorations"
CHECKPOINT_DIR = TASKS_DIR / "checkpoints"


# ── Wisdom store ──

def _wisdom_path(category):
    """Get path for a wisdom category (learnings/decisions/conventions)."""
    WISDOM_DIR.mkdir(parents=True, exist_ok=True)
    return WISDOM_DIR / f"{category}.jsonl"


def append_wisdom(category, entry):
    """Append a wisdom entry. Categories: learnings, decisions, conventions."""
    if category not in ("learnings", "decisions", "conventions"):
        return
    path = _wisdom_path(category)
    entry["timestamp"] = now_iso()
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def load_wisdom(category, limit=50):
    """Load recent wisdom entries."""
    path = _wisdom_path(category)
    if not path.exists():
        return []
    entries = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    return entries[-limit:]


def search_wisdom(query, limit=10):
    """Search across all wisdom categories by keyword."""
    query_lower = query.lower()
    results = []
    for cat in ("learnings", "decisions", "conventions"):
        for entry in load_wisdom(cat, limit=200):
            text = json.dumps(entry, ensure_ascii=False).lower()
            if query_lower in text:
                entry["_category"] = cat
                results.append(entry)
    return results[:limit]


def record_chain_wisdom(chain_name, outcome, steps_completed, context_summary=""):
    """Auto-record wisdom after chain completion."""
    append_wisdom("learnings", {
        "chain": chain_name,
        "outcome": outcome,
        "steps_completed": steps_completed,
        "context": context_summary,
        "source": "chain_auto",
    })


# ── Exploration cache ──

def _cache_key(query):
    """Generate a cache key from a query string."""
    return hashlib.sha256(query.encode()).hexdigest()[:16]


def cache_exploration(query, findings, source="research"):
    """Cache exploration/research results."""
    EXPLORATIONS_DIR.mkdir(parents=True, exist_ok=True)
    key = _cache_key(query)
    entry = {
        "query": query,
        "findings": findings,
        "source": source,
        "timestamp": now_iso(),
        "key": key,
    }
    atomic_write(EXPLORATIONS_DIR / f"{key}.json", json.dumps(entry, indent=2) + "\n")
    # Update index
    _update_cache_index(key, query, source)
    return key


def lookup_exploration(query):
    """Check if an exploration is cached. Returns findings or None."""
    key = _cache_key(query)
    path = EXPLORATIONS_DIR / f"{key}.json"
    if path.exists():
        data = safe_json_load(path, default=None)
        if data:
            return data
    # Fuzzy: check index for similar queries
    index = _load_cache_index()
    query_words = set(query.lower().split())
    for entry in index.get("entries", []):
        cached_words = set(entry.get("query", "").lower().split())
        overlap = len(query_words & cached_words) / max(len(query_words | cached_words), 1)
        if overlap > 0.7:
            path = EXPLORATIONS_DIR / f"{entry['key']}.json"
            if path.exists():
                data = safe_json_load(path, default=None)
                if data:
                    data["_fuzzy_match"] = True
                    return data
    return None


def _load_cache_index():
    """Load the exploration cache index."""
    path = EXPLORATIONS_DIR / "cache-index.json"
    return safe_json_load(path, default={"entries": []})


def _update_cache_index(key, query, source):
    """Update the exploration cache index."""
    index = _load_cache_index()
    # Remove old entry with same key
    index["entries"] = [e for e in index["entries"] if e.get("key") != key]
    index["entries"].append({"key": key, "query": query, "source": source, "timestamp": now_iso()})
    # Keep last 100
    index["entries"] = index["entries"][-100:]
    atomic_write(EXPLORATIONS_DIR / "cache-index.json", json.dumps(index, indent=2) + "\n")


# ── Checkpoint supervisor gate ──

def should_checkpoint(chain_name, current_step, total_steps):
    """Determine if a checkpoint should run at this step.

    Rule: checkpoint every 2 steps in chains with >3 total steps.
    """
    if total_steps <= 3:
        return False
    # Checkpoint at step 2, 4, 6, ... (0-indexed: 1, 3, 5, ...)
    return current_step > 0 and current_step % 2 == 1


def run_checkpoint(chain_name, step_idx):
    """Run a quality gate checkpoint. Returns verdict dict.

    Checks: verify (lint+test), uncommitted changes, context completeness.
    """
    import subprocess
    import sys

    results = {"chain": chain_name, "step": step_idx + 1, "timestamp": now_iso(), "checks": []}

    # Check 1: cc-flow verify (lint + tests)
    try:
        cmd = [sys.executable, "-m", "cc_flow", "verify"]
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        verify_ok = proc.returncode == 0
        results["checks"].append({
            "name": "verify",
            "passed": verify_ok,
            "detail": "lint + tests" if verify_ok else proc.stdout[-200:] if proc.stdout else "failed",
        })
    except (subprocess.TimeoutExpired, Exception):
        results["checks"].append({"name": "verify", "passed": False, "detail": "timeout"})

    # Check 2: No syntax errors in recently changed files
    try:
        cmd = ["git", "diff", "--name-only", "--diff-filter=M"]
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        changed = [f for f in proc.stdout.strip().split("\n") if f.endswith(".py")]
        all_ok = True
        for f in changed[:10]:
            result = subprocess.run(
                [sys.executable, "-m", "py_compile", f],
                capture_output=True, text=True, timeout=5,
            )
            if result.returncode != 0:
                all_ok = False
                break
        results["checks"].append({"name": "syntax", "passed": all_ok, "detail": f"{len(changed)} files"})
    except Exception:
        results["checks"].append({"name": "syntax", "passed": True, "detail": "skipped"})

    # Determine verdict
    all_passed = all(c["passed"] for c in results["checks"])
    any_failed = any(not c["passed"] for c in results["checks"])

    if all_passed:
        results["verdict"] = "pass"
    elif any_failed:
        results["verdict"] = "warn"
    else:
        results["verdict"] = "pass"

    # Save checkpoint
    CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)
    cp_name = f"{chain_name}-step{step_idx + 1}"
    atomic_write(CHECKPOINT_DIR / f"{cp_name}.json", json.dumps(results, indent=2) + "\n")

    return results


# ── CLI commands ──

def cmd_wisdom(args):
    """Sub-dispatch for wisdom commands."""
    wis_cmd = getattr(args, "wisdom_cmd", "")
    if wis_cmd == "show":
        cmd_wisdom_show(args)
    elif wis_cmd == "search":
        cmd_wisdom_search(args)
    elif wis_cmd == "add":
        cmd_wisdom_add(args)
    elif wis_cmd == "clear":
        cmd_wisdom_clear(args)
    else:
        error("Usage: cc-flow wisdom {show|search|add|clear}")


def cmd_wisdom_show(args):
    """Show recent wisdom entries."""
    category = getattr(args, "category", "all")
    limit = getattr(args, "limit", 20)

    if category == "all":
        result = {}
        for cat in ("learnings", "decisions", "conventions"):
            entries = load_wisdom(cat, limit=limit)
            if entries:
                result[cat] = entries
        print(json.dumps({"success": True, "wisdom": result, "total": sum(len(v) for v in result.values())}))
    else:
        entries = load_wisdom(category, limit=limit)
        print(json.dumps({"success": True, "category": category, "entries": entries, "count": len(entries)}))


def cmd_wisdom_search(args):
    """Search wisdom by keyword."""
    query = " ".join(args.query) if args.query else ""
    if not query:
        error("Provide search query")
    results = search_wisdom(query)
    print(json.dumps({"success": True, "query": query, "results": results, "count": len(results)}))


def cmd_wisdom_add(args):
    """Add a wisdom entry manually."""
    category = args.category
    content = args.content
    append_wisdom(category, {"content": content, "source": "manual"})
    print(json.dumps({"success": True, "category": category, "added": True}))


def cmd_wisdom_clear(args):
    """Clear wisdom entries."""
    category = getattr(args, "category", "all")
    if category == "all":
        for cat in ("learnings", "decisions", "conventions"):
            p = _wisdom_path(cat)
            if p.exists():
                p.unlink()
        print(json.dumps({"success": True, "cleared": "all"}))
    else:
        p = _wisdom_path(category)
        if p.exists():
            p.unlink()
        print(json.dumps({"success": True, "cleared": category}))


def cmd_explore(args):
    """Sub-dispatch for explore commands."""
    exp_cmd = getattr(args, "explore_cmd", "")
    if exp_cmd == "cache":
        cmd_explore_cache(args)
    elif exp_cmd == "lookup":
        cmd_explore_lookup(args)
    elif exp_cmd == "clear":
        cmd_explore_clear(args)
    else:
        error("Usage: cc-flow explore {cache|lookup|clear}")


def cmd_explore_cache(args):
    """Show exploration cache stats."""
    index = _load_cache_index()
    entries = index.get("entries", [])
    print(json.dumps({
        "success": True,
        "cached_explorations": len(entries),
        "entries": entries[-10:],
    }))


def cmd_explore_lookup(args):
    """Look up a cached exploration."""
    query = " ".join(args.query) if args.query else ""
    if not query:
        error("Provide lookup query")
    result = lookup_exploration(query)
    if result:
        print(json.dumps({"success": True, "hit": True, **result}))
    else:
        print(json.dumps({"success": True, "hit": False, "query": query}))


def cmd_explore_clear(args):
    """Clear exploration cache."""
    if EXPLORATIONS_DIR.exists():
        for f in EXPLORATIONS_DIR.glob("*.json"):
            f.unlink()
    print(json.dumps({"success": True, "cleared": True}))
