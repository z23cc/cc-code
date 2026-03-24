"""cc-flow context-budget — analyze token overhead from plugins, rules, skills."""

import json
from pathlib import Path

from cc_flow import skin


def _estimate_tokens(text: str) -> int:
    """Rough token estimate: 1 token ~ 4 characters."""
    return len(text) // 4


def _read_file_tokens(path: Path) -> int:
    """Read a file and return estimated token count."""
    try:
        return _estimate_tokens(path.read_text())
    except OSError:
        return 0


def _find_project_root() -> Path:
    """Find the project root (where CLAUDE.md lives)."""
    cwd = Path.cwd()
    # Walk up to find CLAUDE.md
    for parent in [cwd, *cwd.parents]:
        if (parent / "CLAUDE.md").exists():
            return parent
    return cwd


def _scan_claude_md(root: Path) -> list[tuple[str, int, int]]:
    """Scan CLAUDE.md files. Returns list of (path, file_count, tokens)."""
    results = []
    # Project CLAUDE.md
    cm = root / "CLAUDE.md"
    if cm.exists():
        tokens = _read_file_tokens(cm)
        results.append((str(cm.relative_to(root)), 1, tokens))
    # Home CLAUDE.md
    home_cm = Path.home() / "CLAUDE.md"
    if home_cm.exists():
        tokens = _read_file_tokens(home_cm)
        results.append(("~/CLAUDE.md", 1, tokens))
    # Private CLAUDE.md
    private_cm = Path.home() / ".claude" / "CLAUDE.md"
    if private_cm.exists():
        tokens = _read_file_tokens(private_cm)
        results.append(("~/.claude/CLAUDE.md", 1, tokens))
    return results


def _scan_rules(root: Path) -> tuple[int, int]:
    """Scan rules/*.md files. Returns (file_count, total_tokens)."""
    rules_dir = root / "rules"
    if not rules_dir.exists():
        return 0, 0
    count = 0
    total = 0
    for f in sorted(rules_dir.glob("*.md")):
        count += 1
        total += _read_file_tokens(f)
    return count, total


def _scan_hooks(root: Path) -> tuple[int, int]:
    """Scan hooks/hooks.json. Returns (file_count, total_tokens)."""
    hooks_file = root / "hooks" / "hooks.json"
    if not hooks_file.exists():
        # Try .claude/hooks.json
        hooks_file = root / ".claude" / "hooks.json"
    if not hooks_file.exists():
        return 0, 0
    return 1, _read_file_tokens(hooks_file)


def _estimate_session_start(root: Path) -> int:
    """Estimate tokens from SessionStart hook output."""
    # SessionStart hooks typically inject context on startup.
    # Estimate based on hooks.json config for SessionStart events.
    hooks_file = root / "hooks" / "hooks.json"
    if not hooks_file.exists():
        hooks_file = root / ".claude" / "hooks.json"
    if not hooks_file.exists():
        return 0
    try:
        data = json.loads(hooks_file.read_text())
        hooks_map = data.get("hooks", data) if isinstance(data, dict) else {}
        estimate = 0
        # Format: {"hooks": {"EventName": [{"matcher": ..., "hooks": [...]}]}}
        if isinstance(hooks_map, dict):
            session_hooks = hooks_map.get("SessionStart", [])
            if isinstance(session_hooks, list):
                # Each SessionStart hook group typically outputs 200-500 tokens
                estimate += len(session_hooks) * 350
        return estimate
    except (json.JSONDecodeError, OSError):
        return 0


def _scan_agents(root: Path) -> tuple[int, int]:
    """Scan agents/*.md files. Returns (file_count, total_tokens)."""
    agents_dir = root / "agents"
    if not agents_dir.exists():
        return 0, 0
    count = 0
    total = 0
    for f in sorted(agents_dir.glob("*.md")):
        count += 1
        total += _read_file_tokens(f)
    return count, total


def _scan_skills(root: Path) -> tuple[int, int]:
    """Scan skills/*/SKILL.md description fields only. Returns (file_count, total_tokens)."""
    skills_dir = root / "skills"
    if not skills_dir.exists():
        return 0, 0
    count = 0
    total = 0
    for skill_md in sorted(skills_dir.glob("*/SKILL.md")):
        count += 1
        # For matching, only the description/frontmatter is loaded
        try:
            text = skill_md.read_text()
            # Estimate: frontmatter + first paragraph (roughly 30% of file)
            desc_tokens = _estimate_tokens(text) // 3
            total += max(desc_tokens, 50)  # minimum 50 tokens per skill
        except OSError:
            total += 50
    return count, total


