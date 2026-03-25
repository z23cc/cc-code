"""cc-flow go — one command, full automation.

Unified entry point: describe your goal → AI routes → execute.

Routing: AI router (gemini/claude) selects best chain + complexity.
Modes: chain (simple/medium), multi-engine/autopilot (complex), auto (scan/improve).
"""

import json
import os
import subprocess
import sys

from cc_flow.core import error

# ── Intent analysis (lightweight, for output metadata only) ──

INTENT_PATTERNS = {
    "BUILD": {"keywords": {"feature", "add", "create", "implement", "build", "new", "新增", "创建", "实现"},
              "supporting": ["/cc-requirement-gate", "/cc-architecture"]},
    "FIX": {"keywords": {"fix", "bug", "error", "crash", "broken", "fail", "修复", "报错", "崩溃"},
            "supporting": ["/cc-tdd"]},
    "IMPROVE": {"keywords": {"refactor", "optimize", "clean", "simplify", "performance", "speed", "重构", "优化"},
                "supporting": ["/cc-browser-qa", "/cc-elicit"]},
    "VERIFY": {"keywords": {"test", "review", "audit", "check", "qa", "验证", "测试", "审查"},
               "supporting": ["/cc-verification"]},
    "SHIP": {"keywords": {"deploy", "release", "ship", "push", "pr", "部署", "发布", "上线"},
             "supporting": ["/cc-review", "/cc-readiness-audit"]},
    "UNDERSTAND": {"keywords": {"research", "understand", "explain", "investigate", "how", "调研", "理解"},
                   "supporting": ["/cc-scout-repo"]},
    "PLAN": {"keywords": {"plan", "design", "architecture", "spec", "prd", "规划", "设计", "架构"},
             "supporting": ["/cc-elicit", "/cc-requirement-gate"]},
}

DOMAIN_DETECTORS = {
    "security": {"keywords": {"auth", "security", "password", "token", "jwt", "oauth", "secret", "安全", "认证"},
                 "auto_add": "/cc-security-review"},
    "database": {"keywords": {"database", "sql", "migration", "schema", "query", "table", "数据库", "查询"},
                 "auto_add": "/cc-database"},
    "api": {"keywords": {"api", "endpoint", "rest", "graphql", "route", "handler", "接口"},
            "auto_add": "/cc-fastapi"},
    "frontend": {"keywords": {"ui", "css", "frontend", "component", "responsive", "accessibility", "前端", "界面"},
                 "auto_add": "/cc-browser-qa"},
    "performance": {"keywords": {"slow", "performance", "latency", "speed", "optimize", "慢", "性能"},
                    "auto_add": "/cc-performance"},
}


def analyze_intent(query):
    """Lightweight intent classification for output metadata."""
    query_lower = query.lower()
    words = set(query_lower.split())

    intent = "BUILD"
    best_score = 0
    for intent_name, config in INTENT_PATTERNS.items():
        score = len(words & config["keywords"])
        if score > best_score:
            best_score = score
            intent = intent_name

    domains = []
    auto_skills = []
    for domain, config in DOMAIN_DETECTORS.items():
        if words & config["keywords"]:
            domains.append(domain)
            auto_skills.append(config["auto_add"])

    supporting = INTENT_PATTERNS.get(intent, {}).get("supporting", [])

    return {
        "intent": intent,
        "domains": domains,
        "supporting_skills": supporting,
        "auto_add_skills": auto_skills,
    }


# ── Skill to Agent mapping ──

