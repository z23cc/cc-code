"""cc-flow route_learn commands."""

import json
from datetime import datetime, timezone
from pathlib import Path

from cc_flow.core import (
    LEARNINGS_DIR,
    ROUTE_STATS_FILE,
    TASKS_DIR,
    error,
    get_morph_client,
    now_iso,
    safe_json_load,
)

ROUTE_TABLE = [
    # (keywords, command, team, description)
    (["new feature", "add feature", "implement", "build", "新功能", "加功能"],
     "/brainstorm", "feature-dev", "New feature → brainstorm first"),
    (["bug", "broken", "error", "fix", "crash", "报错", "故障", "修"],
     "/debug", "bug-fix", "Bug → systematic debugging"),
    (["review", "code review", "check code", "审查", "看看代码"],
     "/review", "review", "Code review"),
    (["refactor", "clean up", "simplify", "重构", "简化", "清理"],
     "/simplify", "refactor", "Refactoring"),
    (["test", "tdd", "write test", "写测试"],
     "/tdd", None, "Test-driven development"),
    (["deploy", "ship", "release", "上线", "部署", "发布"],
     "/commit", None, "Ship → commit and push"),
    (["plan", "design", "architecture", "规划", "设计", "架构"],
     "/plan", "feature-dev", "Planning"),
    (["slow", "performance", "optimize", "慢", "性能", "优化"],
     "/perf", None, "Performance optimization"),
    (["docs", "readme", "changelog", "文档"],
     "/docs", None, "Documentation"),
    (["scaffold", "new project", "init", "新项目", "创建项目"],
     "/scaffold", None, "New project setup"),
    (["improve", "autoimmune", "自动改进", "自动优化"],
     "/autoimmune", "autoimmune", "Autonomous improvement"),
    (["audit", "health", "ready", "体检", "审计"],
     "/audit", "audit", "Project health check"),
    (["task", "epic", "progress", "任务", "进度"],
     "/tasks", None, "Task management"),
    (["incident", "outage", "down", "事故", "宕机"],
     "/debug", "bug-fix", "Incident response (use incident skill)"),
    (["upgrade", "dependency", "依赖", "升级"],
     None, None, "Dependency upgrade (use dependency-upgrade skill)"),
]


def _load_route_stats():
    """Load route success/failure stats for adaptive confidence."""
    return safe_json_load(ROUTE_STATS_FILE, default={"commands": {}, "updated": ""})


def _save_route_stats(stats):
    stats["updated"] = now_iso()
    ROUTE_STATS_FILE.write_text(json.dumps(stats, indent=2) + "\n")


def cmd_route(args):
    """Analyze user intent and suggest the best command + team."""
    query = " ".join(args.query).lower() if args.query else ""

    if not query:
        error("Provide a task description")

    # Check learnings for past similar tasks
    past_match = _search_learnings(query)

    # Load route stats for adaptive confidence
    route_stats = _load_route_stats()

    # Check promoted patterns for high-confidence matches
    patterns_dir = TASKS_DIR / "patterns"
    pattern_match = None
    if patterns_dir.exists():
        for f in patterns_dir.glob("*.json"):
            try:
                p = json.loads(f.read_text())
                pattern_words = set(p.get("task_pattern", "").split())
                query_words = set(query.split())
                overlap = len(pattern_words & query_words)
                if overlap >= 2 and p.get("success_rate", 0) >= 70:
                    pattern_match = {
                        "pattern": p.get("task_pattern"),
                        "approach": p.get("approach"),
                        "success_rate": p.get("success_rate"),
                        "occurrences": p.get("occurrences"),
                    }
                    break
            except (json.JSONDecodeError, KeyError):
                continue

    matches = []
    for keywords, command, team, desc in ROUTE_TABLE:
        score = sum(1 for kw in keywords if kw in query)
        if score > 0:
            matches.append({"score": score, "command": command, "team": team, "description": desc})

    matches.sort(key=lambda x: -x["score"])
    best = matches[0] if matches else None

    # Calculate routing confidence — combines keyword match, learnings, patterns, and history
    confidence = 0
    if best:
        confidence = min(best["score"] * 25, 80)
    if past_match and past_match.get("confidence", 0) > confidence:
        confidence = past_match["confidence"]
    if pattern_match and pattern_match.get("success_rate", 0) > confidence:
        confidence = pattern_match["success_rate"]

    # Boost/penalize based on historical route success rates
    suggested_cmd = best["command"] if best else "/brainstorm"
    cmd_stats = route_stats.get("commands", {}).get(suggested_cmd, {})
    if cmd_stats:
        total = cmd_stats.get("success", 0) + cmd_stats.get("failure", 0)
        if total >= 3:
            hist_rate = int(cmd_stats["success"] / total * 100)
            # Blend: 70% current confidence + 30% historical success rate
            confidence = int(confidence * 0.7 + hist_rate * 0.3)

    result = {
        "success": True,
        "query": query,
        "confidence": min(confidence, 99),
        "suggestion": {
            "command": suggested_cmd,
            "team": best.get("team") if best else None,
            "reason": best["description"] if best else "Default: start with brainstorming",
        },
    }
    if past_match:
        result["past_learning"] = past_match
    if pattern_match:
        result["promoted_pattern"] = pattern_match
    if cmd_stats:
        s = cmd_stats.get("success", 0)
        f = cmd_stats.get("failure", 0)
        result["route_history"] = {"uses": s + f, "success_rate": int(s / (s + f) * 100) if (s + f) > 0 else 0}
    if matches and len(matches) > 1:
        result["alternatives"] = [
            {"command": m["command"], "reason": m["description"]}
            for m in matches[1:3]
        ]

    print(json.dumps(result))


