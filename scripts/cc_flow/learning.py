"""cc-flow learning — record, search, consolidate learnings.

Split from route_learn.py for better modularity.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

from cc_flow.core import (
    LEARNINGS_DIR,
    ROUTE_STATS_FILE,
    TASKS_DIR,
    get_morph_client,
    now_iso,
    safe_json_load,
)


def _load_route_stats():
    """Load route stats from disk."""
    return safe_json_load(ROUTE_STATS_FILE, default={"commands": {}})


def _save_route_stats(stats):
    """Save route stats to disk."""
    stats["updated"] = now_iso()
    ROUTE_STATS_FILE.write_text(json.dumps(stats, indent=2) + "\n")


def cmd_learn(args):
    """Record a learning from the current session for future routing."""
    LEARNINGS_DIR.mkdir(parents=True, exist_ok=True)

    learning = {
        "timestamp": now_iso(),
        "task": args.task,
        "outcome": args.outcome,
        "approach": args.approach,
        "lesson": args.lesson,
        "score": args.score,
    }
    if getattr(args, "used_command", None):
        learning["command"] = args.used_command

    fname = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S-%f") + ".json"
    path = LEARNINGS_DIR / fname
    path.write_text(json.dumps(learning, indent=2) + "\n")

    if learning.get("command"):
        stats = _load_route_stats()
        cmd = learning["command"]
        if cmd not in stats["commands"]:
            stats["commands"][cmd] = {"success": 0, "failure": 0}
        if args.outcome == "success":
            stats["commands"][cmd]["success"] += 1
        elif args.outcome == "failed":
            stats["commands"][cmd]["failure"] += 1
        else:
            stats["commands"][cmd]["success"] += 0.5
        _save_route_stats(stats)

    if learning.get("command"):
        try:
            from cc_flow.qrouter import q_update
            q_update(args.task, learning["command"], args.outcome)
        except ImportError:
            pass

    print(json.dumps({"success": True, "saved": str(path)}))


def cmd_learnings(args):
    """List or search past learnings."""
    if not LEARNINGS_DIR.exists():
        print(json.dumps({"success": True, "learnings": [], "count": 0}))
        return

    learnings = []
    for f in sorted(LEARNINGS_DIR.glob("*.json")):
        d = safe_json_load(f, default=None)
        if d:
            learnings.append(d)

    if args.search:
        query = args.search.lower()
        learnings = [entry for entry in learnings if
                     query in entry.get("task", "").lower() or
                     query in entry.get("lesson", "").lower() or
                     query in entry.get("approach", "").lower()]

    n = args.last or 10
    print(json.dumps({"success": True, "learnings": learnings[-n:], "count": len(learnings)}))


# ── Search helpers ──

def _make_result(learning, confidence, alternatives, engine):
    """Build a standardized search result dict from a learning entry."""
    return {
        "task": learning.get("task"),
        "approach": learning.get("approach"),
        "lesson": learning.get("lesson"),
        "score": learning.get("score"),
        "confidence": confidence,
        "alternatives": alternatives,
        "engine": engine,
    }


def _try_morph_rerank(query, learnings):
    """Try semantic reranking via Morph."""
    morph_client = get_morph_client()
    if not morph_client or len(learnings) < 2:
        return None
    try:
        documents = [
            f"{d.get('task', '')} | {d.get('lesson', '')} | {d.get('approach', '')}"
            for d in learnings
        ]
        ranked = morph_client.rerank(query, documents, top_n=3)
        if ranked and ranked[0].get("relevance_score", 0) > 0.1:
            best = learnings[ranked[0]["index"]]
            confidence = min(int(ranked[0]["relevance_score"] * 100), 99)
            return _make_result(best, confidence, len(ranked) - 1, "morph-rerank")
    except (RuntimeError, TimeoutError, OSError, json.JSONDecodeError, KeyError, ValueError):
        pass
    return None


def _keyword_search(query, learnings):
    """Score learnings by keyword overlap."""
    words = set(query.lower().split())
    candidates = []
    for d in learnings:
        total_score = (
            len(words & set(d.get("task", "").lower().split())) * 3
            + len(words & set(d.get("lesson", "").lower().split())) * 2
            + len(words & set(d.get("approach", "").lower().split()))
        )
        weighted = total_score * (d.get("score", 3) / 5.0)
        if weighted > 0:
            candidates.append((weighted, d))

    if not candidates:
        return None
    candidates.sort(key=lambda x: -x[0])
    best_weight, best_d = candidates[0]
    if best_weight < 2:
        return None
    return _make_result(best_d, min(int(best_weight * 20), 99), len(candidates) - 1, "keyword")


def _try_embedding_search(query, learnings):
    """Try embedding-based semantic search."""
    try:
        from cc_flow.embeddings import semantic_search
        documents = [
            {"id": str(i), "text": f"{d.get('task', '')} | {d.get('lesson', '')} | {d.get('approach', '')}",
             "index": i}
            for i, d in enumerate(learnings)
        ]
        results = semantic_search(query, documents, top_n=3)
        if results and results[0].get("score", 0) > 0.3:
            best_idx = results[0]["index"]
            best = learnings[best_idx]
            confidence = min(int(results[0]["score"] * 100), 99)
            return _make_result(best, confidence, len(results) - 1, "embedding")
    except (ImportError, RuntimeError, TimeoutError, OSError, json.JSONDecodeError, KeyError, ValueError):
        pass
    return None


def _search_learnings(query):
    """Search learnings — tries rerank -> embedding -> keyword fallback."""
    if not LEARNINGS_DIR.exists():
        return None
    learnings = [
        d for f in LEARNINGS_DIR.glob("*.json")
        if (d := safe_json_load(f, default=None)) and d.get("score", 0) >= 2
    ]
    if not learnings:
        return None
    return (
        _try_morph_rerank(query, learnings)
        or _try_embedding_search(query, learnings)
        or _keyword_search(query, learnings)
    )


# ── Consolidation ──

def _load_learnings_with_paths():
    """Load all learning JSON files, attaching their file path."""
    if not LEARNINGS_DIR.exists():
        return []
    entries = []
    for f in sorted(LEARNINGS_DIR.glob("*.json")):
        d = safe_json_load(f, default=None)
        if d:
            d["_path"] = str(f)
            entries.append(d)
    return entries


def _promote_pattern(key, group, promoted_dir):
    """Promote a high-scoring learning group to a pattern file."""
    avg_score = sum(e.get("score", 3) for e in group) / len(group)
    success_count = sum(1 for e in group if e.get("outcome") == "success")
    if avg_score < 4 or success_count < 2:
        return False
    best = max(group, key=lambda e: e.get("score", 0))
    pattern = {
        "task_pattern": key,
        "approach": best.get("approach"),
        "lesson": best.get("lesson"),
        "avg_score": round(avg_score, 1),
        "success_rate": int(success_count / len(group) * 100),
        "occurrences": len(group),
        "promoted_at": now_iso(),
    }
    fname = key.replace(" ", "-")[:30] + ".json"
    (promoted_dir / fname).write_text(json.dumps(pattern, indent=2) + "\n")
    return True


def _dedup_group(group):
    """Keep top 3 entries in a group, remove the rest."""
    if len(group) <= 3:
        return 0
    group.sort(key=lambda e: -e.get("score", 0))
    for entry in group[3:]:
        Path(entry["_path"]).unlink(missing_ok=True)
    return len(group) - 3


def cmd_consolidate(_args):
    """Consolidate learnings: merge similar entries, promote high-score patterns."""
    learnings = _load_learnings_with_paths()
    if len(learnings) < 2:
        print(json.dumps({"success": True, "consolidated": 0, "promoted": 0}))
        return

    groups = {}
    for entry in learnings:
        task_key = " ".join(sorted(entry.get("task", "").lower().split()[:3]))
        groups.setdefault(task_key, []).append(entry)

    consolidated = 0
    promoted = 0
    promoted_dir = TASKS_DIR / "patterns"
    promoted_dir.mkdir(parents=True, exist_ok=True)

    for key, group in groups.items():
        if len(group) < 2:
            continue
        if _promote_pattern(key, group, promoted_dir):
            promoted += 1
        consolidated += _dedup_group(group)

    print(json.dumps({
        "success": True,
        "consolidated": consolidated,
        "promoted": promoted,
        "total_learnings": len(learnings) - consolidated,
        "patterns": len(list(promoted_dir.glob("*.json"))),
    }))