_SKILL_AGENT_MAP = {
    # Scouts (read-only specialists)
    "cc-scout-repo": "cc-code:cc-scout-repo", "cc-scout-practices": "cc-code:cc-scout-practices",
    "cc-scout-gaps": "cc-code:cc-scout-gaps", "cc-scout-security": "cc-code:cc-scout-security",
    "cc-scout-testing": "cc-code:cc-scout-testing", "cc-scout-docs": "cc-code:cc-scout-docs",
    "cc-scout-docs-gap": "cc-code:cc-scout-docs-gap", "cc-scout-build": "cc-code:cc-scout-build",
    "cc-scout-env": "cc-code:cc-scout-env", "cc-scout-tooling": "cc-code:cc-scout-tooling",
    "cc-scout-observability": "cc-code:cc-scout-observability", "cc-scout-context": "cc-code:cc-scout-context",
    # Reviewers (lens-specific)
    "cc-review": "cc-code:code-reviewer",
    "cc-security-review": "cc-code:security-reviewer",
    "cc-code-review-loop": "cc-code:code-reviewer",
    # Specialists
    "cc-simplify": "cc-code:refactor-cleaner",
    "cc-debug": "cc-code:cc-debug", "cc-research": "cc-code:cc-research",
    "cc-brainstorm": "cc-code:cc-brainstorm", "cc-brainstorming": "cc-code:cc-brainstorm",
    "cc-plan": "cc-code:cc-plan", "cc-architecture": "cc-code:cc-architecture",
    "cc-requirement-gate": "cc-code:cc-requirement-gate",
    "cc-tdd": "cc-code:cc-tdd", "cc-performance": "cc-code:cc-perf",
    "cc-office-hours": "cc-code:cc-office-hours", "cc-grill-me": "cc-code:cc-grill-me",
    "cc-elicit": "cc-code:cc-elicit", "cc-prd-validate": "cc-code:cc-prd-validate",
    "cc-database": "cc-code:db-reviewer",
}

# Team patterns: skill combinations that should use team dispatch
TEAM_PATTERNS = {
    "review": {
        "detect": {"cc-review", "cc-security-review", "cc-code-review-loop"},
        "pattern": "parallel",  # All reviewers run simultaneously
        "agents": [
            {"type": "cc-code:code-reviewer", "role": "General code quality review", "filter": "all files"},
            {"type": "cc-code:python-reviewer", "role": "Python-specific patterns", "filter": ".py files"},
            {"type": "cc-code:security-reviewer", "role": "Security vulnerability scan", "filter": "auth/input/API files"},
        ],
        "consolidate": "Worst verdict wins. CRITICAL/HIGH from any reviewer = block.",
    },
    "research": {
        "detect": {"cc-research", "cc-scout-repo", "cc-scout-practices", "cc-scout-gaps"},
        "pattern": "parallel",  # All scouts run simultaneously
        "agents": [
            {"type": "cc-code:cc-scout-repo", "role": "Find existing patterns & conventions"},
            {"type": "cc-code:cc-scout-practices", "role": "Current best practices & pitfalls"},
            {"type": "cc-code:cc-scout-gaps", "role": "Edge cases & missing requirements"},
        ],
        "consolidate": "Merge findings, deduplicate, prioritize by relevance.",
    },
    "design": {
        "detect": {"cc-brainstorm", "cc-brainstorming", "cc-plan", "cc-architecture", "cc-requirement-gate"},
        "pattern": "parallel",
        "agents": [
            {"type": "cc-code:cc-scout-repo", "role": "Find existing patterns & conventions"},
            {"type": "cc-code:cc-scout-practices", "role": "Best practices for this design"},
            {"type": "cc-code:cc-scout-gaps", "role": "Edge cases & missing requirements"},
        ],
        "consolidate": "Merge scout findings, then use as input for plan/architecture.",
    },
}


def _skill_to_agent(skill_name):
    """Map a skill name to the best agent subagent_type."""
    return _SKILL_AGENT_MAP.get(skill_name, "general-purpose")


def _detect_team_for_phase(phase_steps):
    """Check if a group of steps matches a team pattern. Returns team name or None."""
    skill_names = {s["skill"].lstrip("/").strip() for s in phase_steps}
    for team_name, pattern in TEAM_PATTERNS.items():
        if skill_names & pattern["detect"]:
            return team_name
    return None


# ── Phase-based parallel execution ──

def _group_into_phases(steps):
    """Group chain steps into execution phases.

    Same-phase consecutive steps run in PARALLEL (via Agent tool) ONLY IF:
    1. They share the same phase type (observe/design/verify)
    2. The later step does NOT have `reads` that reference the earlier step's `outputs`
    """
    if not steps:
        return []

    phases = []
    current = {"phase": steps[0].get("phase", "mutate"), "steps": [steps[0]]}

    for s in steps[1:]:
        phase = s.get("phase", "mutate")
        reads = set(s.get("reads", []))
        has_dependency = False
        if reads:
            for prev in current["steps"]:
                if reads & set(prev.get("outputs", [])):
                    has_dependency = True
                    break

        if phase == current["phase"] and phase in ("observe", "design", "verify") and not has_dependency:
            current["steps"].append(s)
        else:
            phases.append(current)
            current = {"phase": phase, "steps": [s]}

    phases.append(current)

    for p in phases:
        p["parallel"] = len(p["steps"]) > 1 and p["phase"] in ("observe", "design", "verify")

    return phases


