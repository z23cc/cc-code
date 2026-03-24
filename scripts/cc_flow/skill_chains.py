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
            {"skill": "/cc-brainstorm", "role": "Design exploration", "required": True,
             "outputs": ["design_doc", "decisions", "acceptance_criteria"]},
            {"skill": "/cc-plan", "role": "Implementation plan with tasks", "required": True,
             "reads": ["design_doc", "decisions"], "outputs": ["epic_id", "task_ids", "plan_doc"]},
            {"skill": "/cc-tdd", "role": "Test-driven implementation", "required": True,
             "reads": ["epic_id", "task_ids"], "outputs": ["test_results", "files_changed", "coverage"]},
            {"skill": "/cc-review", "role": "Code review (parallel reviewers)", "required": True,
             "reads": ["files_changed"], "outputs": ["verdict", "issues_fixed"]},
            {"skill": "/cc-commit", "role": "Verify and commit", "required": True,
             "reads": ["verdict"]},
        ],
    },
    "bugfix": {
        "description": "Systematic bug fix",
        "trigger": ["fix bug", "debug", "crash", "error", "修bug", "修复"],
        "skills": [
            {"skill": "/cc-debug", "role": "Root cause analysis", "required": True,
             "outputs": ["root_cause", "fix_description", "regression_test"]},
            {"skill": "/cc-tdd", "role": "Write regression test + fix", "required": True,
             "reads": ["root_cause", "fix_description"], "outputs": ["test_results", "files_changed"]},
            {"skill": "/cc-review", "role": "Verify no side effects", "required": False,
             "reads": ["files_changed"], "outputs": ["verdict"]},
            {"skill": "/cc-commit", "role": "Commit fix", "required": True,
             "reads": ["verdict"]},
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
        "description": "Unattended autonomous loop: goal-driven with self-heal + quality gates",
        "trigger": ["autonomous", "ralph", "unattended", "run all tasks", "until done",
                     "keep going", "achieve goal", "goal driven",
                     "自治", "无人值守", "自动跑", "跑到完成", "达成目标"],
        "skills": [
            {"skill": "/cc-autonomous-loops", "role": "Choose loop pattern (simple/ralph/goal-driven)", "required": True},
            {"skill": "/cc-ralph", "role": "Configure Ralph: GOAL, SELF_HEAL, MAX_ITERATIONS", "required": True},
            {"skill": "/cc-work", "role": "Execute tasks with worker isolation", "required": True},
            {"skill": "/cc-autoimmune", "role": "Self-heal: scan + create tasks when stuck", "required": False},
            {"skill": "/cc-epic-review", "role": "Verify goal/epic completion", "required": True},
        ],
    },
    # ── Clone/replicate workflows ──
    "clone-site": {
        "description": "Replicate a reference website: capture → analyze → implement → QA compare",
        "trigger": ["clone", "replicate", "copy this site", "make it look like", "reference site",
                     "look the same", "same as this",
                     "仿站", "照着做", "参考", "一模一样", "一样的", "模仿", "抄这个"],
        "skills": [
            {"skill": "/cc-browser", "role": "Screenshot reference at 3 viewports", "required": True},
            {"skill": "/cc-ui-ux", "role": "Extract design tokens (colors, fonts, spacing)", "required": True},
            {"skill": "/cc-plan", "role": "Create component-level implementation plan", "required": True},
            {"skill": "/cc-tdd", "role": "Implement each component with tests", "required": True},
            {"skill": "/cc-qa", "role": "Visual compare against reference screenshots", "required": True},
            {"skill": "/cc-ship", "role": "Deploy when match achieved", "required": False},
        ],
    },
    # ── Remaining unchained skills ──
    "new-project": {
        "description": "Bootstrap project → design → plan → first feature",
        "trigger": ["new project", "start from scratch", "scaffold", "bootstrap", "init",
                     "新项目", "从零开始", "初始化项目"],
        "skills": [
            {"skill": "/cc-scaffold", "role": "Generate project skeleton", "required": True},
            {"skill": "/cc-brainstorm", "role": "Design first feature", "required": True},
            {"skill": "/cc-plan", "role": "Create implementation plan", "required": True},
            {"skill": "/cc-tdd", "role": "Implement with TDD", "required": True},
        ],
    },
    "full-audit": {
        "description": "Comprehensive project health: all scouts + readiness + deep scan",
        "trigger": ["full audit", "project health", "comprehensive check", "how healthy",
                     "全面体检", "项目健康", "全面审查"],
        "skills": [
            {"skill": "/cc-prime", "role": "Run all 12 scouts in parallel", "required": True},
            {"skill": "/cc-readiness-audit", "role": "8-pillar readiness assessment", "required": True},
            {"skill": "/cc-qa-report", "role": "QA report (browser, no fixes)", "required": False},
            {"skill": "/cc-retro", "role": "Recent work review", "required": False},
        ],
    },
    "deploy": {
        "description": "Pre-deploy verification → deploy → monitor",
        "trigger": ["deploy", "production", "go live", "push to prod",
                     "部署", "上生产", "发布上线"],
        "skills": [
            {"skill": "/cc-readiness-audit", "role": "Pre-deploy readiness check", "required": True},
            {"skill": "/cc-verification", "role": "Full lint + test pass", "required": True},
            {"skill": "/cc-deploy", "role": "Docker + CI/CD deployment", "required": True},
            {"skill": "/cc-ship", "role": "Version bump + PR + push", "required": True},
        ],
    },
    "deep-review": {
        "description": "Multi-layer review: bridge → code review → security → refinement",
        "trigger": ["thorough review", "deep review", "review everything", "pre-merge",
                     "深度审查", "全面审查代码", "合并前检查"],
        "skills": [
            {"skill": "/cc-bridge", "role": "Recall past review findings (memory-enhanced)", "required": False},
            {"skill": "/cc-code-review-loop", "role": "Verdict-driven review + auto-fix", "required": True},
            {"skill": "/cc-security-review", "role": "Security patterns check", "required": True},
            {"skill": "/cc-refinement", "role": "Edge case hardening", "required": False},
        ],
    },
    # ── Fast-track workflows ──
    "hotfix": {
        "description": "Emergency/trivial fix — skip brainstorm+plan, minimal review, fast commit",
        "trigger": ["hotfix", "quick fix", "trivial", "typo", "one-liner", "urgent fix",
                     "emergency fix", "config change", "revert", "bump version",
                     "紧急修复", "快速修复", "小改动", "配置修改", "回滚"],
        "skills": [
            {"skill": "/cc-tdd", "role": "Implement fix (skip TDD if <10 lines)", "required": True,
             "outputs": ["fix_description", "files_changed"]},
            {"skill": "/cc-review", "role": "Quick review (1 loop max)", "required": True,
             "reads": ["files_changed"], "outputs": ["verdict"]},
            {"skill": "/cc-commit", "role": "Commit immediately", "required": True,
             "reads": ["verdict"]},
        ],
    },
    "pr-review": {
        "description": "Review an incoming PR: fetch → review → feedback",
        "trigger": ["review pr", "review pull request", "check this pr", "pr review",
                     "审查PR", "看看PR", "PR审查"],
        "skills": [
            {"skill": "/cc-research", "role": "Understand PR changes", "required": True},
            {"skill": "/cc-code-review-loop", "role": "Verdict-driven review", "required": True},
        ],
    },
    "perf-regression": {
        "description": "Detect and fix performance regression",
        "trigger": ["slow down", "regression", "performance regression", "slower", "latency",
                     "性能回退", "变慢了", "延迟增加"],
        "skills": [
            {"skill": "/cc-performance", "role": "Profile and identify bottleneck", "required": True,
             "outputs": ["bottleneck", "baseline_metrics"]},
            {"skill": "/cc-research", "role": "Bisect commit causing regression", "required": True,
             "reads": ["bottleneck"], "outputs": ["root_cause", "commit"]},
            {"skill": "/cc-tdd", "role": "Fix + regression test", "required": True,
             "reads": ["root_cause"], "outputs": ["fix_description", "test_results"]},
            {"skill": "/cc-review", "role": "Verify fix + no side effects", "required": True},
            {"skill": "/cc-commit", "role": "Commit fix", "required": True},
        ],
    },
    "tech-debt": {
        "description": "Structured technical debt reduction sprint",
        "trigger": ["tech debt", "technical debt", "debt sprint", "cleanup sprint",
                     "技术债", "债务清理", "还债"],
        "skills": [
            {"skill": "/cc-research", "role": "Map debt hotspots", "required": True},
            {"skill": "/cc-plan", "role": "Prioritize by ROI", "required": True},
            {"skill": "/cc-simplify", "role": "Refactor highest-ROI items", "required": True},
            {"skill": "/cc-review", "role": "Verify behavior preserved", "required": True},
            {"skill": "/cc-commit", "role": "Commit improvements", "required": True},
        ],
    },
    "db-migration": {
        "description": "Database schema migration: plan → script → test → deploy",
        "trigger": ["migration", "schema change", "database migration", "alter table",
                     "数据库迁移", "改表", "加字段"],
        "skills": [
            {"skill": "/cc-database", "role": "Design migration plan", "required": True,
             "outputs": ["migration_plan", "rollback_plan"]},
            {"skill": "/cc-tdd", "role": "Write migration + test on clean DB", "required": True,
             "reads": ["migration_plan"], "outputs": ["migration_file", "test_results"]},
            {"skill": "/cc-security-review", "role": "Check for data safety", "required": True},
            {"skill": "/cc-review", "role": "Review migration script", "required": True},
            {"skill": "/cc-commit", "role": "Commit migration", "required": True},
        ],
    },
}


