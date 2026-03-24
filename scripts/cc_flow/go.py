"""cc-flow go — one command, full automation.

Unified entry point: describe your goal → system routes, decides mode, executes.

Modes:
  chain  — lightweight skill sequence (≤ 4 required steps), auto-executed
  ralph  — autonomous goal-driven execution (complex goals, creates tasks)
  auto   — OODA improvement loop (scan → fix → test)
"""

import json
import os
import subprocess
import sys

from cc_flow.core import error

# ── Routing ──

def _route(query):
    """Route a query to the best command. Returns route result dict."""
    try:
        from cc_flow.route_learn import ROUTE_TABLE
        query_lower = query.lower()
        words = set(query_lower.split())

        best = None
        best_score = 0
        for keywords, cmd, team, desc in ROUTE_TABLE:
            score = 0
            for kw in keywords:
                if kw in query_lower:
                    score += 2
                elif any(w in words for w in kw.split()):
                    score += 1
            if score > best_score:
                best_score = score
                best = {"command": cmd, "team": team, "description": desc, "score": score}

        return best or {"command": None, "team": None, "description": "No route match", "score": 0}
    except ImportError:
        return {"command": None, "score": 0}


def _find_chain(query, complexity=None):
    """Find the best matching skill chain. Scale-adaptive: prefers -light for simple tasks."""
    try:
        from cc_flow.skill_chains import find_chain
        name, data = find_chain(query, complexity=complexity)
        return name, data
    except ImportError:
        return None, None


# ── Mode decision ──

AUTO_KEYWORDS = {"improve", "autoimmune", "auto", "scan", "lint", "quality",
                 "改进", "自动", "扫描", "质量"}

HOTFIX_KEYWORDS = {"hotfix", "typo", "trivial", "one-liner", "urgent", "revert",
                   "quick fix", "config change", "bump version", "emergency",
                   "紧急", "快速修复", "小改动", "回滚"}


# ── Intent analysis ──

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
    """AI-assisted intent analysis: classify query and suggest supporting skills."""
    query_lower = query.lower()
    words = set(query_lower.split())

    # Classify primary intent
    intent = "BUILD"  # default
    best_score = 0
    for intent_name, config in INTENT_PATTERNS.items():
        score = len(words & config["keywords"])
        if score > best_score:
            best_score = score
            intent = intent_name

    # Detect domains touched
    domains = []
    auto_skills = []
    for domain, config in DOMAIN_DETECTORS.items():
        if words & config["keywords"]:
            domains.append(domain)
            auto_skills.append(config["auto_add"])

    # Get supporting skills for the intent
    supporting = INTENT_PATTERNS.get(intent, {}).get("supporting", [])

    return {
        "intent": intent,
        "domains": domains,
        "supporting_skills": supporting,
        "auto_add_skills": auto_skills,
    }


# ── Scale-Adaptive Planning (blast radius based) ──

# Zero blast radius → one-shot (light chain or hotfix)
ZERO_BLAST_SIGNALS = {
    "typo", "rename", "comment", "config", "bump", "revert", "format",
    "readme", "changelog", "docs", "lint", "import", "spelling",
    "拼写", "改名", "格式化", "文档", "配置",
} | HOTFIX_KEYWORDS

# High blast radius → full planning depth
HIGH_BLAST_SIGNALS = {
    "architecture", "system", "platform", "redesign", "rewrite",
    "multi-service", "microservice", "monorepo", "migrate", "auth",
    "payment", "database schema", "breaking change", "public api",
    "security", "permissions", "rbac", "multi-tenant", "database", "schema",
    "production", "deploy", "infra", "kubernetes", "k8s",
    "架构", "系统", "平台", "重写", "微服务", "迁移", "权限", "支付", "数据库", "生产",
}

# Multi-goal separators
_GOAL_SEPARATORS = {"and", "then", "also", "plus", "另外", "然后", "还要", "以及", "同时"}


def _count_goals(query):
    """Count distinct goals in a query. >1 suggests multi-goal complexity."""
    words = query.lower().split()
    separators = sum(1 for w in words if w in _GOAL_SEPARATORS)
    return 1 + separators