def _build_auto_exec_instruction(chain_name, chain_data, query, steps):
    """Build phase-based execution instruction with parallel dispatch."""
    phases = _group_into_phases(steps)
    total_phases = len(phases)
    total_steps = len(steps)
    parallel_count = sum(len(p["steps"]) for p in phases if p["parallel"])
    is_parallel = parallel_count > 0

    lines = [
        f"# AUTO-EXECUTE: {chain_name} chain",
        f"Goal: {query}",
        "",
    ]

    # Determine if worktree isolation is needed
    has_mutate = any(p["phase"] == "mutate" for p in phases)
    use_worktree = has_mutate and total_steps >= 3  # Only for non-trivial chains

    if use_worktree:
        wt_name = f"cc-{chain_name}-{query.split()[0][:10]}".lower().replace(" ", "-")
        lines.append("## Worktree Isolation")
        lines.append("This chain modifies code. Create an isolated worktree first:")
        lines.append("```bash")
        lines.append(f"cc-flow worktree create {wt_name}")
        lines.append(f"cd $(git rev-parse --show-toplevel)/.claude/worktrees/{wt_name}")
        lines.append("```")
        lines.append("All code changes happen in the worktree. Merge back when done:")
        lines.append("```bash")
        lines.append(f"git checkout main && git merge {wt_name}")
        lines.append(f"cc-flow worktree remove {wt_name}")
        lines.append("```")
        lines.append("")

    if is_parallel:
        lines.append(f"This chain has {total_steps} steps organized into {total_phases} phases.")
        lines.append(f"⚡ {parallel_count} steps run in PARALLEL (same phase, no code conflicts).")
        lines.append("IMPORTANT: For parallel phases, launch ALL agents in ONE message using multiple Agent tool calls.")
        lines.append("")
    else:
        lines.append("Execute these steps IN ORDER. Do NOT stop between steps.")
        lines.append("")

    step_num = 0
    for pi, phase in enumerate(phases):
        phase_label = phase["phase"].upper()

        if phase["parallel"]:
            n_agents = len(phase["steps"])
            team = _detect_team_for_phase(phase["steps"])

            if team and team in TEAM_PATTERNS:
                # Team dispatch — use predefined team agents
                tp = TEAM_PATTERNS[team]
                team_agents = tp.get("agents", [])
                lines.append(f"## Phase {pi+1}/{total_phases}: TEAM [{team.upper()}] — {len(team_agents)} specialist agents")
                lines.append("")
                lines.append(f"**DISPATCH TEAM in ONE message** ({tp.get('pattern', 'parallel')}):")
                lines.append("")
                for i, agent in enumerate(team_agents, 1):
                    step_num += 1
                    lines.append(f"Agent {step_num}: {agent['role']}")
                    lines.append(f"  subagent_type: \"{agent['type']}\"")
                    lines.append(f"  prompt: \"{agent['role']} for: {query}\"")
                    lines.append("  run_in_background: true")
                    if agent.get("filter"):
                        lines.append(f"  focus: {agent['filter']}")
                    lines.append("")
                if tp.get("consolidate"):
                    lines.append(f"**Consolidate**: {tp['consolidate']}")
                lines.append("Then advance: `cc-flow chain advance`")
                lines.append("")
            else:
                # Generic parallel dispatch
                lines.append(f"## Phase {pi+1}/{total_phases}: PARALLEL [{phase_label}] — {n_agents} agents simultaneously")
                lines.append("")
                lines.append(f"**DISPATCH ALL {n_agents} AGENTS IN ONE MESSAGE:**")
                lines.append("")
                for s in phase["steps"]:
                    step_num += 1
                    skill_name = s["skill"].lstrip("/").strip()
                    agent_type = _skill_to_agent(skill_name)
                    lines.append(f"Agent {step_num}: {s['skill']} — {s['role']}")
                    lines.append(f"  subagent_type: \"{agent_type}\"")
                    lines.append(f"  prompt: \"Activate {skill_name} skill for: {query}\"")
                    lines.append("  run_in_background: true")
                    lines.append("")
                lines.append(f"Wait for ALL {n_agents} agents, then advance:")
                lines.append("`cc-flow chain advance`")
                lines.append("")
        else:
            for s in phase["steps"]:
                step_num += 1
                skill_name = s["skill"].lstrip("/").strip()
                required_tag = "REQUIRED" if s["required"] else "OPTIONAL"
                outputs = s.get("outputs", [])
                reads = s.get("reads", [])

                # Check if this single step should use team dispatch
                team = _detect_team_for_phase([s])
                if team and team in TEAM_PATTERNS:
                    tp = TEAM_PATTERNS[team]
                    team_agents = tp.get("agents", [])
                    lines.append(f"## Phase {pi+1}/{total_phases}: TEAM [{team.upper()}] via {s['skill']} [{required_tag}]")
                    lines.append(f"Instead of single {skill_name}, dispatch {len(team_agents)} specialist agents:")
                    lines.append("")
                    for agent in team_agents:
                        lines.append(f"  - {agent['type']}: {agent['role']}")
                    lines.append("")
                    lines.append("**DISPATCH ALL in ONE message** (parallel, run_in_background: true)")
                    if tp.get("consolidate"):
                        lines.append(f"**Consolidate**: {tp['consolidate']}")
                    lines.append("Then advance: `cc-flow chain advance`")
                    lines.append("")
                    continue

                lines.append(f"## Phase {pi+1}/{total_phases}: {s['skill']} [{required_tag}] [{phase_label}]")
                lines.append(f"Role: {s['role']}")

                if reads:
                    lines.append(f"Reads from previous: {', '.join(reads)}")

                lines.append(f"Action: Activate the {skill_name} skill and execute it for: {query}")

                if outputs:
                    ctx_json = ", ".join(f'"{k}": "..."' for k in outputs)
                    lines.append(f"On completion, save: `cc-flow skill ctx save {skill_name} --data '{{{ctx_json}}}'`")
                else:
                    lines.append(f"On completion: `cc-flow skill ctx save {skill_name} --data '{{\"done\": true}}'`")

                lines.append("Then advance: `cc-flow chain advance`")
                lines.append("")

    lines.append("## On Chain Complete")
    lines.append(f"All {total_steps} steps done ({total_phases} phases).")
    if use_worktree:
        lines.append("**Merge worktree back to main:**")
        lines.append("```bash")
        lines.append(f"git checkout main && git merge {wt_name} && cc-flow worktree remove {wt_name}")
        lines.append("```")
    lines.append(f"Record learning: `cc-flow learn --task '{chain_name}: {query}' --outcome success`")

    return "\n".join(lines)


