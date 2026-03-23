"""cc-flow skill chains — predefined multi-skill workflows.

Maps common development scenarios to ordered skill sequences.
Each chain defines: skills to invoke, their order, and what
context passes between them.

Used by: route (suggest chains), pipeline (execute chains).
"""

import json

from cc_flow.core import error

SKILL_CHAINS = {
    "feature": {
        "description": "Full feature development lifecycle",
        "trigger": ["new feature", "add feature", "add new", "build", "implement", "create", "新功能", "新增"],
        "skills": [
            {"skill": "/cc-brainstorm", "role": "Design exploration", "required": True},
            {"skill": "/cc-plan", "role": "Implementation plan with tasks", "required": True},
            {"skill": "/cc-tdd", "role": "Test-driven implementation", "required": True},
            {"skill": "/cc-review", "role": "Code review (parallel reviewers)", "required": True},
            {"skill": "/cc-commit", "role": "Verify and commit", "required": True},
        ],
    },
    "bugfix": {
        "description": "Systematic bug fix",
        "trigger": ["fix bug", "debug", "crash", "error", "修bug", "修复"],
        "skills": [
            {"skill": "/cc-debug", "role": "Root cause analysis", "required": True},
            {"skill": "/cc-tdd", "role": "Write regression test + fix", "required": True},
            {"skill": "/cc-review", "role": "Verify no side effects", "required": False},
            {"skill": "/cc-commit", "role": "Commit fix", "required": True},
        ],
    },
    "ui-design": {
        "description": "UI design → review → optimize → test",
        "trigger": ["design UI", "UI review", "frontend", "design", "界面设计", "设计", "UI审查", "前端"],
        "skills": [
            {"skill": "/cc-ui-ux", "role": "Design decisions (style, colors, fonts)", "required": True},
            {"skill": "/cc-web-design", "role": "Check against Web Interface Guidelines", "required": False},
            {"skill": "/cc-optimize", "role": "Performance optimization (Core Web Vitals)", "required": False},
            {"skill": "/cc-browser", "role": "Visual testing + screenshots", "required": False},
        ],
    },
    "quality": {
        "description": "Full quality gate",
        "trigger": ["quality check", "audit", "is this ready", "质量检查", "审计"],
        "skills": [
            {"skill": "/cc-autoimmune", "role": "Auto-scan and fix", "required": True},
            {"skill": "/cc-audit", "role": "8-pillar readiness check", "required": True},
            {"skill": "/cc-review", "role": "Final code review", "required": False},
        ],
    },
    "onboard": {
        "description": "Understand a new codebase",
        "trigger": ["new project", "onboard", "understand code", "接手项目", "了解代码"],
        "skills": [
            {"skill": "/cc-research", "role": "Investigate architecture", "required": True},
            {"skill": "/cc-scout repo", "role": "Find existing patterns", "required": True},
            {"skill": "/cc-scout testing", "role": "Check test setup", "required": False},
            {"skill": "/cc-scout security", "role": "Security config review", "required": False},
            {"skill": "/cc-prime", "role": "Full project assessment", "required": False},
        ],
    },
    "release": {
        "description": "Pre-release checklist",
        "trigger": ["release", "ship", "deploy", "发布", "上线"],
        "skills": [
            {"skill": "/cc-refine", "role": "Polish and harden", "required": True},
            {"skill": "/cc-security-review", "role": "Security scan", "required": True},
            {"skill": "/cc-review", "role": "Final review", "required": True},
            {"skill": "/cc-docs", "role": "Update documentation", "required": True},
            {"skill": "/cc-commit", "role": "Tag and push", "required": True},
        ],
    },
    "refactor": {
        "description": "Safe refactoring with tests",
        "trigger": ["refactor", "clean up", "simplify", "重构", "清理"],
        "skills": [
            {"skill": "/cc-research", "role": "Map dependencies", "required": True},
            {"skill": "/cc-simplify", "role": "Apply refactoring", "required": True},
            {"skill": "/cc-review", "role": "Verify behavior preserved", "required": True},
            {"skill": "/cc-commit", "role": "Commit changes", "required": True},
        ],
    },
    "research": {
        "description": "Deep codebase understanding (Morph + RP + Memory)",
        "trigger": ["understand", "how does", "explain", "research", "deep dive",
                     "理解", "怎么工作", "深度分析", "调研"],
        "skills": [
            {"skill": "deep-search", "role": "Morph search → RP builder (find + analyze)", "required": True},
            {"skill": "/cc-research", "role": "Structured codebase research", "required": False},
            {"skill": "/cc-scout repo", "role": "Find existing patterns", "required": False},
        ],
    },
    # ── New chains: end-to-end workflows ──
    "idea-to-ship": {
        "description": "Full lifecycle: validate idea → plan → implement → review → ship",
        "trigger": ["idea to production", "end to end", "full lifecycle", "from scratch",
                     "idea to ship", "complete workflow", "everything",
                     "从想法到上线", "想法到发布", "端到端", "完整流程", "从零开始"],
        "skills": [
            {"skill": "/cc-office-hours", "role": "Validate the idea (5 forcing questions)", "required": True},
            {"skill": "/cc-brainstorm", "role": "Explore design options", "required": True},
            {"skill": "/cc-grill-me", "role": "Adversarial review of the plan", "required": False},
            {"skill": "/cc-plan", "role": "Create implementation plan with tasks", "required": True},
            {"skill": "/cc-work", "role": "Execute tasks (worktree + worker + review)", "required": True},
            {"skill": "/cc-epic-review", "role": "Verify all requirements met", "required": True},
            {"skill": "/cc-ship", "role": "Version bump + PR + release", "required": True},
        ],
    },
    "qa-fix": {
        "description": "QA test → fix bugs → verify → ship",
        "trigger": ["qa", "test the site", "find and fix bugs", "QA测试", "测试修复"],
        "skills": [
            {"skill": "/cc-qa", "role": "Diff-aware QA with health scoring", "required": True},
            {"skill": "/cc-review", "role": "Review the fixes", "required": False},
            {"skill": "/cc-commit", "role": "Commit verified fixes", "required": True},
        ],
    },
    "security-audit": {
        "description": "Full security review: scout → code review → fix",
        "trigger": ["security audit", "security review", "security scan", "penetration", "vulnerability",
                     "安全审计", "安全审查", "安全检查", "漏洞扫描"],
        "skills": [
            {"skill": "/cc-scout security", "role": "Check security config", "required": True},
            {"skill": "/cc-security-review", "role": "Code-level security patterns", "required": True},
            {"skill": "/cc-review", "role": "Final review of fixes", "required": False},
            {"skill": "/cc-commit", "role": "Commit security fixes", "required": True},
        ],
    },
    "performance": {
        "description": "Profile → optimize → verify improvement",
        "trigger": ["performance", "slow", "speed up", "optimize", "profile",
                     "性能优化", "太慢", "加速"],
        "skills": [
            {"skill": "/cc-performance", "role": "Profile and identify bottlenecks", "required": True},
            {"skill": "/cc-optimize", "role": "Frontend Core Web Vitals optimization", "required": False},
            {"skill": "/cc-review", "role": "Review optimization changes", "required": False},
            {"skill": "/cc-commit", "role": "Commit improvements", "required": True},
        ],
    },
    "incident": {
        "description": "Production incident: triage → fix → postmortem → prevent",
        "trigger": ["incident", "production down", "outage", "sev1",
                     "生产故障", "线上崩了", "紧急修复"],
        "skills": [
            {"skill": "/cc-incident", "role": "Triage + investigate + mitigate", "required": True},
            {"skill": "/cc-debug", "role": "Root cause analysis", "required": True},
            {"skill": "/cc-tdd", "role": "Regression test + fix", "required": True},
            {"skill": "/cc-review", "role": "Verify fix safety", "required": True},
            {"skill": "/cc-retro", "role": "Postmortem and learnings", "required": False},
        ],
    },
    "docs-update": {
        "description": "Documentation refresh: audit gaps → update → verify",
        "trigger": ["update docs", "documentation", "readme", "stale docs",
                     "更新文档", "文档过期", "写文档"],
        "skills": [
            {"skill": "/cc-scout docs-gap", "role": "Find stale/missing documentation", "required": True},
            {"skill": "/cc-docs", "role": "Update README, CHANGELOG, API docs", "required": True},
            {"skill": "/cc-commit", "role": "Commit doc updates", "required": True},
        ],
    },
    "dependency-upgrade": {
        "description": "Safe dependency upgrade: audit → upgrade → test → fix",
        "trigger": ["upgrade deps", "update dependencies", "outdated packages",
                     "升级依赖", "更新包", "依赖过期"],
        "skills": [
            {"skill": "/cc-dependency-upgrade", "role": "Audit and plan upgrades", "required": True},
            {"skill": "/cc-verification", "role": "Run full test suite", "required": True},
            {"skill": "/cc-review", "role": "Review breaking changes", "required": False},
            {"skill": "/cc-commit", "role": "Commit upgrades", "required": True},
        ],
    },
    "api-feature": {
        "description": "API development: design → scaffold → implement → test",
        "trigger": ["build api", "new endpoint", "api development", "rest api",
                     "api", "endpoint", "接口", "写API", "新接口", "API开发", "写接口"],
        "skills": [
            {"skill": "/cc-brainstorm", "role": "API design exploration", "required": True},
            {"skill": "/cc-plan", "role": "Endpoint specs with request/response", "required": True},
            {"skill": "/cc-fastapi", "role": "FastAPI patterns and implementation", "required": True},
            {"skill": "/cc-tdd", "role": "Test-driven endpoint development", "required": True},
            {"skill": "/cc-security-review", "role": "Auth + input validation review", "required": True},
            {"skill": "/cc-commit", "role": "Commit API changes", "required": True},
        ],
    },
    "autonomous": {
        "description": "Unattended autonomous loop with quality gates",
        "trigger": ["autonomous", "ralph", "unattended", "run all tasks",
                     "自治", "无人值守", "自动跑"],
        "skills": [
            {"skill": "/cc-autonomous-loops", "role": "Choose loop pattern", "required": True},
            {"skill": "/cc-work", "role": "Execute tasks with worker isolation", "required": True},
            {"skill": "/cc-epic-review", "role": "Verify epic completion", "required": True},
        ],
    },
}


