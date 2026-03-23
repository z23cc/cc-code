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
        "description": "UI design → review → test",
        "trigger": ["design UI", "UI review", "frontend", "design", "界面设计", "设计", "UI审查", "前端"],
        "skills": [
            {"skill": "/cc-ui-ux", "role": "Design decisions (style, colors, fonts)", "required": True},
            {"skill": "/cc-web-design", "role": "Check against Web Interface Guidelines", "required": False},
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