# ── Resume logic ──

def _check_resume():
    """Check if there's an interrupted chain to resume."""
    try:
        from cc_flow.skill_flow import CHAIN_STATE_FILE, load_chain_state
        if not CHAIN_STATE_FILE.exists():
            return None
        state = load_chain_state()
        if state and not state.get("complete"):
            return state
    except ImportError:
        pass
    return None


def _execute_resume(state):
    """Resume an interrupted chain."""
    chain_name = state.get("chain", "")
    current_step = state.get("current_step", 0)
    total_steps = state.get("total_steps", 0)

    from cc_flow.skill_chains import SKILL_CHAINS
    chain_data = SKILL_CHAINS.get(chain_name)

    if not chain_data:
        error(f"Cannot resume: chain '{chain_name}' not found")

    remaining = chain_data["skills"][current_step:]
    instruction = _build_auto_exec_instruction(chain_name, chain_data, f"resume {chain_name}", remaining)

    prev_ctx = None
    if current_step > 0:
        try:
            from cc_flow.skill_flow import load_skill_ctx
            prev_skill = chain_data["skills"][current_step - 1]["skill"].lstrip("/").strip()
            prev_ctx = load_skill_ctx(prev_skill)
        except (ImportError, Exception):
            pass

    result = {
        "success": True,
        "mode": "chain",
        "resumed": True,
        "chain": chain_name,
        "resumed_from_step": current_step + 1,
        "total_steps": total_steps,
        "remaining_steps": len(remaining),
        "instruction": instruction,
    }

    if prev_ctx:
        result["prev_context"] = prev_ctx

    print(json.dumps(result))