def find_chain(query):
    """Find the best matching skill chain for a query."""
    ranked = _rank_chains(query)
    if ranked:
        name, chain, _score = ranked[0]
        return name, chain
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


def _load_chain_metrics():
    """Load chain metrics for ranking boost. Returns {chain_name: metrics_dict}."""
    try:
        from cc_flow.skill_flow import _load_metrics
        metrics = _load_metrics()
        return metrics.get("chains", {})
    except (ImportError, Exception):
        return {}


def _rank_chains(query):
    """Rank all chains by relevance to query, boosted by historical success.

    Scoring: keyword match (0-N) + metrics bonus (0-3).
    Metrics bonus = success_rate/100 * 3 (max 3 points for 100% success rate).
    Chains with ≥3 runs get full bonus; fewer runs get proportional bonus.
    """
    query_lower = query.lower()
    words = set(query_lower.split())
    metrics = _load_chain_metrics()
    scored = []

    for name, chain in SKILL_CHAINS.items():
        score = 0
        # Keyword matching
        for trigger in chain["trigger"]:
            if trigger in query_lower:
                score += 2
            elif any(w in words for w in trigger.split()):
                score += 1

        if score > 0:
            # Metrics boost: success_rate * confidence_factor * 3
            m = metrics.get(name, {})
            runs = m.get("runs", 0)
            success_rate = m.get("success_rate", 0)
            if runs > 0:
                # Confidence grows with runs: 0.33 at 1 run, 0.67 at 2, 1.0 at 3+
                confidence = min(runs / 3.0, 1.0)
                bonus = (success_rate / 100.0) * confidence * 3.0
                score += bonus

            scored.append((name, chain, score))

    scored.sort(key=lambda x: -x[2])
    return scored


