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

    # Check content after frontmatter
    body = "\n".join(lines[close_idx + 1:]).strip()
    if len(body) < 50:
        issues.append({"severity": "warning", "message": "Body too short (< 50 chars)"})

    # Check for heading
    if not re.search(r"^#\s", body, re.MULTILINE):
        issues.append({"severity": "warning", "message": "No top-level heading in body"})

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

    for skill_dir in sorted(skills_dir.iterdir()):
        skill_file = skill_dir / "SKILL.md"
        if not skill_file.exists():
            continue

        name = skill_dir.name
        issues = validate_skill(skill_file)
        total_issues += len(issues)
        errors += sum(1 for i in issues if i["severity"] == "error")
        warnings += sum(1 for i in issues if i["severity"] == "warning")

        if issues:
            results.append({"skill": name, "issues": issues})

    total_skills = len(list(skills_dir.iterdir()))
    passed = total_skills - len(results)

    return {
        "success": errors == 0,
        "total": total_skills,
        "passed": passed,
        "failed": len(results),
        "errors": errors,
        "warnings": warnings,
        "details": results,
    }


def cmd_validate_skills(args):
    """Validate all SKILL.md files for frontmatter, triggers, and quality."""
    result = validate_all_skills()
    print(json.dumps(result, indent=2))