# ── Executors ──

def _execute_chain(chain_name, chain_data, query, dry_run=False, complexity="medium", intent=None):
    """Execute a skill chain with full auto-execution protocol."""
    steps = chain_data["skills"]

    try:
        from cc_flow.skill_flow import (
            load_skill_ctx,
            record_chain_start,
            save_chain_state,
            set_current,
        )
    except ImportError:
        save_chain_state = set_current = load_skill_ctx = record_chain_start = None

    if not dry_run and save_chain_state:
        save_chain_state(chain_name, steps)
        first_skill = steps[0]["skill"].lstrip("/").strip()
        set_current(first_skill, chain_name=chain_name)
        if record_chain_start:
            record_chain_start(chain_name)

    # Auto-ops: create worktree if chain modifies code
    worktree_name = None
    worktree_path = None
    if not dry_run:
        phases = _group_into_phases(steps)
        has_mutate = any(p["phase"] == "mutate" for p in phases)
        if has_mutate and len(steps) >= 3:
            try:
                from cc_flow.auto_ops import auto_worktree_create
                worktree_name = f"cc-{chain_name}-{query.split()[0][:10]}".lower().replace(" ", "-")
                worktree_path = auto_worktree_create(worktree_name)
            except (ImportError, Exception):
                pass

    execute_steps = []
    for i, s in enumerate(steps):
        step_info = {
            "step": i + 1,
            "skill": s["skill"],
            "role": s["role"],
            "required": s["required"],
        }
        if "outputs" in s:
            step_info["outputs"] = s["outputs"]
        if "reads" in s:
            step_info["reads"] = s["reads"]
        if i > 0 and load_skill_ctx:
            prev_skill = steps[i - 1]["skill"].lstrip("/").strip()
            prev_ctx = load_skill_ctx(prev_skill)
            if prev_ctx:
                step_info["prev_context"] = prev_ctx

        execute_steps.append(step_info)

    instruction = _build_auto_exec_instruction(chain_name, chain_data, query, steps)
    phases = _group_into_phases(steps)
    parallel_count = sum(len(p["steps"]) for p in phases if p["parallel"])

    result = {
        "success": True,
        "mode": "chain",
        "complexity": complexity,
        "chain": chain_name,
        "description": chain_data.get("description", ""),
        "goal": query,
        "dry_run": dry_run,
        "steps": execute_steps,
        "total_steps": len(steps),
        "required_steps": sum(1 for s in steps if s["required"]),
        "phases": len(phases),
        "parallel_steps": parallel_count,
        "instruction": instruction,
    }

    if intent:
        result["intent"] = intent.get("intent", "")
        if intent.get("domains"):
            result["domains_detected"] = intent["domains"]
        if intent.get("auto_add_skills"):
            result["recommended_additions"] = intent["auto_add_skills"]
        if intent.get("supporting_skills"):
            result["supporting_skills"] = intent["supporting_skills"]
        if intent.get("ai_routed"):
            result["ai_routed"] = True
            result["ai_engine"] = intent.get("ai_engine", "")
            if intent.get("ai_reason"):
                result["ai_reason"] = intent["ai_reason"]

    # Auto-ops info
    if worktree_path:
        result["worktree"] = {"name": worktree_name, "path": worktree_path}
        result["instruction"] = (
            f"## Worktree Created: {worktree_name}\n"
            f"Path: {worktree_path}\n"
            f"cd {worktree_path}\n\n"
            + result.get("instruction", "")
            + f"\n\n## On Complete: merge + cleanup\n"
            f"git checkout main && git merge {worktree_name}\n"
            f"cc-flow worktree remove {worktree_name}\n"
        )

    # Auto-learn
    if not dry_run:
        try:
            from cc_flow.auto_learn import on_chain_complete
            on_chain_complete(chain_name, query, 0, len(steps), "started")
        except (ImportError, Exception):
            pass

    print(json.dumps(result))