def _estimate_complexity(query, chain_data):
    """Estimate task complexity using blast-radius scoring.

    Blast radius = "could this change cause unintended consequences elsewhere?"

    Levels:
      simple  — zero blast radius, single file/config change, no dependencies
      medium  — contained blast radius, single component, clear boundaries
      complex — cross-system blast radius, multiple components, breaking changes

    Scoring: blast_score 0-10
      0-2: simple, 3-6: medium, 7+: complex
    """
    words = set(query.lower().split())
    word_count = len(words)
    blast_score = 0

    # Signal 1: Zero-blast keywords → clamp to simple
    if words & ZERO_BLAST_SIGNALS:
        return "simple"

    # Signal 2: High-blast keywords → +3 per match (substring check for multi-word)
    high_matches = 0
    query_lower = query.lower()
    for signal in HIGH_BLAST_SIGNALS:
        if signal in query_lower:
            high_matches += 1
    blast_score += high_matches * 3

    # Signal 3: Multi-goal → +2 per extra goal
    goals = _count_goals(query)
    if goals > 1:
        blast_score += (goals - 1) * 2

    # Signal 4: File/path mentions → +1 (touches specific code)
    if any(c in query for c in ["/", ".", "src", "lib", "app"]):
        blast_score += 1

    # Signal 5: Long query → +1 (more context = more scope)
    if word_count > 10:
        blast_score += 2
    elif word_count > 6:
        blast_score += 1

    # Signal 6: Chain step count (if matched)
    if chain_data:
        required = sum(1 for s in chain_data.get("skills", []) if s.get("required"))
        if required <= 2:
            blast_score = max(0, blast_score - 2)  # Small chain = lower blast
        elif required >= 5:
            blast_score += 1  # Many steps = higher blast

    # Map score to complexity
    if blast_score <= 2:
        return "simple"
    if blast_score <= 5:
        return "medium"
    return "complex"


def decide_mode(query, route_result, chain_name, chain_data, force_mode=""):
    """Decide execution mode based on complexity-adaptive routing.

    Simple  → light chain (2-3 steps, skip brainstorm/plan)
    Medium  → standard chain (matched chain, ≤5 steps)
    Complex → multi-engine chain (multi-plan → work → review → commit)
    Very complex (no chain match) → Ralph (autonomous)
    Auto    → OODA loop (scan/improve keywords)
    """
    if force_mode:
        return force_mode

    query_lower = query.lower()
    words = set(query_lower.split())

    # 1. Auto mode for improvement/scan keywords
    route_cmd = (route_result or {}).get("command", "") or ""
    if route_cmd in ("/autoimmune", "auto") or words & AUTO_KEYWORDS:
        return "auto"

    # 2. Estimate complexity
    complexity = _estimate_complexity(query, chain_data)

    # 3. Route by complexity
    if complexity == "simple":
        return "chain"

    if complexity == "medium" and chain_data:
        required = sum(1 for s in chain_data.get("skills", []) if s.get("required"))
        if required <= 5:
            return "chain"

    if complexity == "complex":
        if chain_data:
            required = sum(1 for s in chain_data.get("skills", []) if s.get("required"))
            if required <= 5:
                return "chain"
        # Complex without matching chain → use multi-engine chain
        return "multi-engine"

    # Fallback: chain if available, multi-engine otherwise
    if chain_data:
        return "chain"
    return "multi-engine"


# ── Phase-based parallel execution ──