def cmd_chain_suggest(args):
    """Suggest the best skill chain(s) for a task description."""
    query = " ".join(args.query) if args.query else ""
    if not query:
        error("Provide a task description")

    ranked = _rank_chains(query)
    if not ranked:
        print(json.dumps({
            "success": True,
            "suggestion": None,
            "message": "No matching chain. Try: cc-flow chain list",
        }))
        return

    best_name, best_chain, best_score = ranked[0]

    # Include metrics for best chain
    metrics = _load_chain_metrics()
    best_metrics = metrics.get(best_name, {})

    result = {
        "success": True,
        "chain": best_name,
        "description": best_chain["description"],
        "score": round(best_score, 1),
        "steps": [
            f"{'[required]' if s['required'] else '[optional]'} {s['skill']} — {s['role']}"
            for s in best_chain["skills"]
        ],
        "instruction": f"Run: cc-flow go \"{query}\"  (or: cc-flow chain run {best_name})",
    }

    if best_metrics:
        result["history"] = {
            "runs": best_metrics.get("runs", 0),
            "success_rate": best_metrics.get("success_rate", 0),
            "last_completed": best_metrics.get("last_completed", ""),
        }

    # Show alternatives if close in score
    if len(ranked) > 1:
        alts = []
        for name, chain, score in ranked[1:3]:
            if score >= best_score * 0.5:
                alt = {"chain": name, "description": chain["description"], "score": round(score, 1)}
                m = metrics.get(name, {})
                if m:
                    alt["success_rate"] = m.get("success_rate", 0)
                alts.append(alt)
        if alts:
            result["alternatives"] = alts

    print(json.dumps(result))