def cmd_context_budget(args) -> None:
    """Analyze token overhead from always-loaded and on-demand components."""
    root = _find_project_root()

    skin.heading("Context Budget Analysis")
    skin.dim(f"Project root: {root}")
    print()

    rows = []
    total_tokens = 0
    heavy_components = []

    # 1. CLAUDE.md files (always loaded)
    claude_entries = _scan_claude_md(root)
    for path, count, tokens in claude_entries:
        rows.append((path, str(count), str(tokens), "always"))
        total_tokens += tokens
        if tokens > 2000:
            heavy_components.append((path, tokens))

    # 2. Rules (always loaded, alwaysApply: true)
    rules_count, rules_tokens = _scan_rules(root)
    if rules_count > 0:
        rows.append(("rules/*.md", str(rules_count), str(rules_tokens), "always"))
        total_tokens += rules_tokens
        if rules_tokens > 2000:
            heavy_components.append(("rules/*.md", rules_tokens))

    # 3. Hooks config
    hooks_count, hooks_tokens = _scan_hooks(root)
    if hooks_count > 0:
        rows.append(("hooks.json", str(hooks_count), str(hooks_tokens), "always"))
        total_tokens += hooks_tokens
        if hooks_tokens > 2000:
            heavy_components.append(("hooks.json", hooks_tokens))

    # 4. SessionStart output estimate
    session_tokens = _estimate_session_start(root)
    if session_tokens > 0:
        rows.append(("SessionStart output", "~", str(session_tokens), "startup"))
        total_tokens += session_tokens

    # 5. Agents (on-demand)
    agents_count, agents_tokens = _scan_agents(root)
    if agents_count > 0:
        rows.append(("agents/*.md", str(agents_count), str(agents_tokens), "on-demand"))
        total_tokens += agents_tokens
        if agents_tokens > 2000:
            heavy_components.append(("agents/*.md", agents_tokens))

    # 6. Skills descriptions (loaded for matching)
    skills_count, skills_tokens = _scan_skills(root)
    if skills_count > 0:
        rows.append(("skills/*/SKILL.md", str(skills_count), str(skills_tokens), "matching"))
        total_tokens += skills_tokens
        if skills_tokens > 2000:
            heavy_components.append(("skills/*/SKILL.md", skills_tokens))

    # Add percentage column
    display_rows = []
    for component, count, tokens, load_type in rows:
        tok = int(tokens) if tokens.isdigit() else 0
        pct = f"{tok / total_tokens * 100:.1f}%" if total_tokens > 0 else "0%"
        heavy_marker = " [HEAVY]" if tok > 2000 else ""
        display_rows.append((component, count, tokens, pct, load_type + heavy_marker))

    skin.table(
        ["Component", "Files", "Est. Tokens", "% Total", "Load Type"],
        display_rows,
    )

    # Total
    print()
    skin.info(f"Total estimated tokens: {total_tokens:,}")

    # Heavy warnings
    if heavy_components:
        print()
        skin.warning(f"{len(heavy_components)} component(s) exceed 2,000 tokens:")
        for name, tokens in heavy_components:
            skin.dim(f"  {name}: ~{tokens:,} tokens")

    # Optimization suggestions
    if total_tokens > 10000:
        print()
        skin.heading("Optimization Suggestions")
        suggestions = []
        if any(name == "rules/*.md" for name, _ in heavy_components):
            suggestions.append("Consolidate rules — merge related rules into fewer files")
        if any("CLAUDE.md" in name for name, _ in heavy_components):
            suggestions.append("Trim CLAUDE.md — move rarely-used details to docs/ and link them")
        if any("agents" in name for name, _ in heavy_components):
            suggestions.append("Split large agents — keep agent prompts focused and concise")
        if any("skills" in name for name, _ in heavy_components):
            suggestions.append("Shorten SKILL.md descriptions — use concise trigger patterns")
        if not suggestions:
            suggestions.append("Review largest components and extract rarely-used content")
            suggestions.append("Use on-demand loading patterns where possible")
        for s in suggestions:
            skin.dim(f"  - {s}")
        print()
        skin.warning(
            f"Total ({total_tokens:,} tokens) exceeds 10,000 — "
            "consider reducing always-loaded content",
        )
