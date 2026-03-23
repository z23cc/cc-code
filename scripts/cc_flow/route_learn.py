"""cc-flow routing — smart command routing with Q-learning.

Learning commands (learn, learnings, consolidate) moved to learning.py.
"""

import json

from cc_flow.core import (
    ROUTE_STATS_FILE,
    TASKS_DIR,
    error,
    now_iso,
    safe_json_load,
)

ROUTE_TABLE = [
    # Columns: keywords, command, team, description
    (["new feature", "add feature", "implement", "build", "create",
      "新功能", "加功能", "新增", "添加", "实现", "创建"],
     "/brainstorm", "feature-dev", "New feature → brainstorm first"),
    (["bug", "broken", "error", "fix", "crash", "fail",
      "报错", "故障", "修", "修复", "崩溃", "出错"],
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
    (["ui", "ux", "design", "accessibility", "color", "font", "responsive",
      "component", "layout", "界面", "配色", "UI审查", "设计审查"],
     "/cc-ui-ux", None, "UI/UX design review"),
    (["browser", "screenshot", "scrape", "e2e", "fill form", "open site",
      "浏览器", "截图", "打开网站", "表单"],
     "/cc-browser", None, "Browser automation + E2E testing"),
    (["scaffold", "new project", "init", "新项目", "创建项目"],
     "/scaffold", None, "New project setup"),
    (["improve", "autoimmune", "自动改进", "自动优化"],
     "/autoimmune", "autoimmune", "Autonomous improvement"),
    (["onboard", "new to", "接手", "熟悉项目", "了解项目", "first time"],
     "/cc-prime", None, "Onboard → full project scan"),
    (["audit", "health", "ready", "体检", "审计"],
     "/audit", "audit", "Project health check"),
    (["task", "epic", "progress", "任务", "进度"],
     "/tasks", None, "Task management"),
    (["incident", "outage", "down", "事故", "宕机"],
     "/debug", "bug-fix", "Incident response (use incident skill)"),
    (["upgrade", "dependency", "依赖", "升级"],
     None, None, "Dependency upgrade (use dependency-upgrade skill)"),
    (["deep search", "understand code", "how does", "explain code", "analyze code",
      "深度搜索", "理解代码", "分析代码", "代码怎么工作"],
     "deep-search", None, "Deep search → Morph find + RP analyze"),
    (["smart chat", "memory chat", "enhanced chat", "past experience",
      "智能对话", "记忆对话", "历史经验"],
     "smart-chat", None, "Memory-enhanced chat (recall + RP)"),
    (["embed structure", "similar function", "find duplicate", "code similarity",
      "向量化", "相似函数", "重复代码", "代码相似"],
     "embed-structure", None, "Code structure → Morph embed (similarity)"),
    (["past review", "review history", "what went wrong",
      "过去审查", "审查历史", "以前的问题"],
     "recall-review", None, "Recall past review findings from memory"),
    (["bridge", "morph rp supermemory", "system status", "api status",
      "桥接状态", "系统状态", "连接状态"],
     "bridge-status", None, "Check Morph × RP × Supermemory status"),
]


def _load_route_stats():
    """Load route success/failure stats for adaptive confidence."""
    return safe_json_load(ROUTE_STATS_FILE, default={"commands": {}, "updated": ""})


def _save_route_stats(stats):
    stats["updated"] = now_iso()
    ROUTE_STATS_FILE.write_text(json.dumps(stats, indent=2) + "\n")


def _find_pattern_match(query):
    """Search promoted patterns for a high-confidence match."""
    patterns_dir = TASKS_DIR / "patterns"
    if not patterns_dir.exists():
        return None
    query_words = set(query.split())
    for f in patterns_dir.glob("*.json"):
        p = safe_json_load(f, default=None)
        if not p:
            continue
        overlap = len(set(p.get("task_pattern", "").split()) & query_words)
        if overlap >= 2 and p.get("success_rate", 0) >= 70:
            return {
                "pattern": p.get("task_pattern"),
                "approach": p.get("approach"),
                "success_rate": p.get("success_rate"),
                "occurrences": p.get("occurrences"),
            }
    return None


def _keyword_route(query):
    """Match query against ROUTE_TABLE, return sorted matches."""
    matches = []
    for keywords, command, team, desc in ROUTE_TABLE:
        score = sum(1 for kw in keywords if kw in query)
        if score > 0:
            matches.append({"score": score, "command": command, "team": team, "description": desc})
    matches.sort(key=lambda x: -x["score"])
    return matches


def _calc_confidence(best, past_match, pattern_match, cmd_stats):
    """Compute routing confidence from multiple signals."""
    confidence = min(best["score"] * 25, 80) if best else 0
    if past_match and past_match.get("confidence", 0) > confidence:
        confidence = past_match["confidence"]
    if pattern_match and pattern_match.get("success_rate", 0) > confidence:
        confidence = pattern_match["success_rate"]
    if cmd_stats:
        total = cmd_stats.get("success", 0) + cmd_stats.get("failure", 0)
        if total >= 3:
            hist_rate = int(cmd_stats["success"] / total * 100)
            confidence = int(confidence * 0.7 + hist_rate * 0.3)
    return min(confidence, 99)


def _attach_memory_recall(result, query):
    """Attach Supermemory recall results to route if available."""
    try:
        from cc_flow.memory import _get_client
        client = _get_client()
        if not client:
            return
        results = client.search.execute(
            q=query, container_tags=["cc-flow", "learning"],
            limit=2, rerank=True,
        )
        items = [
            (getattr(c, "summary", "") or getattr(c, "content", "") or "")[:100]
            for c in getattr(results, "results", [])
        ]
        if items:
            result["memory_recall"] = items
    except (ImportError, RuntimeError, TimeoutError, OSError, ValueError, KeyError):
        pass


def _attach_chain(result, query):
    """Attach matching skill chain to route result."""
    try:
        from cc_flow.skill_chains import find_chain
        chain_name, chain_data = find_chain(query)
        if chain_name:
            result["skill_chain"] = {
                "name": chain_name,
                "description": chain_data["description"],
                "steps": [s["skill"] for s in chain_data["skills"]],
                "run": f"cc-flow chain run {chain_name}",
            }
    except ImportError:
        pass


def cmd_route(args):
    """Analyze user intent and suggest the best command + team."""

    query = " ".join(args.query).lower() if args.query else ""
    if not query:
        error("Provide a task description")

    # Q-Learning route (highest priority if available)
    try:
        from cc_flow.qrouter import q_route
        q_cmd, q_conf, q_cat = q_route(query)
    except ImportError:
        q_cmd, q_conf, q_cat = None, 0, "general"

    past_match = _search_learnings(query)
    pattern_match = _find_pattern_match(query)
    matches = _keyword_route(query)
    best = matches[0] if matches else None

    route_stats = _load_route_stats()
    suggested_cmd = best["command"] if best else "/brainstorm"

    # Q-learning override if high confidence
    if q_cmd and q_conf > 60:
        suggested_cmd = q_cmd

    cmd_stats = route_stats.get("commands", {}).get(suggested_cmd, {})

    result = {
        "success": True,
        "query": query,
        "confidence": _calc_confidence(best, past_match, pattern_match, cmd_stats),
        "suggestion": {
            "command": suggested_cmd,
            "team": best.get("team") if best else None,
            "reason": best["description"] if best else "Default: start with brainstorming",
        },
    }
    _attach_chain(result, query)

    _attach_memory_recall(result, query)

    if past_match:
        result["past_learning"] = past_match
    if pattern_match:
        result["promoted_pattern"] = pattern_match
    if cmd_stats:
        s = cmd_stats.get("success", 0)
        f = cmd_stats.get("failure", 0)
        result["route_history"] = {"uses": s + f, "success_rate": int(s / (s + f) * 100) if (s + f) > 0 else 0}
    if q_cmd:
        result["q_learning"] = {"command": q_cmd, "confidence": q_conf, "category": q_cat}
    if len(matches) > 1:
        result["alternatives"] = [
            {"command": m["command"], "reason": m["description"]}
            for m in matches[1:3]
        ]

    print(json.dumps(result))


# Re-export learning commands for backward compatibility
from cc_flow.learning import (  # noqa: E402, F401
    _keyword_search,
    _make_result,
    _search_learnings,
    cmd_consolidate,
    cmd_learn,
    cmd_learnings,
)
