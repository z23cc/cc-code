"""cc-flow templates — task template definitions and management."""

import json

from cc_flow.core import TASKS_DIR, error, safe_json_load

TEMPLATES_DIR = TASKS_DIR / "templates"

TASK_TEMPLATES = {
    "feature": {
        "steps": ["Research", "Design", "Implement", "Test", "Review"],
        "spec": "## Description\n\n[What feature to build]\n\n"
                "## Steps\n\n"
                "1. Research: understand requirements and existing code\n"
                "2. Design: brainstorm approach, write pseudocode\n"
                "3. Implement: write code (TDD -- tests first)\n"
                "4. Test: verify all acceptance criteria\n"
                "5. Review: self-review, then request code review\n\n"
                "## Acceptance Criteria\n\n- [ ] Feature works as described\n- [ ] Tests pass\n- [ ] No regressions\n",
    },
    "bugfix": {
        "steps": ["Investigate", "Fix", "Test", "Review"],
        "spec": "## Bug Description\n\n[What is broken]\n\n"
                "## Steps to Reproduce\n\n1. \n\n"
                "## Steps\n\n"
                "1. Investigate: reproduce bug, find root cause\n"
                "2. Fix: minimal change to fix the issue\n"
                "3. Test: add regression test, verify fix\n"
                "4. Review: confirm no side effects\n\n"
                "## Acceptance Criteria\n\n- [ ] Bug is fixed\n- [ ] Regression test added\n",
    },
    "refactor": {
        "steps": ["Analyze", "Refactor", "Test", "Review"],
        "spec": "## Refactor Goal\n\n[What to improve and why]\n\n"
                "## Steps\n\n"
                "1. Analyze: map all usages and dependents\n"
                "2. Refactor: apply changes (preserve behavior)\n"
                "3. Test: verify all existing tests pass\n"
                "4. Review: confirm behavior preserved\n\n"
                "## Acceptance Criteria\n\n- [ ] All tests pass\n- [ ] No behavior change\n- [ ] Code is simpler\n",
    },
    "security": {
        "steps": ["Scan", "Analyze", "Fix", "Verify"],
        "spec": "## Vulnerability\n\n[What the issue is]\n\n"
                "## Steps\n\n"
                "1. Scan: identify all affected code paths\n"
                "2. Analyze: assess severity and impact\n"
                "3. Fix: apply minimal remediation\n"
                "4. Verify: re-scan, confirm resolved\n\n"
                "## Acceptance Criteria\n\n- [ ] Vulnerability resolved\n- [ ] No new issues introduced\n",
    },
}


def _generate_spec(title, template_name=""):
    """Generate task spec from template or default."""
    if template_name and template_name in TASK_TEMPLATES:
        tmpl = TASK_TEMPLATES[template_name]
        return f"# {title}\n\n{tmpl['spec']}"
    return f"# {title}\n\n## Description\n\n[Describe what to do]\n\n## Acceptance Criteria\n\n- [ ] Done\n"


def cmd_template_list(_args):
    """List all available task templates (built-in + custom)."""
    templates = {}
    for name, tmpl in TASK_TEMPLATES.items():
        templates[name] = {"source": "built-in", "steps": tmpl["steps"]}
    if TEMPLATES_DIR.exists():
        for f in sorted(TEMPLATES_DIR.glob("*.json")):
            data = safe_json_load(f, default=None)
            if data:
                templates[f.stem] = {"source": "custom", "steps": data.get("steps", [])}

    print(json.dumps({"success": True, "templates": templates, "count": len(templates)}))


def cmd_template_show(args):
    """Show a template's full spec content."""
    name = args.name
    if name in TASK_TEMPLATES:
        tmpl = TASK_TEMPLATES[name]
        print(json.dumps({"success": True, "name": name, "source": "built-in",
                          "steps": tmpl["steps"], "spec": tmpl["spec"]}))
        return

    custom_path = TEMPLATES_DIR / f"{name}.json"
    if custom_path.exists():
        data = safe_json_load(custom_path, default={})
        print(json.dumps({"success": True, "name": name, "source": "custom", **data}))
        return

    error(f"Template not found: {name}. Run 'cc-flow template list' to see available templates.")


def cmd_template_create(args):
    """Create a custom task template."""
    name = args.name
    TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)

    steps = [s.strip() for s in args.steps.split(",")]
    spec = args.spec if args.spec else f"## {name.title()} Task\n\n## Steps\n\n" + "".join(
        f"{i + 1}. {s}\n" for i, s in enumerate(steps)
    ) + "\n## Acceptance Criteria\n\n- [ ] All steps completed\n"

    data = {"steps": steps, "spec": spec}
    (TEMPLATES_DIR / f"{name}.json").write_text(json.dumps(data, indent=2) + "\n")

    print(json.dumps({"success": True, "name": name, "steps": steps}))
