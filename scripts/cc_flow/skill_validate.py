"""cc-flow skill validation — check all SKILL.md files for quality."""

import json
import os
import re
from pathlib import Path


def _find_skills_dir():
    """Find the skills/ directory relative to the plugin root."""
    # Try CLAUDE_PLUGIN_ROOT first
    root = os.environ.get("CLAUDE_PLUGIN_ROOT", "")
    if root:
        d = Path(root) / "skills"
        if d.is_dir():
            return d
    # Fallback: relative to this file
    d = Path(__file__).parent.parent.parent / "skills"
    if d.is_dir():
        return d
    return None


def validate_skill(skill_path):
    """Validate a single SKILL.md file. Returns list of issues."""
    issues = []
    path = Path(skill_path)

    if not path.exists():
        return [{"severity": "error", "message": f"File not found: {path}"}]

    content = path.read_text()
    lines = content.splitlines()

    # Check frontmatter exists
    if not lines or lines[0].strip() != "---":
        issues.append({"severity": "error", "message": "Missing frontmatter opening ---"})
        return issues

    # Find closing ---
    close_idx = None
    for i, line in enumerate(lines[1:], 1):
        if line.strip() == "---":
            close_idx = i
            break

    if close_idx is None:
        issues.append({"severity": "error", "message": "Missing frontmatter closing ---"})
        return issues

    frontmatter = "\n".join(lines[1:close_idx])

    # Check name field
    if "name:" not in frontmatter:
        issues.append({"severity": "error", "message": "Missing 'name:' field"})

    # Check description field
    if "description:" not in frontmatter:
        issues.append({"severity": "error", "message": "Missing 'description:' field"})
    else:
        # Check TRIGGER keywords
        if "TRIGGER" not in content[:close_idx * 80]:
            issues.append({"severity": "warning", "message": "No TRIGGER keywords in description"})

        # Check Chinese keywords
        has_chinese = bool(re.search(r"[\u4e00-\u9fff]", frontmatter))
        if not has_chinese:
            issues.append({"severity": "warning", "message": "No Chinese keywords in description"})

    # Check NOT FOR field (helps routing disambiguation)
    if "NOT FOR" not in content[:close_idx * 80]:
        issues.append({"severity": "info", "message": "No NOT FOR disambiguation in description"})

    # Check FLOWS INTO / DEPENDS ON (flow graph connectivity)
    desc_text = frontmatter
    has_flow = "FLOWS INTO" in desc_text or "DEPENDS ON" in desc_text
    if not has_flow:
        issues.append({"severity": "info", "message": "No FLOWS INTO or DEPENDS ON — orphan in flow graph"})

    # Check On Completion section (context protocol)
    if "## On Completion" not in content:
        if has_flow:
            issues.append({"severity": "warning", "message": "Has flow edges but no On Completion section"})

    # Check content after frontmatter
    body = "\n".join(lines[close_idx + 1:]).strip()
    if len(body) < 50:
        issues.append({"severity": "warning", "message": "Body too short (< 50 chars)"})

    # Check for heading
    if not re.search(r"^#\s", body, re.MULTILINE):
        issues.append({"severity": "warning", "message": "No top-level heading in body"})

    return issues


