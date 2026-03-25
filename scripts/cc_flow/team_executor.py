"""cc-flow team executor — generate Team Agent dispatch instructions.

Replaces skill_executor's claude -p approach with Claude Code native Agent tool.
Each phase generates a message with Agent tool calls that Claude Code executes.

Architecture:
  Message 1: 6 Agents parallel (RP + Router + 3 scouts + morph-github)
  Message 2: 1 Agent (planner — synthesize all research)
  Message 3: 3-engine PUA on plan (codex + gemini subprocess)
  Message 4: N Agents (tdd — implement, with full tool access)
  Message 5: 3-engine review (subprocess)
  Message 6: auto_commit + auto_learn
"""



def build_team_instruction(chain_name, chain_data, query, complexity="medium"):
    """Build Team Agent execution instruction for a chain.

    Instead of claude -p subprocess, this generates instructions that
    Claude Code follows using its native Agent tool — giving subagents
    full Read/Write/Edit/Bash access.
    """
    steps = chain_data.get("skills", [])

    lines = [
        f"# TEAM AGENT EXECUTION: {chain_name}",
        f"Goal: {query}",
        f"Complexity: {complexity}",
        "",
        "Execute using Claude Code Agent tool. Each phase dispatches agents",
        "in parallel where possible. Agents have FULL tool access (Read/Write/Edit/Bash).",
        "",
    ]

    msg_num = 0

    # ── Message 1: Research blast (all parallel) ──
    research_agents = _build_research_phase(query)
    if research_agents:
        msg_num += 1
        lines.append(f"## Message {msg_num}: Research Blast ({len(research_agents)} agents parallel)")
        lines.append("")
        lines.append(f"**Launch ALL {len(research_agents)} in ONE message:**")
        lines.append("")
        for agent in research_agents:
            lines.append(f"- Agent: `{agent['type']}`")
            lines.append(f"  prompt: \"{agent['prompt']}\"")
            lines.append("  run_in_background: true")
            if agent.get("effort"):
                lines.append("  model: haiku  # fast for research")
            lines.append("")
        lines.append("**Wait for ALL to complete.** Collect their findings.")
        lines.append("")

    # ── Message 2: Plan (sequential, needs research results) ──
    design_steps = [s for s in steps if s.get("phase") in ("design",)]
    if design_steps:
        msg_num += 1
        planner = design_steps[0]
        skill_name = planner["skill"].lstrip("/").strip()
        lines.append(f"## Message {msg_num}: Design — {skill_name}")
        lines.append("")
        lines.append("- Agent: `cc-code:planner`")
        lines.append(f"  prompt: \"Based on the research findings above, create a detailed implementation plan for: {query}\"")
        lines.append("  run_in_background: false  ← wait for this")
        lines.append("")

    # ── Message 3: 3-engine PUA on plan (subprocess) ──
    if complexity in ("medium", "complex"):
        msg_num += 1
        lines.append(f"## Message {msg_num}: 3-Engine Plan Challenge")
        lines.append("")
        lines.append("Run plan through Codex + Gemini for stress-testing:")
        lines.append("```bash")
        lines.append('cc-flow pua --mode plan')
        lines.append("```")
        lines.append("If PUA finds issues, revise the plan before proceeding.")
        lines.append("")

    # ── Message 4: Implement (Agent with full tool access) ──
    mutate_steps = [s for s in steps if s.get("phase") == "mutate"]
    if mutate_steps:
        msg_num += 1
        n_workers = min(len(mutate_steps), 3)
        lines.append(f"## Message {msg_num}: Implement ({n_workers} worker agents)")
        lines.append("")
        if n_workers > 1:
            lines.append(f"**Launch {n_workers} workers in parallel (different modules):**")
            lines.append("")
        for i, step in enumerate(mutate_steps[:3]):
            skill_name = step["skill"].lstrip("/").strip()
            agent_type = _skill_to_agent_type(skill_name)
            lines.append(f"- Agent: `{agent_type}`")
            lines.append(f"  prompt: \"{step['role']} for: {query}. Follow TDD: write test first, then implement, then verify.\"")
            lines.append('  isolation: "worktree"  # isolated git worktree')
            if n_workers > 1:
                lines.append("  run_in_background: true")
            else:
                lines.append("  run_in_background: false")
            lines.append("")
        if n_workers > 1:
            lines.append("**Wait for ALL workers to complete.**")
            lines.append("")

    # ── Message 5: Review (3-engine subprocess) ──
    verify_steps = [s for s in steps if s.get("phase") == "verify"]
    if verify_steps:
        msg_num += 1
        lines.append(f"## Message {msg_num}: 3-Engine Review + Plan Verification")
        lines.append("")
        lines.append("Run in parallel:")
        lines.append("```bash")
        lines.append("cc-flow plan-verify  # 3 engines check: did we build what we planned?")
        lines.append("cc-flow review       # 3 engines debate, auto-PUA if disputed")
        lines.append("```")
        lines.append("")
        lines.append("If review = SHIP → proceed. If NEEDS_WORK → fix and re-review.")
        lines.append("")

    # ── Message 6: Commit + Learn ──
    gate_steps = [s for s in steps if s.get("phase") == "gate"]
    if gate_steps:
        msg_num += 1
        lines.append(f"## Message {msg_num}: Commit + Learn")
        lines.append("")
        lines.append("```bash")
        lines.append("cc-flow verify        # final lint + test")
        lines.append(f"git add -A && git commit -m \"feat({chain_name}): {query}\"")
        lines.append("```")
        lines.append("")
        lines.append("Auto-learn triggers: wisdom + metrics + Q-learning + dashboard events.")
        lines.append("")

    # Summary
    lines.append(f"## Summary: {msg_num} messages, Team Agent execution")
    lines.append(f"Research: {len(research_agents)} agents parallel")
    lines.append("Design: planner + 3-engine PUA")
    lines.append(f"Implement: {len(mutate_steps)} workers (Agent with tool access)")
    lines.append("Review: 3-engine debate + plan-verify")
    lines.append("Commit: auto-verify + auto-commit")

    return "\n".join(lines)