def find_chain(query):
    """Find the best matching skill chain for a query."""
    query_lower = query.lower()
    words = set(query_lower.split())
    best_chain = None
    best_score = 0

    for name, chain in SKILL_CHAINS.items():
        score = 0
        for trigger in chain["trigger"]:
            # Full phrase match (weighted 2x)
            if trigger in query_lower:
                score += 2
            # Word overlap match
            elif any(w in words for w in trigger.split()):
                score += 1
        if score > best_score:
            best_score = score
            best_chain = name

    if best_chain and best_score > 0:
        return best_chain, SKILL_CHAINS[best_chain]
    return None, None


def cmd_chain_list(_args):
    """List all predefined skill chains."""
    result = {}
    for name, chain in SKILL_CHAINS.items():
        result[name] = {
            "description": chain["description"],
            "skills": len(chain["skills"]),
            "required": sum(1 for s in chain["skills"] if s["required"]),
        }
    print(json.dumps({"success": True, "chains": result, "count": len(result)}))


def cmd_chain_show(args):
    """Show a skill chain's steps."""
    name = args.name
    if name not in SKILL_CHAINS:
        error(f"Chain not found: {name}. Available: {', '.join(SKILL_CHAINS.keys())}")

    chain = SKILL_CHAINS[name]
    print(json.dumps({
        "success": True,
        "name": name,
        "description": chain["description"],
        "skills": chain["skills"],
    }))