# ─── Learning Loop ───


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

    # Filename from timestamp + microseconds for uniqueness
    fname = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S-%f") + ".json"
    path = LEARNINGS_DIR / fname
    path.write_text(json.dumps(learning, indent=2) + "\n")

    # Update route stats if command was recorded
    if learning.get("command"):
        stats = _load_route_stats()
        cmd = learning["command"]
        if cmd not in stats["commands"]:
            stats["commands"][cmd] = {"success": 0, "failure": 0}
        if args.outcome == "success":
            stats["commands"][cmd]["success"] += 1
        elif args.outcome == "failed":
            stats["commands"][cmd]["failure"] += 1
        else:  # partial
            stats["commands"][cmd]["success"] += 0.5
        _save_route_stats(stats)

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

    # Show recent N
    n = args.last or 10
    recent = learnings[-n:]

    print(json.dumps({"success": True, "learnings": recent, "count": len(learnings)}))


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
    """Try semantic reranking via Morph. Returns result dict or None."""
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
    except Exception:
        pass
    return None


def _keyword_search(query, learnings):
    """Score learnings by keyword overlap. Returns result dict or None."""
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


def _search_learnings(query):
    """Search learnings — uses Morph Rerank if available, falls back to keyword overlap."""
    if not LEARNINGS_DIR.exists():
        return None

    learnings = [
        d for f in LEARNINGS_DIR.glob("*.json")
        if (d := safe_json_load(f, default=None)) and d.get("score", 0) >= 2
    ]
    if not learnings:
        return None

    return _try_morph_rerank(query, learnings) or _keyword_search(query, learnings)


def cmd_consolidate(_args):
    """Consolidate learnings: merge similar entries, promote high-score patterns."""
    if not LEARNINGS_DIR.exists():
        print(json.dumps({"success": True, "consolidated": 0, "promoted": 0}))
        return

    learnings = []
    for f in sorted(LEARNINGS_DIR.glob("*.json")):
        d = safe_json_load(f, default=None)
        if not d:
            continue
        d["_path"] = str(f)
        learnings.append(d)

    if len(learnings) < 2:
        print(json.dumps({"success": True, "consolidated": 0, "promoted": 0}))
        return

    # Group by task similarity
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

        # Average score for this pattern
        avg_score = sum(e.get("score", 3) for e in group) / len(group)
        success_count = sum(1 for e in group if e.get("outcome") == "success")
        success_rate = int(success_count / len(group) * 100)

        # Promote patterns with high avg score and multiple successes
        if avg_score >= 4 and success_count >= 2:
            best = max(group, key=lambda e: e.get("score", 0))
            pattern = {
                "task_pattern": key,
                "approach": best.get("approach"),
                "lesson": best.get("lesson"),
                "avg_score": round(avg_score, 1),
                "success_rate": success_rate,
                "occurrences": len(group),
                "promoted_at": now_iso(),
            }
            fname = key.replace(" ", "-")[:30] + ".json"
            (promoted_dir / fname).write_text(json.dumps(pattern, indent=2) + "\n")
            promoted += 1

        # Keep only the best entry per group, remove duplicates
        if len(group) > 3:
            group.sort(key=lambda e: -e.get("score", 0))
            for entry in group[3:]:
                Path(entry["_path"]).unlink(missing_ok=True)
                consolidated += 1

    print(json.dumps({
        "success": True,
        "consolidated": consolidated,
        "promoted": promoted,
        "total_learnings": len(learnings) - consolidated,
        "patterns": len(list(promoted_dir.glob("*.json"))),
    }))


# ─── Auto (integrated autoimmune) ───
