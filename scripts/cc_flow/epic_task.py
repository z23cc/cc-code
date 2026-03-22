"""cc-flow epic/task CRUD commands.

Template commands (list/show/create) moved to templates.py.
"""

import argparse
import json
import re
import sys
from pathlib import Path

from cc_flow.core import (
    COMPLETED_DIR,
    EPICS_DIR,
    META_FILE,
    TASKS_DIR,
    TASKS_SUBDIR,
    all_tasks,
    error,
    locked_meta_update,
    now_iso,
    safe_json_load,
    save_meta,
    save_task,
    slugify,
)
from cc_flow.templates import _generate_spec

# TASK_TEMPLATES moved to templates.py

def cmd_init(_args):
    """Initialize .tasks/ directory structure."""
    for d in [TASKS_DIR, EPICS_DIR, TASKS_SUBDIR, COMPLETED_DIR]:
        d.mkdir(parents=True, exist_ok=True)
    if not META_FILE.exists():
        save_meta({"next_epic": 1})
    print(json.dumps({"success": True, "path": str(TASKS_DIR)}))


def cmd_epic_create(args):
    """Create a new epic with title, spec file, and metadata."""
    from cc_flow.core import allocate_epic_num
    slug = slugify(args.title)
    epic_num = locked_meta_update(allocate_epic_num)
    epic_id = f"epic-{epic_num}-{slug}"

    spec_path = EPICS_DIR / f"{epic_id}.md"
    spec_path.write_text(
        f"# Epic: {args.title}\n\n"
        f"## Goal\n\n[Describe the goal]\n\n"
        f"## Requirements\n\n- [ ] [Requirement 1]\n\n"
        f"## Acceptance Criteria\n\n- [Criterion 1]\n",
    )
    print(json.dumps({"success": True, "id": epic_id, "spec": str(spec_path)}))


def cmd_epic_import(args):
    """Import tasks from a plan markdown file. Parses ### Task N: Title headers."""

    plan_path = Path(args.file)
    if not plan_path.exists():
        error(f"File not found: {args.file}")

    content = plan_path.read_text()

    # Extract title from first H1
    title_match = re.search(r"^#\s+(.+)", content, re.MULTILINE)
    title = title_match.group(1).strip() if title_match else plan_path.stem

    # Create epic with locked meta
    cmd_init(argparse.Namespace())
    from cc_flow.core import allocate_epic_num
    slug = slugify(title)
    epic_num = locked_meta_update(allocate_epic_num)
    epic_id = f"epic-{epic_num}-{slug}"

    # Copy plan as epic spec
    spec_path = EPICS_DIR / f"{epic_id}.md"
    spec_path.write_text(content)

    # Parse tasks: ### Task N: Title  or  ### N. Title  or  ### Title
    task_pattern = re.compile(
        r"^###\s+(?:Task\s+\d+[:.]\s*|(\d+)\.\s+)?(.+)",
        re.MULTILINE,
    )
    matches = list(task_pattern.finditer(content))

    task_num = 0
    prev_task_id = None
    created = []
    for m in matches:
        task_title = m.group(2).strip()
        if not task_title or task_title.lower().startswith("phase"):
            continue
        task_num += 1
        task_id = f"{epic_id}.{task_num}"

        # Extract content between this ### and the next ###
        start = m.end()
        next_match = task_pattern.search(content, start)
        end = next_match.start() if next_match else len(content)
        task_body = content[start:end].strip()

        deps = [prev_task_id] if prev_task_id and args.sequential else []

        state = {
            "id": task_id,
            "epic": epic_id,
            "title": task_title,
            "status": "todo",
            "depends_on": deps,
            "created": now_iso(),
        }
        save_task(TASKS_SUBDIR / f"{task_id}.json", state)

        task_spec = TASKS_SUBDIR / f"{task_id}.md"
        task_spec.write_text(f"# Task: {task_title}\n\n{task_body}\n")

        created.append(task_id)
        prev_task_id = task_id

    print(json.dumps({
        "success": True,
        "epic": epic_id,
        "tasks_created": len(created),
        "tasks": created,
    }))


def cmd_task_create(args):
    """Create a new task in an epic with title, size, deps, tags, and template."""
    from cc_flow.core import resolve_epic_id
    epic_id = resolve_epic_id(args.epic)
    # Find next task number for this epic
    existing = list(TASKS_SUBDIR.glob(f"{epic_id}.*.json"))
    next_num = len(existing) + 1
    task_id = f"{epic_id}.{next_num}"
    deps = args.deps.split(",") if args.deps else []

    size = getattr(args, "size", None) or "M"
    tags = [t.strip() for t in args.tags.split(",") if t.strip()] if getattr(args, "tags", "") else []
    template = getattr(args, "template", "") or ""

    state = {
        "id": task_id,
        "epic": epic_id,
        "title": args.title,
        "status": "todo",
        "depends_on": deps,
        "size": size,
        "tags": tags,
        "created": now_iso(),
    }
    save_task(TASKS_SUBDIR / f"{task_id}.json", state)

    # Generate spec from template or default
    spec_content = _generate_spec(args.title, template)
    spec_path = TASKS_SUBDIR / f"{task_id}.md"
    spec_path.write_text(spec_content)
    print(json.dumps({"success": True, "id": task_id, "epic": epic_id, "tags": tags}))