def cmd_chain_suggest(args):
    """Suggest the best skill chain for a task description."""
    query = " ".join(args.query) if args.query else ""
    if not query:
        error("Provide a task description")

    name, chain = find_chain(query)
    if not chain:
        print(json.dumps({
            "success": True,
            "suggestion": None,
            "message": "No matching chain. Try: cc-flow chain list",
        }))
        return

    print(json.dumps({
        "success": True,
        "chain": name,
        "description": chain["description"],
        "steps": [
            f"{'[required]' if s['required'] else '[optional]'} {s['skill']} — {s['role']}"
            for s in chain["skills"]
        ],
        "instruction": f"Run skills in order: {' → '.join(s['skill'] for s in chain['skills'])}",
    }))


def cmd_chain_run(args):
    """Execute a skill chain — outputs step-by-step instructions for the agent."""
    name = args.name
    if name not in SKILL_CHAINS:
        error(f"Chain not found: {name}. Available: {', '.join(SKILL_CHAINS.keys())}")

    chain = SKILL_CHAINS[name]
    only_required = getattr(args, "required_only", False)

    steps = chain["skills"]
    if only_required:
        steps = [s for s in steps if s["required"]]

    print(json.dumps({
        "success": True,
        "chain": name,
        "description": chain["description"],
        "execute": [
            {
                "step": i + 1,
                "skill": s["skill"],
                "role": s["role"],
                "required": s["required"],
                "instruction": f"Run: {s['skill']}",
            }
            for i, s in enumerate(steps)
        ],
        "total_steps": len(steps),
        "instruction": (
            f"Execute this {name} chain step by step:\n"
            + "\n".join(f"  {i + 1}. {s['skill']} — {s['role']}" for i, s in enumerate(steps))
            + "\n\nStart with step 1. After each step completes, proceed to the next."
        ),
    }))