def _cross_reference_check(skills_dir):
    """Cross-reference validation: commands ↔ skills, flow graph consistency."""
    issues = []

    # Known aliases: command name → skill directory name (or vice versa)
    KNOWN_ALIASES = {
        "cc-brainstorm": "cc-brainstorming", "cc-brainstorming": "cc-brainstorm",
        "cc-debug": "cc-debugging", "cc-debugging": "cc-debug",
        "cc-refine": "cc-refinement", "cc-refinement": "cc-refine",
        "cc-audit": "cc-readiness-audit", "cc-readiness-audit": "cc-audit",
        "cc-fix": "cc-debugging", "cc-tasks": "cc-task-tracking",
        "cc-review": "cc-code-review-loop", "cc-code-review-loop": "cc-review",
        "cc-prime": "cc-readiness-audit", "cc-perf": "cc-performance",
        "cc-commit": "cc-git-workflow", "cc-route": "cc-feedback-loop",
        "cc-help": "cc-context-tips", "cc-scout": "cc-scout-practices",
        "cc-simplify": "cc-refinement", "cc-team": "cc-teams",
        "cc-interview": "cc-brainstorming", "cc-blueprint": "cc-plan",
        "cc-pr-review": "cc-code-review-loop", "cc-ralph-init": "cc-ralph",
    }
    # Scouts are accessed via /cc-scout {type}, not individual commands
    SCOUT_SKILLS = {
        f"cc-scout-{t}" for t in (
            "build", "context", "docs", "docs-gap", "env", "gaps",
            "observability", "practices", "repo", "security", "testing", "tooling",
        )
    }

    root = skills_dir.parent
    commands_dir = root / "commands"

    skill_names = set()
    for d in skills_dir.iterdir():
        if d.is_dir() and d.name.startswith("cc-"):
            skill_names.add(d.name)

    # 1. Check every skill has a matching command (skip aliased ones)
    if commands_dir.exists():
        cmd_names = {f.stem for f in commands_dir.glob("cc-*.md")}
        for sname in sorted(skill_names):
            if sname not in cmd_names and sname not in KNOWN_ALIASES and sname not in SCOUT_SKILLS:
                # Check if any alias maps to this skill
                has_alias = any(v == sname for v in KNOWN_ALIASES.values())
                if not has_alias:
                    issues.append({
                        "type": "missing_command",
                        "skill": sname,
                        "message": f"Skill '{sname}' has no matching command",
                    })

    # 2. Check flow graph references resolve (with alias awareness)
    try:
        from cc_flow.skill_flow import build_graph
        graph = build_graph(skills_dir)
        all_known = set(graph.get("nodes", {}).keys()) | set(KNOWN_ALIASES.keys())
        # Also add cc-commit which is virtual
        all_known.add("cc-commit")

        for name, node in graph.get("nodes", {}).items():
            for ref in node.get("flows_into", []):
                if ref not in all_known:
                    issues.append({
                        "type": "broken_flow_ref",
                        "skill": name,
                        "message": f"FLOWS INTO '{ref}' — not found",
                    })
            for ref in node.get("depends_on", []):
                if ref not in all_known:
                    issues.append({
                        "type": "broken_dep_ref",
                        "skill": name,
                        "message": f"DEPENDS ON '{ref}' — not found",
                    })
    except (ImportError, Exception):
        pass

    return issues


def validate_all_skills():
    """Validate all skills in the skills/ directory."""
    skills_dir = _find_skills_dir()
    if not skills_dir:
        return {"success": False, "error": "skills/ directory not found"}

    results = []
    total_issues = 0
    errors = 0
    warnings = 0
    infos = 0

    for skill_dir in sorted(skills_dir.iterdir()):
        skill_file = skill_dir / "SKILL.md"
        if not skill_file.exists():
            continue

        name = skill_dir.name
        issues = validate_skill(skill_file)
        total_issues += len(issues)
        errors += sum(1 for i in issues if i["severity"] == "error")
        warnings += sum(1 for i in issues if i["severity"] == "warning")
        infos += sum(1 for i in issues if i["severity"] == "info")

        if issues:
            results.append({"skill": name, "issues": issues})

    # Cross-reference checks
    xref_issues = _cross_reference_check(skills_dir)
    if xref_issues:
        results.append({"skill": "_cross_references", "issues": [
            {"severity": "warning", "message": i["message"]} for i in xref_issues
        ]})
        warnings += len(xref_issues)

    total_skills = sum(1 for d in skills_dir.iterdir() if d.is_dir() and d.name.startswith("cc-"))
    passed = total_skills - len([r for r in results if r["skill"] != "_cross_references"])

    return {
        "success": errors == 0,
        "total": total_skills,
        "passed": passed,
        "failed": len([r for r in results if r["skill"] != "_cross_references"]),
        "errors": errors,
        "warnings": warnings,
        "infos": infos,
        "cross_ref_issues": len(xref_issues),
        "details": results,
    }


def cmd_validate_skills(args):
    """Validate all SKILL.md files for frontmatter, triggers, and quality."""
    result = validate_all_skills()
    print(json.dumps(result, indent=2))