def cmd_epic_close(args):
    """Close epic — requires all tasks done."""
    epic_id = args.id
    epic_path = EPICS_DIR / f"{epic_id}.md"
    if not epic_path.exists():
        error(f"Epic not found: {epic_id}")

    tasks = all_tasks()
    epic_tasks = [t for t in tasks.values() if t.get("epic") == epic_id]
    not_done = [t for t in epic_tasks if t["status"] != "done"]
    if not_done:
        ids = [t["id"] for t in not_done]
        print(json.dumps({"success": False, "error": f"Cannot close: {len(not_done)} tasks not done", "pending": ids}))
        sys.exit(1)

    # Move epic and tasks to completed/
    completed_epic = COMPLETED_DIR / epic_path.name
    epic_path.rename(completed_epic)
    for t in epic_tasks:
        for ext in (".json", ".md"):
            src = TASKS_SUBDIR / f"{t['id']}{ext}"
            if src.exists():
                src.rename(COMPLETED_DIR / src.name)

    print(json.dumps({"success": True, "id": epic_id, "tasks_archived": len(epic_tasks)}))


def cmd_task_reset(args):
    """Reset task to todo, clearing started/completed/blocked fields."""
    path = TASKS_SUBDIR / f"{args.id}.json"
    if not path.exists():
        error(f"Task not found: {args.id}")

    data = safe_json_load(path)
    data["status"] = "todo"
    for field in ("started", "completed", "summary", "blocked_reason", "blocked_at"):
        data.pop(field, None)
    save_task(path, data)
    print(json.dumps({"success": True, "id": args.id, "status": "todo"}))


def cmd_task_update(args):
    """Update task attributes (title, priority, size, tags)."""
    path = TASKS_SUBDIR / f"{args.id}.json"
    if not path.exists():
        error(f"Task not found: {args.id}")

    data = safe_json_load(path)
    updated = []
    if args.title:
        data["title"] = args.title
        updated.append("title")
    if args.priority is not None:
        data["priority"] = args.priority
        updated.append("priority")
    if args.size:
        data["size"] = args.size
        updated.append("size")
    if args.tags:
        data["tags"] = [t.strip() for t in args.tags.split(",")]
        updated.append("tags")

    if not updated:
        error("Nothing to update. Use --title, --priority, --size, or --tags.")

    save_task(path, data)
    print(json.dumps({"success": True, "id": args.id, "updated": updated}))


def cmd_task_comment(args):
    """Add a comment/note to a task without changing its status."""
    path = TASKS_SUBDIR / f"{args.id}.json"
    if not path.exists():
        error(f"Task not found: {args.id}")

    data = safe_json_load(path)
    comments = data.get("comments", [])
    comments.append({"text": args.text, "at": now_iso()})
    data["comments"] = comments
    save_task(path, data)
    print(json.dumps({"success": True, "id": args.id, "comment_count": len(comments)}))


def cmd_task_set_spec(args):
    """Update task spec from file."""
    task_id = args.id
    spec_path = TASKS_SUBDIR / f"{task_id}.md"
    json_path = TASKS_SUBDIR / f"{task_id}.json"

    if not json_path.exists():
        error(f"Task not found: {task_id}")

    src = Path(args.file)
    if not src.exists():
        error(f"File not found: {args.file}")

    spec_path.write_text(src.read_text())
    print(json.dumps({"success": True, "id": task_id, "spec": str(spec_path)}))


def cmd_epic_reset(args):
    """Reset all tasks in an epic to todo."""
    epic_id = args.id
    tasks = all_tasks()
    epic_tasks = [t for t in tasks.values() if t.get("epic") == epic_id]
    if not epic_tasks:
        error(f"No tasks found for: {epic_id}")

    reset_count = 0
    for t in epic_tasks:
        if t["status"] != "todo":
            t["status"] = "todo"
            for field in ("started", "completed", "summary", "blocked_reason", "blocked_at"):
                t.pop(field, None)
            save_task(TASKS_SUBDIR / f"{t['id']}.json", t)
            reset_count += 1

    print(json.dumps({"success": True, "epic": epic_id, "reset": reset_count}))


def cmd_dep_add(args):
    """Add dependency to existing task."""
    path = TASKS_SUBDIR / f"{args.id}.json"
    if not path.exists():
        error(f"Task not found: {args.id}")

    dep_path = TASKS_SUBDIR / f"{args.dep}.json"
    if not dep_path.exists():
        error(f"Dependency not found: {args.dep}")

    data = safe_json_load(path)
    deps = data.get("depends_on", [])
    if args.dep not in deps:
        deps.append(args.dep)
        data["depends_on"] = deps
        save_task(path, data)
    print(json.dumps({"success": True, "id": args.id, "depends_on": deps}))


def cmd_dep_show(args):
    """Show dependency chain for a task — what it needs and what needs it."""
    task_id = args.id
    tasks = all_tasks()
    if task_id not in tasks:
        error(f"Task not found: {task_id}")

    task = tasks[task_id]

    # Upstream: what this task depends on (recursive)
    def _upstream(tid, visited=None):
        if visited is None:
            visited = set()
        if tid in visited:
            return []
        visited.add(tid)
        result = []
        for dep in tasks.get(tid, {}).get("depends_on", []):
            if dep in tasks:
                result.append({"id": dep, "title": tasks[dep].get("title", ""), "status": tasks[dep]["status"]})
                result.extend(_upstream(dep, visited))
        return result

    # Downstream: what depends on this task
    downstream = [
        {"id": tid, "title": t.get("title", ""), "status": t["status"]}
        for tid, t in tasks.items()
        if task_id in t.get("depends_on", [])
    ]

    print(json.dumps({
        "success": True,
        "id": task_id,
        "title": task.get("title", ""),
        "status": task["status"],
        "upstream": _upstream(task_id),
        "downstream": downstream,
        "blocked_by": [
            u["id"] for u in _upstream(task_id)
            if u["status"] != "done" and u["id"] in task.get("depends_on", [])
        ],
    }))



# Re-export template commands for backward compatibility
from cc_flow.templates import (  # noqa: E402, F401
    cmd_template_create,
    cmd_template_list,
    cmd_template_show,
)