def _group_into_phases(steps):
    """Group chain steps into execution phases.

    Same-phase consecutive steps run in PARALLEL (via Agent tool) ONLY IF:
    1. They share the same phase type (observe/design/verify)
    2. The later step does NOT have `reads` that reference the earlier step's `outputs`

    Phase types:
      observe — read-only analysis (parallel safe)
      design  — produce specs, no code changes (parallel safe)
      verify  — check code state (parallel safe)
      mutate  — change code (sequential)
      gate    — commit/ship (sequential, always last)

    Returns: list of phases, each phase = {"phase": str, "parallel": bool, "steps": [...]}
    """
    if not steps:
        return []

    phases = []
    current = {"phase": steps[0].get("phase", "mutate"), "steps": [steps[0]]}

    for s in steps[1:]:
        phase = s.get("phase", "mutate")
        reads = set(s.get("reads", []))
        # Check if this step reads from any output in the current group
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

    # Mark parallel phases
    for p in phases:
        p["parallel"] = len(p["steps"]) > 1 and p["phase"] in ("observe", "design", "verify")

    return phases


def _build_auto_exec_instruction(chain_name, chain_data, query, steps):
    """Build phase-based execution instruction with parallel dispatch.

    Key optimization: consecutive observe/design/verify steps are grouped
    into parallel phases. Claude dispatches them as multiple Agent tool
    calls in a single message, then waits for all to complete before
    proceeding to the next phase.
    """
    phases = _group_into_phases(steps)
    total_phases = len(phases)
    total_steps = len(steps)

    # Count parallelizable steps
    parallel_count = sum(len(p["steps"]) for p in phases if p["parallel"])
    is_parallel = parallel_count > 0

    lines = [
        f"# AUTO-EXECUTE: {chain_name} chain",
        f"Goal: {query}",
        "",
    ]

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
            # Parallel phase
            lines.append(f"## Phase {pi+1}/{total_phases}: PARALLEL [{phase_label}] — {len(phase['steps'])} agents simultaneously")
            lines.append("")
            lines.append("**Launch ALL of these in a single message (multiple Agent tool calls):**")
            lines.append("")
            for s in phase["steps"]:
                step_num += 1
                skill_name = s["skill"].lstrip("/").strip()
                required_tag = "REQUIRED" if s["required"] else "OPTIONAL"
                lines.append(f"- **{s['skill']}** [{required_tag}]: {s['role']}")
            lines.append("")
            lines.append("Wait for ALL parallel agents to complete, then save each context:")
            for s in phase["steps"]:
                skill_name = s["skill"].lstrip("/").strip()
                outputs = s.get("outputs", [])
                if outputs:
                    ctx_json = ", ".join(f'"{k}": "..."' for k in outputs)
                    lines.append(f"  `cc-flow skill ctx save {skill_name} --data '{{{ctx_json}}}'`")
                else:
                    lines.append(f"  `cc-flow skill ctx save {skill_name} --data '{{\"done\": true}}'`")
            lines.append("Then advance: `cc-flow chain advance`")
            lines.append("")
        else:
            # Sequential step(s)
            for s in phase["steps"]:
                step_num += 1
                skill_name = s["skill"].lstrip("/").strip()
                required_tag = "REQUIRED" if s["required"] else "OPTIONAL"
                outputs = s.get("outputs", [])
                reads = s.get("reads", [])

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
    lines.append(f"All {total_steps} steps done ({total_phases} phases). The chain will auto-report completion.")
    lines.append(f"Record learning: `cc-flow learn --task '{chain_name}: {query}' --outcome success`")

    return "\n".join(lines)


# ── Resume logic ──