def _build_research_phase(query):
    """Build the research blast — 6 agents that all run in parallel."""
    return [
        {
            "type": "cc-code:cc-scout-repo",
            "prompt": f"Scan the current repository for patterns relevant to: {query}",
            "effort": "medium", "maxTurns": 5,
        },
        {
            "type": "cc-code:cc-scout-practices",
            "prompt": f"Research best practices and pitfalls for: {query}",
            "effort": "medium", "maxTurns": 5,
        },
        {
            "type": "cc-code:cc-scout-gaps",
            "prompt": f"Identify edge cases and missing requirements for: {query}",
            "effort": "medium", "maxTurns": 5,
        },
        {
            "type": "general-purpose",
            "prompt": (
                f"Use mcp__morph-mcp__github_codebase_search to find "
                f"open source implementations of: {query}. "
                f"Summarize 3-5 relevant approaches."
            ),
            "effort": "medium", "maxTurns": 3,
        },
        {
            "type": "cc-code:cc-research",
            "prompt": f"Investigate codebase architecture for: {query}. Map dependencies.",
            "effort": "high", "maxTurns": 10,
        },
        {
            "type": "general-purpose",
            "prompt": (
                f"Use mcp__RepoPrompt__context_builder to gather "
                f"deep cross-file context for: {query}. Response type: plan."
            ),
            "effort": "high", "maxTurns": 3,
        },
    ]


def _classify_phases(steps):
    """Classify steps into phase groups."""
    phases = {"observe": [], "design": [], "mutate": [], "verify": [], "gate": []}
    for s in steps:
        phase = s.get("phase", "mutate")
        phases.setdefault(phase, []).append(s)
    return phases


def _skill_to_agent_type(skill_name):
    """Map skill to best Agent subagent_type."""
    mapping = {
        "cc-tdd": "cc-code:cc-tdd",
        "cc-debug": "cc-code:cc-debug",
        "cc-simplify": "cc-code:refactor-cleaner",
        "cc-work": "cc-code:cc-work",
        "cc-plan": "cc-code:planner",
        "cc-brainstorm": "cc-code:cc-brainstorm",
        "cc-architecture": "cc-code:cc-architecture",
        "cc-research": "cc-code:cc-research",
        "cc-review": "cc-code:code-reviewer",
        "cc-security-review": "cc-code:security-reviewer",
    }
    return mapping.get(skill_name, "general-purpose")