def _skill_name_from_cmd(cmd):
    """Extract skill name from command string like '/cc-brainstorm'."""
    return cmd.lstrip("/").strip()


def cmd_chain_run(args):
    """Execute a skill chain — context-aware step-by-step instructions.

    Each step includes context loaded from the previous step's output.
    Chain state is persisted for resume via `cc-flow chain advance`.
    """
    name = args.name
    if name not in SKILL_CHAINS:
        error(f"Chain not found: {name}. Available: {', '.join(SKILL_CHAINS.keys())}")

    chain = SKILL_CHAINS[name]
    only_required = getattr(args, "required_only", False)

    steps = chain["skills"]
    if only_required:
        steps = [s for s in steps if s["required"]]

    # Load context from previous skills and save chain state
    try:
        from cc_flow.skill_flow import (
            load_skill_ctx, set_current, save_chain_state, record_chain_start,
        )
        # Save chain state for resume
        save_chain_state(name, steps, current_step=0)
        # Set first skill as current
        first_skill = _skill_name_from_cmd(steps[0]["skill"])
        set_current(first_skill, chain_name=name)
        # Record metrics
        record_chain_start(name)
    except ImportError:
        pass

    execute_steps = []
    for i, s in enumerate(steps):
        skill_name = _skill_name_from_cmd(s["skill"])
        step_info = {
            "step": i + 1,
            "skill": s["skill"],
            "role": s["role"],
            "required": s["required"],
            "instruction": f"Run: {s['skill']}",
        }

        # Load context from previous step
        if i > 0:
            prev_skill = _skill_name_from_cmd(steps[i - 1]["skill"])
            try:
                prev_ctx = load_skill_ctx(prev_skill)
                if prev_ctx:
                    step_info["prev_context"] = prev_ctx
            except (ImportError, Exception):
                pass

        # Add context-save reminder
        step_info["on_completion"] = (
            f"After completing this step, save context:\n"
            f"  cc-flow skill ctx save {skill_name} --data '{{...}}'\n"
            f"Then advance the chain:\n"
            f"  cc-flow chain advance"
        )

        execute_steps.append(step_info)

    print(json.dumps({
        "success": True,
        "chain": name,
        "description": chain["description"],
        "execute": execute_steps,
        "total_steps": len(steps),
        "instruction": (
            f"Execute this {name} chain step by step:\n"
            + "\n".join(
                f"  {i + 1}. {s['skill']} — {s['role']}"
                for i, s in enumerate(steps)
            )
            + "\n\nAfter each step: save context with `cc-flow skill ctx save <name> --data '{{...}}'`"
            + "\nThen advance: `cc-flow chain advance`"
        ),
    }))