def _execute_ralph(query, max_iterations=25, dry_run=False):
    """Execute Ralph autonomous loop."""
    if dry_run:
        print(json.dumps({
            "success": True,
            "mode": "ralph",
            "goal": query,
            "max_iterations": max_iterations,
            "dry_run": True,
            "instruction": (
                f"Ralph will autonomously execute: {query}\n"
                f"  - Creates epic + tasks from goal\n"
                f"  - Fresh Claude session per iteration\n"
                f"  - Self-healing on failures\n"
                f"  - Max {max_iterations} iterations\n"
                f"  - Receipt-based proof-of-work"
            ),
        }))
        return

    try:
        from cc_flow.ralph_cmd import _find_ralph_sh, _init_ralph
    except ImportError:
        error("Ralph module not available")

    ralph_dir = _init_ralph(query)
    ralph_sh = ralph_dir / "ralph.sh"

    if not ralph_sh.is_file():
        sh = _find_ralph_sh()
        if not sh:
            error("Ralph not found. Install: cc-flow ralph --init")
        ralph_sh = sh

    env = os.environ.copy()
    env["GOAL"] = query
    env["SELF_HEAL"] = "1"
    env["GOAL_VERIFY"] = "tests"
    env["MAX_ITERATIONS"] = str(max_iterations)
    env["YOLO"] = "1"

    print(json.dumps({
        "starting": True,
        "mode": "ralph",
        "goal": query,
        "max_iterations": max_iterations,
        "instruction": (
            f"Launching Ralph autonomous execution for: {query}\n"
            f"Ralph will create tasks and execute until goal achieved or {max_iterations} iterations."
        ),
    }))

    try:
        result = subprocess.run(["bash", str(ralph_sh)], check=False, env=env, cwd=os.getcwd())
        sys.exit(result.returncode)
    except KeyboardInterrupt:
        print("\nRalph interrupted.")
        sys.exit(130)


def _execute_auto(query, dry_run=False):
    """Run OODA auto-improvement loop."""
    if dry_run:
        print(json.dumps({
            "success": True,
            "mode": "auto",
            "goal": query,
            "dry_run": True,
            "instruction": (
                f"Auto-improvement loop for: {query}\n"
                f"  Phase 1: OBSERVE — scan for lint, type, test issues\n"
                f"  Phase 2: DECIDE — pick next task, recommend team\n"
                f"  Phase 3: ACT — auto-fix lint, run tests\n"
                f"  Loop until clean"
            ),
        }))
        return

    cmd = [sys.executable, "-m", "cc_flow", "auto", "full"]
    print(json.dumps({
        "starting": True,
        "mode": "auto",
        "goal": query,
        "instruction": "Running: cc-flow auto full (scan → fix → test)",
    }))

    try:
        result = subprocess.run(cmd, check=False, cwd=os.getcwd())
        sys.exit(result.returncode)
    except KeyboardInterrupt:
        print("\nAuto interrupted.")
        sys.exit(130)


# ── Main command ──