def _check_resume():
    """Check if there's an interrupted chain to resume. Returns state or None."""
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
    """Resume an interrupted chain from the current step."""
    from cc_flow.skill_chains import SKILL_CHAINS
    from cc_flow.skill_flow import load_skill_ctx, set_current

    chain_name = state.get("chain", "")
    current_step = state.get("current_step", 0)
    total_steps = state.get("total_steps", 0)
    state.get("steps", [])

    chain_data = SKILL_CHAINS.get(chain_name)
    if not chain_data:
        print(json.dumps({
            "success": False,
            "error": f"Chain '{chain_name}' not found. Clear with: cc-flow skill ctx clear",
        }))
        return

    steps = chain_data["skills"]
    remaining = steps[current_step:]

    # Set current skill
    if remaining:
        skill_name = remaining[0]["skill"].lstrip("/").strip()
        set_current(skill_name, chain_name=chain_name)

    # Load previous step context if available
    prev_ctx = None
    if current_step > 0:
        prev_skill = steps[current_step - 1]["skill"].lstrip("/").strip()
        prev_ctx = load_skill_ctx(prev_skill)

    instruction = _build_auto_exec_instruction(
        chain_name, chain_data, f"(resumed from step {current_step + 1})", remaining,
    )

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

    # Set up chain state via skill_flow
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

    # Build step list with context
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

        # Load prev context
        if i > 0 and load_skill_ctx:
            prev_skill = steps[i - 1]["skill"].lstrip("/").strip()
            prev_ctx = load_skill_ctx(prev_skill)
            if prev_ctx:
                step_info["prev_context"] = prev_ctx

        execute_steps.append(step_info)

    # Build auto-execution instruction
    instruction = _build_auto_exec_instruction(chain_name, chain_data, query, steps)

    # Phase analysis for parallel execution
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

    # Add AI intent analysis
    if intent:
        result["intent"] = intent.get("intent", "")
        if intent.get("domains"):
            result["domains_detected"] = intent["domains"]
        if intent.get("auto_add_skills"):
            result["recommended_additions"] = intent["auto_add_skills"]
        if intent.get("supporting_skills"):
            result["supporting_skills"] = intent["supporting_skills"]

    print(json.dumps(result))


def _execute_ralph(query, max_iterations=25, dry_run=False):
    """Launch Ralph in goal-driven autonomous mode."""
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

    # Delegate to ralph_cmd
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
            f"Ralph will create tasks and execute until goal achieved or {max_iterations} iterations.\n"
            f"Monitor: tail -f scripts/ralph/runs/latest/progress.log\n"
            f"Pause: touch scripts/ralph/PAUSE\n"
            f"Stop: touch scripts/ralph/STOP"
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

    # Delegate to auto full
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
        sys.exit(130)


# ── Main command ──

def cmd_go(args):
    """One command, full automation: describe your goal, everything runs."""
    query = " ".join(args.goal) if args.goal else ""
    force_mode = getattr(args, "mode", "") or ""
    max_iter = getattr(args, "max", 25)
    dry_run = getattr(args, "dry_run", False)
    resume = getattr(args, "resume", False)

    # Resume mode: continue interrupted chain
    if resume:
        state = _check_resume()
        if state:
            _execute_resume(state)
            return
        print(json.dumps({"success": False, "error": "No interrupted chain to resume."}))
        return

    if not query:
        # Check for interrupted chain even without --resume
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

    # 1. Analyze intent (AI-first routing)
    intent_analysis = analyze_intent(query)

    # 2. Pre-estimate complexity (before chain selection) for scale-adaptive routing
    pre_complexity = _estimate_complexity(query, None)

    # 3. Route — find_chain uses pre_complexity to prefer -light variants for simple tasks
    route_result = _route(query)
    chain_name, chain_data = _find_chain(query, complexity=pre_complexity)

    # 4. Refine complexity with chain data (post-chain selection)
    complexity = _estimate_complexity(query, chain_data)
    mode = decide_mode(query, route_result, chain_name, chain_data, force_mode)

    # 5. Multi-goal advisory
    goals = _count_goals(query)
    if goals > 1:
        intent_analysis["multi_goal"] = True
        intent_analysis["goal_count"] = goals

    # 6. Execute
    if mode == "chain" and chain_data:
        _execute_chain(chain_name, chain_data, query, dry_run, complexity=complexity,
                       intent=intent_analysis)
    elif mode == "multi-engine":
        # Complex task → use multi-engine chain (multi-plan → work → review → commit)
        from cc_flow.skill_chains import SKILL_CHAINS
        me_chain = SKILL_CHAINS.get("multi-engine")
        if me_chain:
            _execute_chain("multi-engine", me_chain, query, dry_run, complexity="complex",
                           intent=intent_analysis)
        else:
            _execute_ralph(query, max_iter, dry_run)
    elif mode == "auto":
        _execute_auto(query, dry_run)
    else:
        _execute_ralph(query, max_iter, dry_run)