def cmd_chain_advance(args):
    """Advance chain to the next step after current step completes.

    Optionally saves context data from the completed step.
    Returns the next step info or signals chain completion.
    """
    try:
        from cc_flow.skill_flow import (
            load_chain_state, advance_chain_state, set_current,
            save_skill_ctx, load_skill_ctx,
            record_chain_complete,
        )
    except ImportError:
        error("skill_flow module not available")

    state = load_chain_state()
    if not state:
        error("No active chain. Start one with: cc-flow chain run <name>")

    chain_name = state.get("chain", "")
    current_step = state.get("current_step", 0)
    step_skills = state.get("steps", [])

    # Save context from completed step if --data provided
    data_str = getattr(args, "data", "{}")
    saved_keys = []
    if data_str and data_str != "{}":
        try:
            data = json.loads(data_str)
            if current_step < len(step_skills):
                completed_skill = _skill_name_from_cmd(step_skills[current_step])
                save_skill_ctx(completed_skill, data)
                saved_keys = list(data.keys())
        except (json.JSONDecodeError, Exception):
            pass

    # Schema validation: check if saved context has expected output keys
    schema_warnings = []
    if chain_name in SKILL_CHAINS and current_step < len(SKILL_CHAINS[chain_name]["skills"]):
        step_def = SKILL_CHAINS[chain_name]["skills"][current_step]
        expected_outputs = step_def.get("outputs", [])
        if expected_outputs and saved_keys:
            missing = [k for k in expected_outputs if k not in saved_keys]
            if missing:
                schema_warnings.append(
                    f"Missing expected context keys: {', '.join(missing)} "
                    f"(expected: {', '.join(expected_outputs)})"
                )

    # Advance to next step
    new_state = advance_chain_state()
    if not new_state:
        error("No active chain state")

    if new_state.get("complete"):
        # Record metrics
        total = state.get("total_steps", 0)
        try:
            record_chain_complete(chain_name, total, total)
        except Exception:
            pass

        print(json.dumps({
            "success": True,
            "complete": True,
            "chain": chain_name,
            "message": f"Chain '{chain_name}' complete! All steps finished.",
            "auto_learn": f"cc-flow learn --task '{chain_name} chain' --outcome success --approach 'chain execution' --lesson 'completed {total} steps'",
        }))
        return

    # Get next step info from chain definition
    next_step_idx = new_state["current_step"]
    if chain_name in SKILL_CHAINS:
        chain = SKILL_CHAINS[chain_name]
        steps = chain["skills"]
        if next_step_idx < len(steps):
            next_step = steps[next_step_idx]
            next_skill = _skill_name_from_cmd(next_step["skill"])

            # Set as current skill
            set_current(next_skill, chain_name=chain_name)

            # Load context from previous step
            prev_ctx = None
            if next_step_idx > 0:
                prev_skill = _skill_name_from_cmd(steps[next_step_idx - 1]["skill"])
                prev_ctx = load_skill_ctx(prev_skill)

            # Check if next step's reads are satisfied
            reads_check = []
            next_reads = next_step.get("reads", [])
            if next_reads and prev_ctx:
                missing_reads = [k for k in next_reads if k not in prev_ctx]
                if missing_reads:
                    reads_check.append(
                        f"Next step expects: {', '.join(next_reads)}. "
                        f"Missing: {', '.join(missing_reads)}"
                    )

            result = {
                "success": True,
                "chain": chain_name,
                "step": next_step_idx + 1,
                "total_steps": len(steps),
                "skill": next_step["skill"],
                "role": next_step["role"],
                "required": next_step["required"],
                "instruction": f"NEXT -> Run: {next_step['skill']} — {next_step['role']}",
            }
            if prev_ctx:
                result["prev_context"] = prev_ctx
            if schema_warnings:
                result["schema_warnings"] = schema_warnings
            if reads_check:
                result["reads_warnings"] = reads_check

            print(json.dumps(result))
            return

    # Fallback: just show step number
    print(json.dumps({
        "success": True,
        "chain": chain_name,
        "step": next_step_idx + 1,
        "message": f"Advanced to step {next_step_idx + 1}",
    }))