def cmd_go(args):
    """One command, full automation: describe your goal, everything runs."""
    query = " ".join(args.goal) if args.goal else ""
    force_mode = getattr(args, "mode", "") or ""
    max_iter = getattr(args, "max", 25)
    dry_run = getattr(args, "dry_run", False)
    resume = getattr(args, "resume", False)
    auto_exec = not getattr(args, "no_auto_exec", False)

    # Resume mode
    if resume:
        state = _check_resume()
        if state:
            _execute_resume(state)
            return
        print(json.dumps({"success": False, "error": "No interrupted chain to resume."}))
        return

    if not query:
        state = _check_resume()
        if state:
            chain = state.get("chain", "?")
            step = state.get("current_step", 0) + 1
            total = state.get("total_steps", 0)
            print(json.dumps({
                "success": False,
                "error": f"No goal specified. (Interrupted chain '{chain}' at step {step}/{total} — use --resume to continue)",
            }))
            return
        error("Describe your goal: cc-flow go \"what you want to achieve\"")

    # Route via AI or forced mode
    from cc_flow.ai_router import ai_route
    from cc_flow.skill_chains import SKILL_CHAINS

    if force_mode:
        # Forced mode — direct dispatch
        intent_analysis = analyze_intent(query)
        mode = force_mode
        chain_name, chain_data = None, None
        complexity = "medium"
        if force_mode == "chain":
            # Find best chain via keyword for forced chain mode
            from cc_flow.skill_chains import find_chain
            chain_name, chain_data = find_chain(query)
    else:
        # AI router — single routing path
        ai_result = ai_route(query)
        ai_chain = ai_result["chain"] if ai_result else None

        # Standalone command routing
        STANDALONE_COMMANDS = {"review", "prime", "audit", "interview", "scout",
                               "research", "retro", "verify", "dashboard", "doctor", "health",
                               "deep-search", "smart-chat", "recall-review", "embed-structure", "bridge-status",
                               "pua"}

        if ai_chain == "autopilot":
            mode = "multi-engine"
            chain_name, chain_data = None, None
            complexity = "complex"
        elif ai_chain == "auto":
            mode = "auto"
            chain_name, chain_data = None, None
            complexity = ai_result.get("complexity", "medium")
        elif ai_chain in STANDALONE_COMMANDS:
            mode = "command"
            chain_name = ai_chain
            chain_data = None
            complexity = ai_result.get("complexity", "simple")
        elif ai_chain and ai_chain in SKILL_CHAINS:
            chain_name = ai_chain
            chain_data = SKILL_CHAINS[ai_chain]
            complexity = ai_result.get("complexity", "medium")
            if complexity == "simple":
                light_name = f"{ai_chain}-light"
                if light_name in SKILL_CHAINS:
                    chain_name = light_name
                    chain_data = SKILL_CHAINS[light_name]
            mode = "chain"
        else:
            mode = "multi-engine"
            chain_name, chain_data = None, None
            complexity = "complex"

        intent_analysis = analyze_intent(query)
        if ai_result:
            intent_analysis["ai_routed"] = True
            intent_analysis["ai_engine"] = ai_result.get("router_engine", "")
            intent_analysis["ai_reason"] = ai_result.get("reason", "")
            intent_analysis["from_cache"] = ai_result.get("from_cache", False)

    # Execute
    if auto_exec and mode == "chain" and chain_data and not dry_run:
        # Full auto: every skill step runs as subprocess (claude -p)
        from cc_flow.skill_executor import execute_chain_auto
        result = execute_chain_auto(chain_name, chain_data, query)
        print(json.dumps(result))
        return

    if mode == "command":
        # Standalone command — dispatch directly
        cmd_map = {
            "review": "cc-flow review",
            "prime": "cc-flow scan --create",
            "audit": "cc-flow scan --create",
            "verify": "cc-flow verify",
            "dashboard": "cc-flow dashboard",
            "doctor": "cc-flow doctor",
            "health": "cc-flow health",
            "retro": "/cc-retro",
            "interview": "/cc-interview",
            "research": "/cc-research",
            "scout": "/cc-scout",
            # Bridge (Morph × RP × Supermemory)
            "deep-search": f"cc-flow deep-search \"{query}\"",
            "smart-chat": f"cc-flow smart-chat \"{query}\"",
            "recall-review": f"cc-flow recall-review \"{query}\"",
            "embed-structure": "cc-flow embed-structure",
            "bridge-status": "cc-flow bridge-status",
            "pua": "cc-flow pua",
        }
        target = cmd_map.get(chain_name, f"/cc-{chain_name}")
        reason = intent_analysis.get("ai_reason", "")
        print(json.dumps({
            "success": True,
            "mode": "command",
            "command": target,
            "goal": query,
            "dry_run": dry_run,
            "ai_routed": True,
            "ai_reason": reason,
            "instruction": f"Run: {target}\nReason: {reason}",
        }))
    elif mode == "chain" and chain_data:
        _execute_chain(chain_name, chain_data, query, dry_run, complexity=complexity,
                       intent=intent_analysis)
    elif mode == "multi-engine":
        from cc_flow.autopilot import run_autopilot
        result = run_autopilot(query, timeout=300, dry_run=dry_run)
        print(json.dumps(result))
    elif mode == "auto":
        _execute_auto(query, dry_run)
    elif mode == "ralph":
        # Legacy: explicit --mode=ralph still works
        _execute_ralph(query, max_iter, dry_run)
    else:
        # Default fallback: autopilot (3-engine guided)
        from cc_flow.autopilot import run_autopilot
        result = run_autopilot(query, timeout=300, dry_run=dry_run)
        print(json.dumps(result))
