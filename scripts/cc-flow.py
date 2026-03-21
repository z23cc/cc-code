#!/usr/bin/env python3
"""cc-flow — task & workflow manager for cc-code plugin.

Version: 2.4.0

Usage:
    cc-flow init
    cc-flow epic create --title "Epic title"
    cc-flow epic close <epic-id>
    cc-flow epic import --file plan.md
    cc-flow epic reset <epic-id>
    cc-flow task create --epic <epic-id> --title "Task title" [--deps id1,id2] [--size S] [--tags a,b] [--template feature]
    cc-flow task reset <task-id>
    cc-flow task set-spec <task-id> --file spec.md
    cc-flow rollback <task-id> [--confirm]
    cc-flow dep add <task-id> <dep-id>
    cc-flow list [--json]
    cc-flow epics
    cc-flow tasks [--epic <epic-id>] [--status todo|in_progress|done|blocked]
    cc-flow show <id>
    cc-flow ready [--epic <epic-id>]
    cc-flow next [--epic <epic-id>]
    cc-flow start <task-id>
    cc-flow done <task-id> [--summary "What was done"]
    cc-flow block <task-id> --reason "Why blocked"
    cc-flow progress [--epic <epic-id>]
    cc-flow status
    cc-flow validate
    cc-flow scan [--create-tasks]
    cc-flow auto [scan|run|test|full|status]
    cc-flow route <query...>
    cc-flow learn --task "X" --outcome success --approach "Y" --lesson "Z" [--score 5]
    cc-flow learnings [--search query] [--last N]
    cc-flow consolidate
    cc-flow history
    cc-flow search <query> [--dir path]
    cc-flow compact [--file path] [--ratio 0.3] [--output path]
    cc-flow github-search <query> --repo owner/repo
    cc-flow session [save|restore|list]
    cc-flow dashboard
    cc-flow doctor [--format text|json]
    cc-flow graph [--epic <id>] [--format mermaid|ascii|dot]
    cc-flow config [key] [value]
    cc-flow log --status KEPT --task-id <id> --description "..." [--iteration N]
    cc-flow log --show 10
    cc-flow summary
    cc-flow stats
    cc-flow archive
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

# Import shared utilities from cc_flow package
sys.path.insert(0, str(Path(__file__).parent))
from cc_flow import VERSION  # noqa: E402
from cc_flow.core import (  # noqa: E402
    COMPLETED_DIR, CONFIG_FILE, DEFAULT_CONFIG, EPICS_DIR, LEARNINGS_DIR,
    LOG_FILE, META_FILE, ROUTE_STATS_FILE, SESSION_DIR, TASKS_DIR,
    TASKS_SUBDIR, all_tasks, get_morph_client as _get_morph_client,
    load_meta, locked_meta_update as _locked_meta_update,
    now_iso, safe_json_load, save_meta, save_task, slugify,
    error as _error,
)


def cmd_init(_args):
    for d in [TASKS_DIR, EPICS_DIR, TASKS_SUBDIR, COMPLETED_DIR]:
        d.mkdir(parents=True, exist_ok=True)
    if not META_FILE.exists():
        save_meta({"next_epic": 1})
    print(json.dumps({"success": True, "path": str(TASKS_DIR)}))


def cmd_epic_create(args):
    slug = slugify(args.title)

    def allocate(meta):
        epic_num = meta["next_epic"]
        meta["next_epic"] = epic_num + 1
        return epic_num

    epic_num = _locked_meta_update(allocate)
    epic_id = f"epic-{epic_num}-{slug}"

    spec_path = EPICS_DIR / f"{epic_id}.md"
    spec_path.write_text(
        f"# Epic: {args.title}\n\n"
        f"## Goal\n\n[Describe the goal]\n\n"
        f"## Requirements\n\n- [ ] [Requirement 1]\n\n"
        f"## Acceptance Criteria\n\n- [Criterion 1]\n"
    )
    print(json.dumps({"success": True, "id": epic_id, "spec": str(spec_path)}))


def cmd_epic_import(args):
    """Import tasks from a plan markdown file. Parses ### Task N: Title headers."""
    import re

    plan_path = Path(args.file)
    if not plan_path.exists():
        print(json.dumps({"success": False, "error": f"File not found: {args.file}"}))
        sys.exit(1)

    content = plan_path.read_text()

    # Extract title from first H1
    title_match = re.search(r"^#\s+(.+)", content, re.MULTILINE)
    title = title_match.group(1).strip() if title_match else plan_path.stem

    # Create epic with locked meta
    cmd_init(argparse.Namespace())
    slug = slugify(title)

    def allocate(meta):
        n = meta["next_epic"]
        meta["next_epic"] = n + 1
        return n

    epic_num = _locked_meta_update(allocate)
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


TASK_TEMPLATES = {
    "feature": {
        "steps": ["Research", "Design", "Implement", "Test", "Review"],
        "spec": "## Description\n\n[What feature to build]\n\n"
                "## Steps\n\n"
                "1. Research: understand requirements and existing code\n"
                "2. Design: brainstorm approach, write pseudocode\n"
                "3. Implement: write code (TDD — tests first)\n"
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
        return f"# Task: {title}\n\n{tmpl['spec']}"
    return (
        f"# Task: {title}\n\n"
        f"## Description\n\n[Describe what to do]\n\n"
        f"## Acceptance Criteria\n\n- [ ] [Criterion 1]\n"
    )


def cmd_task_create(args):
    epic_id = args.epic
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


def cmd_list(args):
    epics = {}
    for f in sorted(EPICS_DIR.glob("*.md")):
        epic_id = f.stem
        epics[epic_id] = {"id": epic_id, "tasks": []}

    tasks = all_tasks()
    for t in tasks.values():
        epic = t.get("epic", "")
        if epic in epics:
            epics[epic]["tasks"].append(t)

    if getattr(args, "json", False):
        print(json.dumps({"success": True, "epics": list(epics.values()), "count": len(epics)}))
        return

    for epic_id, epic in epics.items():
        done = sum(1 for t in epic["tasks"] if t["status"] == "done")
        total = len(epic["tasks"])
        # Extract title from epic spec first line
        epic_spec = EPICS_DIR / f"{epic_id}.md"
        epic_title = ""
        if epic_spec.exists():
            first_line = epic_spec.read_text().split("\n", 1)[0]
            epic_title = first_line.lstrip("# ").replace("Epic:", "").strip()
        title_part = f": {epic_title}" if epic_title else ""
        print(f"\n[{epic_id}]{title_part} ({done}/{total} done)")
        for t in epic["tasks"]:
            status = t["status"]
            marker = {"todo": "○", "in_progress": "◐", "done": "●", "blocked": "✗"}
            size = t.get("size", "")
            size_tag = f" [{size}]" if size else ""
            print(f"  {marker.get(status, '?')} [{status:12}] {t['id']}: {t['title']}{size_tag}")

    if not epics:
        print("No epics found. Run: cc-flow init && cc-flow epic create --title '...'")


def cmd_epics(_args):
    epics = []
    tasks = all_tasks()
    for f in sorted(EPICS_DIR.glob("*.md")):
        epic_id = f.stem
        epic_tasks = [t for t in tasks.values() if t.get("epic") == epic_id]
        done = sum(1 for t in epic_tasks if t["status"] == "done")
        epics.append({"id": epic_id, "tasks": len(epic_tasks), "done": done})
    print(json.dumps({"success": True, "epics": epics}))


def cmd_tasks(args):
    tasks = all_tasks()
    tag_filter = getattr(args, "tag", "") or ""
    result = []
    for t in tasks.values():
        if args.epic and t.get("epic") != args.epic:
            continue
        if args.status and t["status"] != args.status:
            continue
        if tag_filter and tag_filter not in t.get("tags", []):
            continue
        result.append(t)
    print(json.dumps({"success": True, "tasks": result, "count": len(result)}))


def cmd_show(args):
    task_id = args.id
    # Try task first
    task_path = TASKS_SUBDIR / f"{task_id}.json"
    if task_path.exists():
        data = safe_json_load(task_path)
        spec_path = TASKS_SUBDIR / f"{task_id}.md"
        spec = spec_path.read_text() if spec_path.exists() else ""
        print(json.dumps({"success": True, "type": "task", "data": data}))
        if spec:
            print(f"\n{spec}")
        return

    # Try epic
    epic_path = EPICS_DIR / f"{task_id}.md"
    if epic_path.exists():
        print(epic_path.read_text())
        tasks = [t for t in all_tasks().values() if t.get("epic") == task_id]
        if tasks:
            print(f"\n## Tasks ({sum(1 for t in tasks if t['status'] == 'done')}/{len(tasks)} done)")
            for t in tasks:
                print(f"- [{t['status']}] {t['id']}: {t['title']}")
        return

    print(json.dumps({"success": False, "error": f"Not found: {task_id}"}))
    sys.exit(1)


def cmd_ready(args):
    tasks = all_tasks()
    ready, in_progress, blocked = [], [], []

    for t in tasks.values():
        if args.epic and t.get("epic") != args.epic:
            continue
        if t["status"] == "in_progress":
            in_progress.append(t)
        elif t["status"] == "blocked":
            blocked.append(t)
        elif t["status"] == "todo":
            deps_done = all(
                tasks.get(d, {}).get("status") == "done"
                for d in t.get("depends_on", [])
            )
            if deps_done:
                ready.append(t)

    print(json.dumps({
        "success": True,
        "ready": [{"id": t["id"], "title": t["title"]} for t in ready],
        "in_progress": [{"id": t["id"], "title": t["title"]} for t in in_progress],
        "blocked": [{"id": t["id"], "title": t["title"]} for t in blocked],
    }))


def cmd_start(args):
    path = TASKS_SUBDIR / f"{args.id}.json"
    if not path.exists():
        print(json.dumps({"success": False, "error": f"Task not found: {args.id}"}))
        sys.exit(1)

    data = safe_json_load(path)
    if data["status"] not in ("todo", "blocked"):
        print(json.dumps({"success": False, "error": f"Cannot start task with status: {data['status']}"}))
        sys.exit(1)

    # Check dependencies
    tasks = all_tasks()
    for dep in data.get("depends_on", []):
        dep_task = tasks.get(dep)
        if dep_task and dep_task["status"] != "done":
            print(json.dumps({"success": False, "error": f"Dependency not done: {dep}"}))
            sys.exit(1)

    data["status"] = "in_progress"
    data["started"] = now_iso()

    # Record git SHA at start for diff tracking and rollback
    import subprocess as _sp
    try:
        sha = _sp.run(["git", "rev-parse", "HEAD"],
                       capture_output=True, text=True, timeout=5).stdout.strip()
        if sha:
            data["git_sha_start"] = sha
    except (OSError, _sp.TimeoutExpired):
        pass

    save_task(path, data)
    print(json.dumps({"success": True, "id": args.id, "status": "in_progress"}))


def cmd_done(args):
    path = TASKS_SUBDIR / f"{args.id}.json"
    if not path.exists():
        print(json.dumps({"success": False, "error": f"Task not found: {args.id}"}))
        sys.exit(1)

    data = safe_json_load(path)

    # Calculate duration if started
    duration_sec = None
    if data.get("started"):
        try:
            started = datetime.fromisoformat(data["started"].replace("Z", "+00:00"))
            now = datetime.now(timezone.utc)
            duration_sec = int((now - started).total_seconds())
        except (ValueError, TypeError):
            pass

    # Track git diff since task start
    diff_stats = _get_diff_stats(data.get("git_sha_start"))

    data["status"] = "done"
    data["completed"] = now_iso()
    if duration_sec is not None:
        data["duration_sec"] = duration_sec
    if args.summary:
        data["summary"] = args.summary
    if diff_stats:
        data["diff"] = diff_stats
    save_task(path, data)

    result = {"success": True, "id": args.id, "status": "done"}
    if duration_sec is not None:
        mins = duration_sec // 60
        result["duration"] = f"{mins}m" if mins > 0 else f"{duration_sec}s"
    if diff_stats:
        result["diff"] = diff_stats

    # Auto-consolidate learnings if config allows
    config = DEFAULT_CONFIG.copy()
    if CONFIG_FILE.exists():
        try:
            config.update(json.loads(CONFIG_FILE.read_text()))
        except json.JSONDecodeError:
            pass
    if config.get("auto_consolidate") and LEARNINGS_DIR.exists():
        learning_count = len(list(LEARNINGS_DIR.glob("*.json")))
        if learning_count >= 10:
            result["hint"] = "Run 'cc-flow consolidate' to promote patterns"

    print(json.dumps(result))


def _get_diff_stats(start_sha=None):
    """Get git diff stats since a commit SHA."""
    import subprocess as _sp
    if not start_sha:
        return None
    try:
        result = _sp.run(
            ["git", "diff", "--stat", start_sha, "HEAD"],
            capture_output=True, text=True, timeout=10,
        )
        if result.returncode != 0 or not result.stdout.strip():
            return None

        lines = result.stdout.strip().split("\n")
        # Last line: "N files changed, X insertions(+), Y deletions(-)"
        summary_line = lines[-1] if lines else ""
        files_changed = 0
        insertions = 0
        deletions = 0

        import re
        m = re.search(r"(\d+) files? changed", summary_line)
        if m:
            files_changed = int(m.group(1))
        m = re.search(r"(\d+) insertions?", summary_line)
        if m:
            insertions = int(m.group(1))
        m = re.search(r"(\d+) deletions?", summary_line)
        if m:
            deletions = int(m.group(1))

        return {
            "files_changed": files_changed,
            "insertions": insertions,
            "deletions": deletions,
            "total_lines": insertions + deletions,
        }
    except (OSError, _sp.TimeoutExpired):
        return None


def cmd_rollback(args):
    """Rollback a failed task to the git state when it was started."""
    import subprocess as _sp

    path = TASKS_SUBDIR / f"{args.id}.json"
    if not path.exists():
        _error(f"Task not found: {args.id}")

    data = safe_json_load(path)
    start_sha = data.get("git_sha_start")

    if not start_sha:
        _error(f"No git SHA recorded for {args.id}. Task was not started in a git repo.")

    if data["status"] not in ("in_progress", "blocked"):
        _error(f"Cannot rollback task with status: {data['status']}")

    # Show what will be rolled back
    diff_stats = _get_diff_stats(start_sha)
    if diff_stats and diff_stats["total_lines"] == 0:
        print(json.dumps({"success": True, "id": args.id, "action": "no_changes",
                          "message": "No changes to rollback"}))
        return

    if not getattr(args, "confirm", False):
        result = {
            "success": True,
            "id": args.id,
            "action": "preview",
            "sha": start_sha[:8],
            "diff": diff_stats,
            "message": f"Will reset to {start_sha[:8]}. Run with --confirm to execute.",
        }
        print(json.dumps(result))
        return

    # Execute rollback
    try:
        _sp.run(["git", "reset", "--hard", start_sha],
                capture_output=True, text=True, timeout=30, check=True)
    except (_sp.CalledProcessError, _sp.TimeoutExpired, OSError) as exc:
        _error(f"Rollback failed: {exc}")

    # Reset task to todo
    data["status"] = "todo"
    for field in ("started", "completed", "summary", "blocked_reason",
                  "blocked_at", "git_sha_start", "duration_sec", "diff"):
        data.pop(field, None)
    save_task(path, data)

    print(json.dumps({
        "success": True,
        "id": args.id,
        "action": "rolled_back",
        "sha": start_sha[:8],
        "diff": diff_stats,
    }))


def cmd_block(args):
    path = TASKS_SUBDIR / f"{args.id}.json"
    if not path.exists():
        print(json.dumps({"success": False, "error": f"Task not found: {args.id}"}))
        sys.exit(1)

    data = safe_json_load(path)
    data["status"] = "blocked"
    data["blocked_reason"] = args.reason
    data["blocked_at"] = now_iso()
    save_task(path, data)
    print(json.dumps({"success": True, "id": args.id, "status": "blocked"}))


def cmd_progress(args):
    tasks = all_tasks()
    epics = {}
    for f in sorted(EPICS_DIR.glob("*.md")):
        epics[f.stem] = []

    for t in tasks.values():
        epic = t.get("epic", "")
        if epic in epics:
            epics[epic].append(t)

    json_output = []
    for epic_id, epic_tasks in epics.items():
        if args.epic and epic_id != args.epic:
            continue
        total = len(epic_tasks)
        done = sum(1 for t in epic_tasks if t["status"] == "done")
        in_prog = sum(1 for t in epic_tasks if t["status"] == "in_progress")
        blocked = sum(1 for t in epic_tasks if t["status"] == "blocked")
        todo = total - done - in_prog - blocked
        pct = int(done / total * 100) if total > 0 else 0
        entry = {"epic": epic_id, "total": total, "done": done,
                 "in_progress": in_prog, "blocked": blocked, "todo": todo, "pct": pct}
        json_output.append(entry)

        if not getattr(args, "json", False):
            # Extract title from epic spec
            epic_spec = EPICS_DIR / f"{epic_id}.md"
            epic_title = ""
            if epic_spec.exists():
                first_line = epic_spec.read_text().split("\n", 1)[0]
                epic_title = first_line.lstrip("# ").replace("Epic:", "").strip()
            label = f"{epic_title}" if epic_title else epic_id
            if total == 0:
                print(f"{label}: no tasks")
            else:
                bar_len = 20
                filled = int(bar_len * done / total)
                bar = "█" * filled + "░" * (bar_len - filled)
                print(f"{label}: {bar} {pct}% ({done}/{total})")
                if in_prog:
                    print(f"  ◐ {in_prog} in progress")
                if blocked:
                    print(f"  ✗ {blocked} blocked")
                if todo:
                    print(f"  ○ {todo} todo")

    if getattr(args, "json", False):
        print(json.dumps({"success": True, "epics": json_output}))


def cmd_version(_args):
    """Print cc-flow version."""
    print(json.dumps({"success": True, "version": VERSION}))


def cmd_status(_args):
    """Global overview — epic counts, task counts, health."""
    tasks = all_tasks()
    epic_files = sorted(EPICS_DIR.glob("*.md"))
    total_tasks = len(tasks)
    done = sum(1 for t in tasks.values() if t["status"] == "done")
    in_prog = sum(1 for t in tasks.values() if t["status"] == "in_progress")
    blocked = sum(1 for t in tasks.values() if t["status"] == "blocked")
    todo = total_tasks - done - in_prog - blocked
    print(json.dumps({
        "success": True,
        "epics": len(epic_files),
        "tasks": total_tasks,
        "done": done,
        "in_progress": in_prog,
        "blocked": blocked,
        "todo": todo,
    }))


def cmd_next(args):
    """Smart next: pick highest-priority ready task."""
    tasks = all_tasks()
    ready = []
    for t in tasks.values():
        if args.epic and t.get("epic") != args.epic:
            continue
        if t["status"] != "todo":
            continue
        deps_done = all(
            tasks.get(d, {}).get("status") == "done"
            for d in t.get("depends_on", [])
        )
        if deps_done:
            ready.append(t)

    if not ready:
        # Check if there's in-progress work to resume
        in_prog = [t for t in tasks.values() if t["status"] == "in_progress"]
        if in_prog:
            t = in_prog[0]
            print(json.dumps({"success": True, "action": "resume", "id": t["id"], "title": t["title"]}))
        else:
            print(json.dumps({"success": True, "action": "none", "reason": "all done or blocked"}))
        return

    # Sort by priority field (lower = higher priority), then by id
    ready.sort(key=lambda t: (t.get("priority", 999), t["id"]))
    t = ready[0]
    print(json.dumps({"success": True, "action": "start", "id": t["id"], "title": t["title"]}))


def cmd_validate(args):
    """Validate epic/task structure — specs exist, deps valid, no cycles."""
    tasks = all_tasks()
    errors = []
    warnings = []

    # Check all epics have spec files
    for f in sorted(EPICS_DIR.glob("*.md")):
        epic_id = f.stem
        epic_tasks = [t for t in tasks.values() if t.get("epic") == epic_id]
        if not epic_tasks:
            warnings.append(f"Epic {epic_id} has no tasks")

    # Check all tasks have valid structure
    for tid, t in tasks.items():
        # Check epic exists
        epic_id = t.get("epic", "")
        epic_path = EPICS_DIR / f"{epic_id}.md"
        if not epic_path.exists():
            errors.append(f"Task {tid}: epic {epic_id} spec missing")

        # Check spec exists
        spec_path = TASKS_SUBDIR / f"{tid}.md"
        if not spec_path.exists():
            warnings.append(f"Task {tid}: spec file missing")

        # Check status valid
        if t.get("status") not in ("todo", "in_progress", "done", "blocked"):
            errors.append(f"Task {tid}: invalid status '{t.get('status')}'")

        # Check deps exist
        for dep in t.get("depends_on", []):
            if dep not in tasks:
                errors.append(f"Task {tid}: dependency {dep} not found")

    # Check for dependency cycles (DFS)
    def has_cycle(task_id, visited, rec_stack):
        visited.add(task_id)
        rec_stack.add(task_id)
        for dep in tasks.get(task_id, {}).get("depends_on", []):
            if dep not in visited:
                if has_cycle(dep, visited, rec_stack):
                    return True
            elif dep in rec_stack:
                errors.append(f"Dependency cycle detected involving {task_id} → {dep}")
                return True
        rec_stack.discard(task_id)
        return False

    visited, rec_stack = set(), set()
    for tid in tasks:
        if tid not in visited:
            has_cycle(tid, visited, rec_stack)

    valid = len(errors) == 0
    print(json.dumps({
        "success": valid,
        "valid": valid,
        "errors": errors,
        "warnings": warnings,
        "task_count": len(tasks),
    }))
    if not valid:
        sys.exit(1)


def cmd_epic_close(args):
    """Close epic — requires all tasks done."""
    epic_id = args.id
    epic_path = EPICS_DIR / f"{epic_id}.md"
    if not epic_path.exists():
        print(json.dumps({"success": False, "error": f"Epic not found: {epic_id}"}))
        sys.exit(1)

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
        print(json.dumps({"success": False, "error": f"Task not found: {args.id}"}))
        sys.exit(1)

    data = safe_json_load(path)
    data["status"] = "todo"
    for field in ("started", "completed", "summary", "blocked_reason", "blocked_at"):
        data.pop(field, None)
    save_task(path, data)
    print(json.dumps({"success": True, "id": args.id, "status": "todo"}))


def cmd_task_set_spec(args):
    """Update task spec from file."""
    task_id = args.id
    spec_path = TASKS_SUBDIR / f"{task_id}.md"
    json_path = TASKS_SUBDIR / f"{task_id}.json"

    if not json_path.exists():
        print(json.dumps({"success": False, "error": f"Task not found: {task_id}"}))
        sys.exit(1)

    src = Path(args.file)
    if not src.exists():
        print(json.dumps({"success": False, "error": f"File not found: {args.file}"}))
        sys.exit(1)

    spec_path.write_text(src.read_text())
    print(json.dumps({"success": True, "id": task_id, "spec": str(spec_path)}))


def cmd_epic_reset(args):
    """Reset all tasks in an epic to todo."""
    epic_id = args.id
    tasks = all_tasks()
    epic_tasks = [t for t in tasks.values() if t.get("epic") == epic_id]
    if not epic_tasks:
        print(json.dumps({"success": False, "error": f"No tasks found for: {epic_id}"}))
        sys.exit(1)

    reset_count = 0
    for t in epic_tasks:
        if t["status"] != "todo":
            t["status"] = "todo"
            for field in ("started", "completed", "summary", "blocked_reason", "blocked_at"):
                t.pop(field, None)
            save_task(TASKS_SUBDIR / f"{t['id']}.json", t)
            reset_count += 1

    print(json.dumps({"success": True, "epic": epic_id, "reset": reset_count}))


def cmd_scan(args):
    """Scan codebase for issues, generate improvement epic + tasks."""
    import subprocess

    findings = {"P1": [], "P2": [], "P3": [], "P4": []}

    # Ruff scan
    try:
        result = subprocess.run(
            ["ruff", "check", ".", "--output-format", "json"],
            capture_output=True, text=True, timeout=30,
        )
        if result.stdout.strip():
            issues = json.loads(result.stdout)
            by_rule = {}
            for i in issues:
                by_rule.setdefault(i.get("code", "?"), []).append(i)
            for rule, items in sorted(by_rule.items(), key=lambda x: -len(x[1]))[:10]:
                findings["P3"].append(f"Fix {len(items)}x ruff {rule}: {items[0].get('message', '')}")
    except (FileNotFoundError, subprocess.TimeoutExpired, json.JSONDecodeError):
        pass

    # Mypy scan
    try:
        result = subprocess.run(
            ["mypy", ".", "--no-error-summary"],
            capture_output=True, text=True, timeout=60,
        )
        for line in result.stdout.strip().split("\n")[:10]:
            if line.strip() and "error:" in line:
                findings["P2"].append(f"Fix mypy: {line.strip()}")
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    # Bandit scan
    try:
        result = subprocess.run(
            ["bandit", "-r", ".", "-f", "json", "-q"],
            capture_output=True, text=True, timeout=30,
        )
        if result.stdout.strip():
            data = json.loads(result.stdout)
            for r in data.get("results", [])[:10]:
                sev = r.get("issue_severity", "MEDIUM")
                priority = "P1" if sev in ("HIGH", "CRITICAL") else "P3"
                findings[priority].append(
                    f"[{sev}] {r.get('issue_text', '')} ({r.get('filename', '')}:{r.get('line_number', '')})"
                )
    except (FileNotFoundError, subprocess.TimeoutExpired, json.JSONDecodeError):
        pass

    # Count totals
    total = sum(len(v) for v in findings.values())

    if args.create_tasks and total > 0:
        # Auto-create epic + tasks
        cmd_init(argparse.Namespace())

        meta = load_meta()
        epic_num = meta["next_epic"]
        date_slug = datetime.now(timezone.utc).strftime("%Y%m%d")
        epic_id = f"epic-{epic_num}-scan-{date_slug}"
        meta["next_epic"] = epic_num + 1
        save_meta(meta)

        spec_lines = [f"# Epic: Code scan {date_slug}\n\n## Findings\n"]
        task_num = 0
        for priority in ("P1", "P2", "P3", "P4"):
            for finding in findings[priority]:
                task_num += 1
                task_id = f"{epic_id}.{task_num}"
                state = {
                    "id": task_id,
                    "epic": epic_id,
                    "title": f"[{priority}] {finding}",
                    "status": "todo",
                    "depends_on": [],
                    "priority": {"P1": 1, "P2": 2, "P3": 3, "P4": 4}[priority],
                    "created": now_iso(),
                }
                save_task(TASKS_SUBDIR / f"{task_id}.json", state)
                spec_path = TASKS_SUBDIR / f"{task_id}.md"
                spec_path.write_text(f"# Task: {finding}\n\n## Fix\n\n[Describe the fix]\n")
                spec_lines.append(f"- [{priority}] {finding}")

        epic_spec = EPICS_DIR / f"{epic_id}.md"
        epic_spec.write_text("\n".join(spec_lines) + "\n")

        print(json.dumps({
            "success": True,
            "epic": epic_id,
            "tasks_created": task_num,
            "findings": {k: len(v) for k, v in findings.items()},
        }))
    else:
        # Just report
        output = {"success": True, "total": total, "findings": {}}
        for priority in ("P1", "P2", "P3", "P4"):
            if findings[priority]:
                output["findings"][priority] = findings[priority]
        print(json.dumps(output))


LOG_HEADER = "timestamp\titeration\tmode\tarea\ttask_id\tdescription\tstatus\tfiles_changed\tdiff_lines\tduration_sec\tnotes\n"


def cmd_log(args):
    """Append entry to improvement-results.tsv or show recent entries."""
    if args.show:
        if not LOG_FILE.exists():
            print(json.dumps({"success": False, "error": "No log file found"}))
            sys.exit(1)
        lines = LOG_FILE.read_text().strip().split("\n")
        n = min(args.show, len(lines) - 1)  # Skip header
        entries = []
        for line in lines[-n:]:
            parts = line.split("\t")
            if len(parts) >= 6:
                entries.append({
                    "timestamp": parts[0], "iteration": parts[1], "mode": parts[2],
                    "task_id": parts[4], "status": parts[6] if len(parts) > 6 else "",
                })
        print(json.dumps({"success": True, "entries": entries, "total": len(lines) - 1}))
        return

    # Append mode
    if not LOG_FILE.exists():
        LOG_FILE.write_text(LOG_HEADER)

    row = "\t".join([
        now_iso(),
        str(args.iteration or ""),
        args.mode or "",
        args.area or "",
        args.task_id or "",
        args.description or "",
        args.status or "",
        str(args.files or ""),
        str(args.diff_lines or ""),
        str(args.duration or ""),
        args.notes or "",
    ])
    with open(LOG_FILE, "a") as f:
        f.write(row + "\n")
    print(json.dumps({"success": True, "logged": args.status}))


def cmd_summary(_args):
    """Print session summary from improvement-results.tsv."""
    if not LOG_FILE.exists():
        print("No improvement-results.tsv found.")
        return

    lines = LOG_FILE.read_text().strip().split("\n")[1:]  # Skip header
    kept = sum(1 for row in lines if "KEPT" in row)
    discarded = sum(1 for row in lines if "DISCARDED" in row)
    skipped = sum(1 for row in lines if "SKIPPED" in row)
    total = len(lines)
    pct = int(kept / total * 100) if total > 0 else 0

    print("## Autoimmune Summary")
    print("| Metric | Value |")
    print("|--------|-------|")
    print(f"| Iterations | {total} |")
    print(f"| Kept | {kept} ({pct}%) |")
    print(f"| Discarded | {discarded} |")
    print(f"| Skipped | {skipped} |")




def cmd_archive(_args):
    """Show completed/archived epics and tasks."""
    if not COMPLETED_DIR.exists():
        print(json.dumps({"success": True, "archived": [], "count": 0}))
        return

    archived_epics = []
    for f in sorted(COMPLETED_DIR.glob("*.md")):
        if "." not in f.stem.split("-", 2)[-1]:  # Epic md (no task dot notation)
            # Check if it looks like an epic (no dot in the id part)
            parts = f.stem.split(".")
            if len(parts) == 1:  # Epic file, not task
                epic_id = f.stem
                task_files = list(COMPLETED_DIR.glob(f"{epic_id}.*.json"))
                archived_epics.append({
                    "id": epic_id,
                    "tasks": len(task_files),
                })

    if not archived_epics:
        # Try listing all json files
        task_jsons = sorted(COMPLETED_DIR.glob("*.json"))
        tasks = []
        for f in task_jsons:
            d = safe_json_load(f, default=None)
            if not d or "id" not in d:
                continue
            tasks.append({"id": d["id"], "title": d.get("title", ""), "completed": d.get("completed", "")})
        print(json.dumps({"success": True, "tasks": tasks, "count": len(tasks)}))
    else:
        print(json.dumps({"success": True, "archived": archived_epics, "count": len(archived_epics)}))


def cmd_stats(_args):
    """Productivity stats from improvement-results.tsv and .tasks/ history."""
    stats = {"epics": {}, "totals": {"kept": 0, "discarded": 0, "skipped": 0}}

    # From TSV log
    if LOG_FILE.exists():
        lines = LOG_FILE.read_text().strip().split("\n")[1:]
        for line in lines:
            parts = line.split("\t")
            if len(parts) < 7:
                continue
            status = parts[6]
            if status == "KEPT":
                stats["totals"]["kept"] += 1
            elif status == "DISCARDED":
                stats["totals"]["discarded"] += 1
            elif status == "SKIPPED":
                stats["totals"]["skipped"] += 1

    # From .tasks/
    tasks = all_tasks()
    epic_stats = {}
    for t in tasks.values():
        epic = t.get("epic", "unknown")
        if epic not in epic_stats:
            epic_stats[epic] = {"total": 0, "done": 0, "todo": 0, "in_progress": 0, "blocked": 0}
        epic_stats[epic]["total"] += 1
        epic_stats[epic][t["status"]] = epic_stats[epic].get(t["status"], 0) + 1

    # Calculate velocity
    done_tasks = [t for t in tasks.values() if t.get("completed")]
    if len(done_tasks) >= 2:
        times = sorted(t["completed"] for t in done_tasks)
        first = datetime.fromisoformat(times[0].replace("Z", "+00:00"))
        last = datetime.fromisoformat(times[-1].replace("Z", "+00:00"))
        hours = max((last - first).total_seconds() / 3600, 0.1)
        velocity = len(done_tasks) / hours
        stats["velocity"] = f"{velocity:.1f} tasks/hour"
    else:
        stats["velocity"] = "insufficient data"

    total_attempts = stats["totals"]["kept"] + stats["totals"]["discarded"]
    success_rate = int(stats["totals"]["kept"] / total_attempts * 100) if total_attempts > 0 else 0

    print("## Productivity Stats")
    print("| Metric | Value |")
    print("|--------|-------|")
    print(f"| Active epics | {len(epic_stats)} |")
    print(f"| Total tasks | {len(tasks)} |")
    print(f"| Done | {sum(e['done'] for e in epic_stats.values())} |")
    print(f"| Velocity | {stats['velocity']} |")
    if total_attempts > 0:
        print(f"| Autoimmune kept | {stats['totals']['kept']} |")
        print(f"| Autoimmune discarded | {stats['totals']['discarded']} |")
        print(f"| Success rate | {success_rate}% |")


# ─── Router ───

ROUTE_TABLE = [
    # (keywords, command, team, description)
    (["new feature", "add feature", "implement", "build", "新功能", "加功能"],
     "/brainstorm", "feature-dev", "New feature → brainstorm first"),
    (["bug", "broken", "error", "fix", "crash", "报错", "故障", "修"],
     "/debug", "bug-fix", "Bug → systematic debugging"),
    (["review", "code review", "check code", "审查", "看看代码"],
     "/review", "review", "Code review"),
    (["refactor", "clean up", "simplify", "重构", "简化", "清理"],
     "/simplify", "refactor", "Refactoring"),
    (["test", "tdd", "write test", "写测试"],
     "/tdd", None, "Test-driven development"),
    (["deploy", "ship", "release", "上线", "部署", "发布"],
     "/commit", None, "Ship → commit and push"),
    (["plan", "design", "architecture", "规划", "设计", "架构"],
     "/plan", "feature-dev", "Planning"),
    (["slow", "performance", "optimize", "慢", "性能", "优化"],
     "/perf", None, "Performance optimization"),
    (["docs", "readme", "changelog", "文档"],
     "/docs", None, "Documentation"),
    (["scaffold", "new project", "init", "新项目", "创建项目"],
     "/scaffold", None, "New project setup"),
    (["improve", "autoimmune", "自动改进", "自动优化"],
     "/autoimmune", "autoimmune", "Autonomous improvement"),
    (["audit", "health", "ready", "体检", "审计"],
     "/audit", "audit", "Project health check"),
    (["task", "epic", "progress", "任务", "进度"],
     "/tasks", None, "Task management"),
    (["incident", "outage", "down", "事故", "宕机"],
     "/debug", "bug-fix", "Incident response (use incident skill)"),
    (["upgrade", "dependency", "依赖", "升级"],
     None, None, "Dependency upgrade (use dependency-upgrade skill)"),
]


def _load_route_stats():
    """Load route success/failure stats for adaptive confidence."""
    return safe_json_load(ROUTE_STATS_FILE, default={"commands": {}, "updated": ""})


def _save_route_stats(stats):
    stats["updated"] = now_iso()
    ROUTE_STATS_FILE.write_text(json.dumps(stats, indent=2) + "\n")


def cmd_route(args):
    """Analyze user intent and suggest the best command + team."""
    query = " ".join(args.query).lower() if args.query else ""

    if not query:
        _error("Provide a task description")

    # Check learnings for past similar tasks
    past_match = _search_learnings(query)

    # Load route stats for adaptive confidence
    route_stats = _load_route_stats()

    # Check promoted patterns for high-confidence matches
    patterns_dir = TASKS_DIR / "patterns"
    pattern_match = None
    if patterns_dir.exists():
        for f in patterns_dir.glob("*.json"):
            try:
                p = json.loads(f.read_text())
                pattern_words = set(p.get("task_pattern", "").split())
                query_words = set(query.split())
                overlap = len(pattern_words & query_words)
                if overlap >= 2 and p.get("success_rate", 0) >= 70:
                    pattern_match = {
                        "pattern": p.get("task_pattern"),
                        "approach": p.get("approach"),
                        "success_rate": p.get("success_rate"),
                        "occurrences": p.get("occurrences"),
                    }
                    break
            except (json.JSONDecodeError, KeyError):
                continue

    matches = []
    for keywords, command, team, desc in ROUTE_TABLE:
        score = sum(1 for kw in keywords if kw in query)
        if score > 0:
            matches.append({"score": score, "command": command, "team": team, "description": desc})

    matches.sort(key=lambda x: -x["score"])
    best = matches[0] if matches else None

    # Calculate routing confidence — combines keyword match, learnings, patterns, and history
    confidence = 0
    if best:
        confidence = min(best["score"] * 25, 80)
    if past_match and past_match.get("confidence", 0) > confidence:
        confidence = past_match["confidence"]
    if pattern_match and pattern_match.get("success_rate", 0) > confidence:
        confidence = pattern_match["success_rate"]

    # Boost/penalize based on historical route success rates
    suggested_cmd = best["command"] if best else "/brainstorm"
    cmd_stats = route_stats.get("commands", {}).get(suggested_cmd, {})
    if cmd_stats:
        total = cmd_stats.get("success", 0) + cmd_stats.get("failure", 0)
        if total >= 3:
            hist_rate = int(cmd_stats["success"] / total * 100)
            # Blend: 70% current confidence + 30% historical success rate
            confidence = int(confidence * 0.7 + hist_rate * 0.3)

    result = {
        "success": True,
        "query": query,
        "confidence": min(confidence, 99),
        "suggestion": {
            "command": suggested_cmd,
            "team": best.get("team") if best else None,
            "reason": best["description"] if best else "Default: start with brainstorming",
        },
    }
    if past_match:
        result["past_learning"] = past_match
    if pattern_match:
        result["promoted_pattern"] = pattern_match
    if cmd_stats:
        s = cmd_stats.get("success", 0)
        f = cmd_stats.get("failure", 0)
        result["route_history"] = {"uses": s + f, "success_rate": int(s / (s + f) * 100) if (s + f) > 0 else 0}
    if matches and len(matches) > 1:
        result["alternatives"] = [
            {"command": m["command"], "reason": m["description"]}
            for m in matches[1:3]
        ]

    print(json.dumps(result))


# ─── Learning Loop ───

def cmd_learn(args):
    """Record a learning from the current session for future routing."""
    LEARNINGS_DIR.mkdir(parents=True, exist_ok=True)

    learning = {
        "timestamp": now_iso(),
        "task": args.task,
        "outcome": args.outcome,
        "approach": args.approach,
        "lesson": args.lesson,
        "score": args.score,
    }
    if getattr(args, "used_command", None):
        learning["command"] = args.used_command

    # Filename from timestamp + microseconds for uniqueness
    fname = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S-%f") + ".json"
    path = LEARNINGS_DIR / fname
    path.write_text(json.dumps(learning, indent=2) + "\n")

    # Update route stats if command was recorded
    if learning.get("command"):
        stats = _load_route_stats()
        cmd = learning["command"]
        if cmd not in stats["commands"]:
            stats["commands"][cmd] = {"success": 0, "failure": 0}
        if args.outcome == "success":
            stats["commands"][cmd]["success"] += 1
        elif args.outcome == "failed":
            stats["commands"][cmd]["failure"] += 1
        else:  # partial
            stats["commands"][cmd]["success"] += 0.5
        _save_route_stats(stats)

    print(json.dumps({"success": True, "saved": str(path)}))


def cmd_learnings(args):
    """List or search past learnings."""
    if not LEARNINGS_DIR.exists():
        print(json.dumps({"success": True, "learnings": [], "count": 0}))
        return

    learnings = []
    for f in sorted(LEARNINGS_DIR.glob("*.json")):
        d = safe_json_load(f, default=None)
        if d:
            learnings.append(d)

    if args.search:
        query = args.search.lower()
        learnings = [entry for entry in learnings if
                     query in entry.get("task", "").lower() or
                     query in entry.get("lesson", "").lower() or
                     query in entry.get("approach", "").lower()]

    # Show recent N
    n = args.last or 10
    recent = learnings[-n:]

    print(json.dumps({"success": True, "learnings": recent, "count": len(learnings)}))


def _search_learnings(query):
    """Search learnings — uses Morph Rerank if available, falls back to keyword overlap."""
    if not LEARNINGS_DIR.exists():
        return None

    # Collect all learnings
    learnings = []
    for f in LEARNINGS_DIR.glob("*.json"):
        d = safe_json_load(f, default=None)
        if d and d.get("score", 0) >= 2:
            learnings.append(d)

    if not learnings:
        return None

    # Try Morph Rerank for semantic matching
    morph_client = _get_morph_client()
    if morph_client and len(learnings) >= 2:
        try:
            documents = [
                f"{d.get('task', '')} | {d.get('lesson', '')} | {d.get('approach', '')}"
                for d in learnings
            ]
            ranked = morph_client.rerank(query, documents, top_n=3)
            if ranked and ranked[0].get("relevance_score", 0) > 0.1:
                best = learnings[ranked[0]["index"]]
                confidence = min(int(ranked[0]["relevance_score"] * 100), 99)
                return {
                    "task": best.get("task"),
                    "approach": best.get("approach"),
                    "lesson": best.get("lesson"),
                    "score": best.get("score"),
                    "confidence": confidence,
                    "alternatives": len(ranked) - 1,
                    "engine": "morph-rerank",
                }
        except Exception:
            pass  # Fall through to keyword matching

    # Fallback: keyword overlap scoring
    query_lower = query.lower()
    candidates = []
    for d in learnings:
        task = d.get("task", "").lower()
        lesson = d.get("lesson", "").lower()
        approach = d.get("approach", "").lower()
        words = set(query_lower.split())
        total_score = (len(words & set(task.split())) * 3
                       + len(words & set(lesson.split())) * 2
                       + len(words & set(approach.split())))
        weighted = total_score * (d.get("score", 3) / 5.0)
        if weighted > 0:
            candidates.append((weighted, d))

    if not candidates:
        return None

    candidates.sort(key=lambda x: -x[0])
    best_weight, best_d = candidates[0]

    if best_weight < 2:
        return None

    return {
        "task": best_d.get("task"),
        "approach": best_d.get("approach"),
        "lesson": best_d.get("lesson"),
        "score": best_d.get("score"),
        "confidence": min(int(best_weight * 20), 99),
        "alternatives": len(candidates) - 1,
        "engine": "keyword",
    }


def cmd_consolidate(_args):
    """Consolidate learnings: merge similar entries, promote high-score patterns."""
    if not LEARNINGS_DIR.exists():
        print(json.dumps({"success": True, "consolidated": 0, "promoted": 0}))
        return

    learnings = []
    for f in sorted(LEARNINGS_DIR.glob("*.json")):
        d = safe_json_load(f, default=None)
        if not d:
            continue
        d["_path"] = str(f)
        learnings.append(d)

    if len(learnings) < 2:
        print(json.dumps({"success": True, "consolidated": 0, "promoted": 0}))
        return

    # Group by task similarity
    groups = {}
    for entry in learnings:
        task_key = " ".join(sorted(entry.get("task", "").lower().split()[:3]))
        groups.setdefault(task_key, []).append(entry)

    consolidated = 0
    promoted = 0
    promoted_dir = TASKS_DIR / "patterns"
    promoted_dir.mkdir(parents=True, exist_ok=True)

    for key, group in groups.items():
        if len(group) < 2:
            continue

        # Average score for this pattern
        avg_score = sum(e.get("score", 3) for e in group) / len(group)
        success_count = sum(1 for e in group if e.get("outcome") == "success")
        success_rate = int(success_count / len(group) * 100)

        # Promote patterns with high avg score and multiple successes
        if avg_score >= 4 and success_count >= 2:
            best = max(group, key=lambda e: e.get("score", 0))
            pattern = {
                "task_pattern": key,
                "approach": best.get("approach"),
                "lesson": best.get("lesson"),
                "avg_score": round(avg_score, 1),
                "success_rate": success_rate,
                "occurrences": len(group),
                "promoted_at": now_iso(),
            }
            fname = key.replace(" ", "-")[:30] + ".json"
            (promoted_dir / fname).write_text(json.dumps(pattern, indent=2) + "\n")
            promoted += 1

        # Keep only the best entry per group, remove duplicates
        if len(group) > 3:
            group.sort(key=lambda e: -e.get("score", 0))
            for entry in group[3:]:
                Path(entry["_path"]).unlink(missing_ok=True)
                consolidated += 1

    print(json.dumps({
        "success": True,
        "consolidated": consolidated,
        "promoted": promoted,
        "total_learnings": len(learnings) - consolidated,
        "patterns": len(list(promoted_dir.glob("*.json"))),
    }))


# ─── Auto (integrated autoimmune) ───


def cmd_auto(args):
    """Integrated autoimmune loop using cc-flow task system."""
    mode = getattr(args, "auto_cmd", None)
    if mode == "scan":
        _auto_scan(args)
    elif mode == "run":
        _auto_run(args)
    elif mode == "test":
        _auto_test(args)
    elif mode == "full":
        print("## Mode: Full (scan → run → test)")
        _auto_scan(args)
        _auto_run(args)
        _auto_test(args)
    elif mode == "status":
        _auto_status(args)
    else:
        print(json.dumps({"success": False, "error": "Usage: cc-flow auto [scan|run|test|full|status]"}))
        sys.exit(1)


def _auto_scan(args):
    """Mode D: scan codebase, create epic + tasks."""
    print("## Auto Scan: detecting issues...")
    # Use existing scan with --create-tasks
    scan_args = argparse.Namespace(create_tasks=True)
    cmd_scan(scan_args)


def _auto_run(args):
    """Mode A: pick tasks, implement, verify, mark done/discarded."""
    epic_filter = getattr(args, "epic", "") or ""

    # Find the latest scan epic if no filter
    if not epic_filter:
        tasks = all_tasks()
        scan_epics = [f.stem for f in sorted(EPICS_DIR.glob("epic-*-scan-*.md"))]
        if scan_epics:
            epic_filter = scan_epics[-1]

    if not epic_filter:
        # Fall back to any epic with todo tasks
        for f in sorted(EPICS_DIR.glob("*.md"), reverse=True):
            epic_tasks = [t for t in all_tasks().values() if t.get("epic") == f.stem and t["status"] == "todo"]
            if epic_tasks:
                epic_filter = f.stem
                break

    if not epic_filter:
        print(json.dumps({"success": True, "action": "none", "reason": "No tasks to work on. Run: cc-flow auto scan"}))
        return

    max_iterations = getattr(args, "max", 0) or 20
    iteration = 0
    kept = 0
    discarded = 0

    print(f"## Auto Run: epic={epic_filter}, max={max_iterations}")

    while iteration < max_iterations:
        # Find next ready task
        tasks = all_tasks()
        ready = []
        for t in tasks.values():
            if t.get("epic") != epic_filter:
                continue
            if t["status"] != "todo":
                continue
            deps_done = all(tasks.get(d, {}).get("status") == "done" for d in t.get("depends_on", []))
            if deps_done:
                ready.append(t)

        if not ready:
            print(f"\n✅ All tasks done or blocked. Iterations: {iteration}, kept: {kept}, discarded: {discarded}")
            break

        ready.sort(key=lambda t: (t.get("priority", 999), t["id"]))
        task = ready[0]
        task_id = task["id"]
        iteration += 1

        print(f"\n--- Iteration {iteration}: {task_id} — {task['title']} ---")

        # Start task
        task["status"] = "in_progress"
        task["started"] = now_iso()
        save_task(TASKS_SUBDIR / f"{task_id}.json", task)

        # Determine team based on task content
        team_rec = _recommend_team(task)

        # Read spec content for context
        spec_path = TASKS_SUBDIR / f"{task_id}.md"
        spec_content = spec_path.read_text().strip() if spec_path.exists() else ""

        # Output structured instruction for Claude
        print(json.dumps({
            "action": "implement",
            "task_id": task_id,
            "title": task["title"],
            "size": task.get("size", "M"),
            "spec": str(spec_path),
            "spec_preview": spec_content[:200] if spec_content else "",
            "team": team_rec,
            "instruction": (
                f"Execute this task using the {team_rec['template']} team pattern:\n"
                f"1. {team_rec['steps'][0]}\n"
                f"2. {team_rec['steps'][1]}\n"
                f"3. {team_rec['steps'][2]}\n"
                f"Max diff: {team_rec['max_diff']} lines. Verify before marking done."
            ),
            "morph_available": _get_morph_client() is not None,
            "morph_hint": "Use morph edit_file (MCP) or MorphClient.apply_file() for fast code edits. Use morph codebase_search for exploration.",
        }))

        # Return control to Claude for implementation
        break

    if iteration >= max_iterations:
        print(f"\n⏹ Max iterations ({max_iterations}) reached. Kept: {kept}, Discarded: {discarded}")


def _auto_test(args):
    """Mode B: auto-fix lint/type/test errors."""
    import subprocess as sp

    print("## Auto Test: fixing lint + type + test errors...")

    # Phase B1: ruff auto-fix
    result = sp.run(["ruff", "check", ".", "--fix"], capture_output=True, text=True)
    if result.returncode == 0:
        print("B1 ruff: clean (or auto-fixed)")
    else:
        print(f"B1 ruff: {result.stdout[:200]}")

    # Phase B2: Check for remaining issues
    result = sp.run(["ruff", "check", "."], capture_output=True, text=True)
    remaining = result.stdout.strip().count("\n") + 1 if result.stdout.strip() else 0
    print(f"B2 remaining ruff issues: {remaining}")

    # Note: mypy and pytest fixes require Claude's reasoning — print instructions
    print(json.dumps({
        "action": "fix_remaining",
        "instruction": "Run mypy and pytest. Fix any errors with minimal changes. Verify after each fix.",
    }))


def _auto_status(args):
    """Show autoimmune session status from cc-flow data."""
    tasks = all_tasks()
    total = len(tasks)
    done = sum(1 for t in tasks.values() if t["status"] == "done")
    in_prog = sum(1 for t in tasks.values() if t["status"] == "in_progress")
    blocked = sum(1 for t in tasks.values() if t["status"] == "blocked")
    todo = total - done - in_prog - blocked

    # Check log
    log_entries = 0
    kept = 0
    disc = 0
    if LOG_FILE.exists():
        lines = LOG_FILE.read_text().strip().split("\n")[1:]
        log_entries = len(lines)
        kept = sum(1 for row in lines if "KEPT" in row)
        disc = sum(1 for row in lines if "DISCARDED" in row)

    print("## Auto Status")
    print("| Metric | Value |")
    print("|--------|-------|")
    print(f"| Tasks total | {total} |")
    print(f"| Done | {done} |")
    print(f"| In progress | {in_prog} |")
    print(f"| Blocked | {blocked} |")
    print(f"| Todo | {todo} |")
    if log_entries > 0:
        pct = int(kept / (kept + disc) * 100) if (kept + disc) > 0 else 0
        print(f"| Log entries | {log_entries} |")
        print(f"| Kept | {kept} ({pct}%) |")
        print(f"| Discarded | {disc} |")


TEAM_PATTERNS = [
    {
        "keywords": ["security", "bandit", "injection", "xss", "csrf", "auth", "secret", "vulnerability"],
        "template": "security-fix",
        "agents": ["researcher", "security-reviewer", "build-fixer"],
        "steps": [
            "Dispatch researcher: investigate the security issue, find affected code",
            "Dispatch security-reviewer: verify the vulnerability and suggest fix",
            "Apply minimal fix, run bandit to confirm resolved",
        ],
        "max_diff": 30,
    },
    {
        "keywords": ["type", "mypy", "annotation", "hint", "typing"],
        "template": "type-fix",
        "agents": ["build-fixer"],
        "steps": [
            "Read the mypy error message carefully",
            "Add type annotation or fix type mismatch (minimal change)",
            "Run mypy to verify the error is resolved",
        ],
        "max_diff": 20,
    },
    {
        "keywords": ["lint", "ruff", "unused", "import", "F401", "F841", "E741"],
        "template": "lint-fix",
        "agents": ["refactor-cleaner"],
        "steps": [
            "Run ruff check to see the exact violation",
            "Apply minimal fix (remove unused import, rename variable, etc.)",
            "Run ruff check to verify clean",
        ],
        "max_diff": 10,
    },
    {
        "keywords": ["test", "pytest", "failing", "assert", "fixture"],
        "template": "test-fix",
        "agents": ["researcher", "build-fixer"],
        "steps": [
            "Dispatch researcher: read the failing test + code under test",
            "Determine if it's a test bug or code bug",
            "Fix minimally, run pytest to verify green",
        ],
        "max_diff": 30,
    },
    {
        "keywords": ["refactor", "extract", "duplicate", "simplify", "complexity", "dead code"],
        "template": "refactor",
        "agents": ["researcher", "refactor-cleaner", "code-reviewer"],
        "steps": [
            "Dispatch researcher: map all usages and dependents",
            "Dispatch refactor-cleaner: apply the refactoring",
            "Dispatch code-reviewer: verify behavior preserved",
        ],
        "max_diff": 50,
    },
    {
        "keywords": ["doc", "docstring", "readme", "comment"],
        "template": "docs",
        "agents": ["refactor-cleaner"],
        "steps": [
            "Read the code to understand what it does",
            "Add/update documentation (docstring, comment, README)",
            "Verify no code changes, only docs",
        ],
        "max_diff": 30,
    },
]

DEFAULT_TEAM = {
    "template": "general-fix",
    "agents": ["researcher", "build-fixer"],
    "steps": [
        "Dispatch researcher: understand the issue and affected code",
        "Apply minimal fix (< 50 lines diff)",
        "Verify with lint + tests",
    ],
    "max_diff": 50,
}


def _recommend_team(task):
    """Recommend a team template based on task title/content keywords."""
    title_lower = task.get("title", "").lower()

    for pattern in TEAM_PATTERNS:
        score = sum(1 for kw in pattern["keywords"] if kw in title_lower)
        if score > 0:
            return {
                "template": pattern["template"],
                "agents": pattern["agents"],
                "steps": pattern["steps"],
                "max_diff": pattern["max_diff"],
                "match_score": score,
            }

    return {
        "template": DEFAULT_TEAM["template"],
        "agents": DEFAULT_TEAM["agents"],
        "steps": DEFAULT_TEAM["steps"],
        "max_diff": DEFAULT_TEAM["max_diff"],
        "match_score": 0,
    }


def cmd_config(args):
    """Manage cc-flow configuration."""
    config = DEFAULT_CONFIG.copy()
    if CONFIG_FILE.exists():
        config.update(safe_json_load(CONFIG_FILE, default={}))

    if args.key and args.value:
        # Set a config value
        # Auto-convert types
        val = args.value
        if val.lower() in ("true", "false"):
            val = val.lower() == "true"
        elif val.isdigit():
            val = int(val)
        config[args.key] = val
        CONFIG_FILE.write_text(json.dumps(config, indent=2) + "\n")
        print(json.dumps({"success": True, "key": args.key, "value": val}))
    elif args.key:
        # Get a config value
        print(json.dumps({"success": True, "key": args.key, "value": config.get(args.key)}))
    else:
        # Show all config
        print(json.dumps({"success": True, "config": config}))


def cmd_history(_args):
    """Show task completion timeline with velocity trends."""
    tasks = all_tasks()

    # Include archived tasks
    archived = []
    if COMPLETED_DIR.exists():
        for f in COMPLETED_DIR.glob("*.json"):
            try:
                archived.append(json.loads(f.read_text()))
            except json.JSONDecodeError:
                continue

    all_done = [t for t in list(tasks.values()) + archived if t.get("completed")]
    all_done.sort(key=lambda t: t.get("completed", ""))

    if not all_done:
        print(json.dumps({"success": True, "entries": [], "count": 0}))
        return

    # Group by date
    by_date = {}
    for t in all_done:
        date = t["completed"][:10]
        by_date.setdefault(date, []).append(t)

    # Calculate rolling velocity (tasks/day over last 7 entries)
    entries = []
    dates = sorted(by_date.keys())
    for date in dates:
        tasks_done = by_date[date]
        entries.append({
            "date": date,
            "count": len(tasks_done),
            "tasks": [{"id": t["id"], "title": t.get("title", "")} for t in tasks_done],
        })

    # Overall stats
    if len(dates) >= 2:
        first = datetime.fromisoformat(dates[0])
        last = datetime.fromisoformat(dates[-1])
        days = max((last - first).days, 1)
        daily_velocity = len(all_done) / days
    else:
        daily_velocity = len(all_done)

    print(json.dumps({
        "success": True,
        "entries": entries[-20:],  # Last 20 days
        "count": len(all_done),
        "daily_velocity": round(daily_velocity, 1),
        "date_range": f"{dates[0]} → {dates[-1]}" if len(dates) >= 2 else dates[0],
    }))


def cmd_dep_add(args):
    """Add dependency to existing task."""
    path = TASKS_SUBDIR / f"{args.id}.json"
    if not path.exists():
        print(json.dumps({"success": False, "error": f"Task not found: {args.id}"}))
        sys.exit(1)

    dep_path = TASKS_SUBDIR / f"{args.dep}.json"
    if not dep_path.exists():
        print(json.dumps({"success": False, "error": f"Dependency not found: {args.dep}"}))
        sys.exit(1)

    data = safe_json_load(path)
    deps = data.get("depends_on", [])
    if args.dep not in deps:
        deps.append(args.dep)
        data["depends_on"] = deps
        save_task(path, data)
    print(json.dumps({"success": True, "id": args.id, "depends_on": deps}))


def cmd_session(args):
    """Save or restore session state."""
    import subprocess as _sp

    mode = getattr(args, "session_cmd", None)
    SESSION_DIR.mkdir(parents=True, exist_ok=True)

    if mode == "save":
        # Gather comprehensive session state
        tasks = all_tasks()
        in_prog = [t for t in tasks.values() if t["status"] == "in_progress"]
        done_count = sum(1 for t in tasks.values() if t["status"] == "done")
        learn_count = len(list(LEARNINGS_DIR.glob("*.json"))) if LEARNINGS_DIR.exists() else 0

        # Git state
        try:
            git_sha = _sp.run(["git", "rev-parse", "HEAD"],
                              capture_output=True, text=True, timeout=5).stdout.strip()
            git_branch = _sp.run(["git", "branch", "--show-current"],
                                 capture_output=True, text=True, timeout=5).stdout.strip()
            git_dirty = _sp.run(["git", "status", "--porcelain"],
                                capture_output=True, text=True, timeout=5).stdout.strip()
        except (OSError, _sp.TimeoutExpired):
            git_sha = git_branch = git_dirty = ""

        # Recent learnings
        recent_learnings = []
        if LEARNINGS_DIR.exists():
            for f in sorted(LEARNINGS_DIR.glob("*.json"))[-3:]:
                d = safe_json_load(f, default=None)
                if d:
                    recent_learnings.append({
                        "task": d.get("task", ""),
                        "lesson": d.get("lesson", ""),
                    })

        name = getattr(args, "name", "") or datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        session = {
            "name": name,
            "timestamp": now_iso(),
            "git_sha": git_sha,
            "git_branch": git_branch,
            "git_dirty": bool(git_dirty),
            "tasks_total": len(tasks),
            "tasks_done": done_count,
            "in_progress": [{"id": t["id"], "title": t.get("title", "")} for t in in_prog],
            "learnings_count": learn_count,
            "recent_learnings": recent_learnings,
            "notes": getattr(args, "notes", "") or "",
        }

        path = SESSION_DIR / f"{name}.json"
        path.write_text(json.dumps(session, indent=2) + "\n")
        print(json.dumps({"success": True, "session": name, "path": str(path)}))

    elif mode == "restore":
        name = getattr(args, "name", "latest")
        if name == "latest":
            files = sorted(SESSION_DIR.glob("*.json"))
            if not files:
                _error("No sessions found")
            path = files[-1]
        else:
            path = SESSION_DIR / f"{name}.json"

        if not path.exists():
            _error(f"Session not found: {name}")

        data = safe_json_load(path)

        print(f"## Session: {data.get('name', '?')}")
        print(f"Saved: {data.get('timestamp', '?')}")
        print(f"Branch: {data.get('git_branch', '?')} @ {data.get('git_sha', '?')[:8]}")
        if data.get("git_dirty"):
            print("WARNING: Had uncommitted changes when saved")
        print(f"Progress: {data.get('tasks_done', 0)}/{data.get('tasks_total', 0)} tasks done")

        if data.get("in_progress"):
            print("\n### Resume These Tasks:")
            for t in data["in_progress"]:
                print(f"  - cc-flow start {t['id']} — {t['title']}")

        if data.get("recent_learnings"):
            print("\n### Recent Learnings:")
            for entry in data["recent_learnings"]:
                print(f"  - {entry['task']}: {entry['lesson']}")

        if data.get("notes"):
            print(f"\n### Notes:\n{data['notes']}")

        print("\n### Next Steps:")
        print("  1. `cc-flow dashboard` — see current state")
        print("  2. `cc-flow next` — pick next task")

    elif mode == "list":
        sessions = []
        for f in sorted(SESSION_DIR.glob("*.json")):
            d = safe_json_load(f, default=None)
            if d:
                sessions.append({
                    "name": d.get("name", f.stem),
                    "timestamp": d.get("timestamp", ""),
                    "done": d.get("tasks_done", 0),
                    "total": d.get("tasks_total", 0),
                    "branch": d.get("git_branch", ""),
                })
        print(json.dumps({"success": True, "sessions": sessions, "count": len(sessions)}))

    else:
        _error("Usage: cc-flow session [save|restore|list]")


def cmd_search(args):
    """Semantic code search via Morph API, with grep fallback and optional rerank."""
    import subprocess as _sp

    query = " ".join(args.query) if args.query else ""
    if not query:
        _error("Provide a search query")

    search_dir = getattr(args, "dir", ".") or "."
    fmt = getattr(args, "format", "text") or "text"
    do_rerank = getattr(args, "rerank", False)

    # Try Morph Python client first
    client = _get_morph_client()
    if client:
        try:
            result = client.search(query, search_dir)
            if result:
                if fmt == "json":
                    print(json.dumps({"success": True, "engine": "morph-python", "query": query, "results": result}))
                else:
                    print(f"## Search: {query} (morph semantic)\n")
                    print(result if isinstance(result, str) else json.dumps(result, indent=2))
                return
        except Exception:
            pass  # Fall through to grep

    # Fallback to grep
    try:
        result = _sp.run(
            ["grep", "-rn", "--include=*.py", "--include=*.ts", "--include=*.js",
             "--include=*.go", "--include=*.rs", "--include=*.md",
             "-i", query, search_dir],
            capture_output=True, text=True, timeout=15,
        )
        lines = [ln for ln in result.stdout.strip().split("\n") if ln.strip()][:30]

        # Rerank grep results with Morph if requested and available
        if do_rerank and lines and client:
            try:
                ranked = client.rerank(query, lines, top_n=min(10, len(lines)))
                lines = [r["document"] for r in ranked]
                engine = "grep+rerank"
            except Exception:
                engine = "grep-fallback"
        else:
            engine = "grep-fallback"

        if fmt == "json":
            print(json.dumps({"success": True, "engine": engine, "query": query,
                              "results": lines, "count": len(lines)}))
        else:
            print(f"## Search: {query} ({engine})\n")
            for line in lines:
                if line.strip():
                    print(f"  {line}")
    except (_sp.TimeoutExpired, OSError):
        _error("Search failed")


def cmd_compact(args):
    """Compress text via Morph API (Python)."""
    client = _get_morph_client()
    if not client:
        _error("MORPH_API_KEY not set. Get one at https://morphllm.com/dashboard/api-keys")

    ratio = float(getattr(args, "ratio", "0.3") or "0.3")
    input_file = getattr(args, "file", "") or ""

    if input_file:
        if not Path(input_file).exists():
            _error(f"File not found: {input_file}")
        content = Path(input_file).read_text()
    else:
        import select
        if select.select([sys.stdin], [], [], 0.1)[0]:
            content = sys.stdin.read()
        else:
            _error("Provide input via --file or stdin: cat file.txt | cc-flow compact")

    try:
        output = client.compact(content, ratio)
        original_len = len(content)
        compact_len = len(output)
        savings = int((1 - compact_len / original_len) * 100) if original_len > 0 else 0
        print(json.dumps({
            "success": True, "original_chars": original_len,
            "compact_chars": compact_len, "savings": f"{savings}%",
        }))
        if getattr(args, "output", ""):
            Path(args.output).write_text(output)
            print(f"Written to {args.output}")
        else:
            print(output)
    except Exception as exc:
        _error(f"compact failed: {exc}")


def cmd_github_search(args):
    """Search GitHub repos — uses Morph Embedding + Rerank (Python)."""
    import subprocess as _sp

    query = " ".join(args.query) if args.query else ""
    if not query:
        _error("Provide a search query")

    repo = getattr(args, "repo", "") or ""
    url = getattr(args, "url", "") or ""

    if not repo and not url:
        _error("Provide --repo owner/repo or --url github-url")

    # Use gh CLI to search GitHub (no morph node dependency needed)
    target = repo or url.replace("https://github.com/", "").rstrip("/")
    try:
        result = _sp.run(
            ["gh", "search", "code", query, "--repo", target, "--json", "repository,path,textMatches", "-L", "10"],
            capture_output=True, text=True, timeout=30,
        )
        if result.returncode == 0 and result.stdout.strip():
            data = json.loads(result.stdout)
            print(f"## GitHub Search: {query} in {target}\n")
            for item in data:
                path = item.get("path", "")
                repo_name = item.get("repository", {}).get("nameWithOwner", "")
                print(f"  {repo_name}/{path}")
                for match in item.get("textMatches", [])[:2]:
                    fragment = match.get("fragment", "")[:100]
                    print(f"    > {fragment}")
            print(f"\n  {len(data)} results found")
        else:
            _error(f"gh search failed: {result.stderr[:200]}")
    except (OSError, _sp.TimeoutExpired) as exc:
        _error(f"GitHub search error: {exc}")


def cmd_dashboard(args):
    """One-screen overview: epics, velocity, health, learnings. Use --json for machine-readable."""
    if getattr(args, "json", False):
        cmd_status(args)
        return
    tasks = all_tasks()
    total = len(tasks)
    done = sum(1 for t in tasks.values() if t["status"] == "done")
    in_prog = sum(1 for t in tasks.values() if t["status"] == "in_progress")
    blocked = sum(1 for t in tasks.values() if t["status"] == "blocked")
    todo = total - done - in_prog - blocked

    # Header
    print("╔══════════════════════════════════════════╗")
    print(f"║  cc-flow Dashboard  (v{VERSION})          ║")
    print("╠══════════════════════════════════════════╣")

    # Global stats
    pct = int(done / total * 100) if total > 0 else 0
    bar_len = 20
    filled = int(bar_len * done / total) if total > 0 else 0
    bar = "█" * filled + "░" * (bar_len - filled)
    print(f"║  Progress: {bar} {pct:>3}%  ║")
    print(f"║  ● {done} done  ◐ {in_prog} active  ○ {todo} todo  ✗ {blocked} blocked ║")

    # Velocity
    done_tasks = [t for t in tasks.values() if t.get("completed")]
    if len(done_tasks) >= 2:
        times = sorted(t["completed"] for t in done_tasks)
        first = datetime.fromisoformat(times[0].replace("Z", "+00:00"))
        last = datetime.fromisoformat(times[-1].replace("Z", "+00:00"))
        hours = max((last - first).total_seconds() / 3600, 0.1)
        velocity = len(done_tasks) / hours
        print(f"║  Velocity: {velocity:.1f} tasks/hour                  ║")
    else:
        print("║  Velocity: —                              ║")

    print("╠══════════════════════════════════════════╣")

    # Epic summary
    epic_files = sorted(EPICS_DIR.glob("*.md")) if EPICS_DIR.exists() else []
    if epic_files:
        print("║  Epics:                                   ║")
        for f in epic_files[:5]:
            epic_id = f.stem
            epic_tasks = [t for t in tasks.values() if t.get("epic") == epic_id]
            e_done = sum(1 for t in epic_tasks if t["status"] == "done")
            e_total = len(epic_tasks)
            # Title
            first_line = f.read_text().split("\n", 1)[0]
            title = first_line.lstrip("# ").replace("Epic:", "").strip()[:25]
            e_pct = int(e_done / e_total * 100) if e_total > 0 else 0
            mini_bar = "█" * (e_pct // 10) + "░" * (10 - e_pct // 10)
            print(f"║    {mini_bar} {e_pct:>3}% {title:<25} ║")
        if len(epic_files) > 5:
            print(f"║    ... +{len(epic_files) - 5} more                          ║")
    else:
        print("║  No epics yet. Run: cc-flow epic create   ║")

    print("╠══════════════════════════════════════════╣")

    # Learnings & patterns
    learn_count = len(list(LEARNINGS_DIR.glob("*.json"))) if LEARNINGS_DIR.exists() else 0
    patterns_dir = TASKS_DIR / "patterns"
    pattern_count = len(list(patterns_dir.glob("*.json"))) if patterns_dir.exists() else 0
    route_stats = _load_route_stats()
    total_routes = sum(
        v.get("success", 0) + v.get("failure", 0)
        for v in route_stats.get("commands", {}).values()
    )

    print(f"║  Learning: {learn_count} entries, {pattern_count} patterns         ║")
    if total_routes > 0:
        total_success = sum(v.get("success", 0) for v in route_stats.get("commands", {}).values())
        rate = int(total_success / total_routes * 100) if total_routes > 0 else 0
        print(f"║  Routing:  {total_routes} routes, {rate}% success rate      ║")
    else:
        print("║  Routing:  no data yet                    ║")

    # Autoimmune log
    if LOG_FILE.exists():
        lines = LOG_FILE.read_text().strip().split("\n")[1:]
        kept = sum(1 for row in lines if "KEPT" in row)
        disc = sum(1 for row in lines if "DISCARDED" in row)
        ai_total = kept + disc
        if ai_total > 0:
            ai_rate = int(kept / ai_total * 100)
            print(f"║  Autoimmune: {ai_total} runs, {ai_rate}% success         ║")

    print("╚══════════════════════════════════════════╝")

    # Next action suggestion
    if blocked > 0:
        print(f"\n  ⚠ {blocked} blocked task(s). Run: cc-flow tasks --status blocked")
    elif in_prog > 0:
        ip = next(t for t in tasks.values() if t["status"] == "in_progress")
        print(f"\n  → Resume: {ip['id']} — {ip['title']}")
    elif todo > 0:
        # Find next ready
        for t in tasks.values():
            if t["status"] == "todo":
                deps_done = all(tasks.get(d, {}).get("status") == "done" for d in t.get("depends_on", []))
                if deps_done:
                    print(f"\n  → Next: cc-flow start {t['id']} — {t['title']}")
                    break
    elif total > 0:
        print("\n  ✅ All tasks done!")
    else:
        print("\n  → Get started: cc-flow epic create --title 'My Feature'")


def _doctor_checks():
    """Run all health checks, return list of check results."""
    import os
    import shutil
    import subprocess as sp

    checks = []

    def chk(name, status, msg, fix=None):
        checks.append({"name": name, "status": status, "message": msg, "fix": fix})

    # Python version
    v = sys.version_info
    if v >= (3, 9):
        chk("Python", "pass", f"{v.major}.{v.minor}.{v.micro}")
    elif v >= (3, 7):
        chk("Python", "warn", f"{v.major}.{v.minor} (3.9+ recommended)", "brew install python@3.12")
    else:
        chk("Python", "fail", f"{v.major}.{v.minor} (3.9+ required)", "brew install python@3.12")

    # Git + Git repo
    if shutil.which("git"):
        try:
            ver = sp.run(["git", "--version"], capture_output=True, text=True, timeout=5).stdout.strip()
            chk("Git", "pass", ver)
            result = sp.run(["git", "rev-parse", "--is-inside-work-tree"],
                            capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                branch = sp.run(["git", "branch", "--show-current"],
                                capture_output=True, text=True, timeout=5).stdout.strip()
                chk("Git repo", "pass", f"branch: {branch}" if branch else "detached HEAD")
            else:
                chk("Git repo", "warn", "not a git repo", "git init")
        except (sp.TimeoutExpired, OSError):
            chk("Git", "warn", "git found but not responding")
    else:
        chk("Git", "fail", "git not found", "brew install git")

    # Lint tools
    for tool, pkg in [("ruff", "pip install ruff"), ("mypy", "pip install mypy")]:
        chk(tool, "pass" if shutil.which(tool) else "warn",
            "available" if shutil.which(tool) else "not installed",
            None if shutil.which(tool) else pkg)

    # .tasks/ directory
    if TASKS_DIR.exists() and META_FILE.exists():
        meta = load_meta()
        chk(".tasks/", "pass", f"initialized (next_epic={meta.get('next_epic', '?')})")
    elif TASKS_DIR.exists():
        chk(".tasks/", "warn", "directory exists but meta.json missing", "cc-flow init")
    else:
        chk(".tasks/", "warn", "not initialized", "cc-flow init")

    # Task integrity
    tasks = all_tasks()
    if tasks:
        orphaned = sum(1 for t in tasks.values() if not (EPICS_DIR / f"{t.get('epic', '')}.md").exists())
        broken_deps = sum(1 for t in tasks.values() for d in t.get("depends_on", []) if d not in tasks)
        if orphaned == 0 and broken_deps == 0:
            chk("Task integrity", "pass", f"{len(tasks)} tasks, all clean")
        else:
            parts = ([f"{orphaned} orphaned"] if orphaned else []) + ([f"{broken_deps} broken deps"] if broken_deps else [])
            chk("Task integrity", "warn", ", ".join(parts), "cc-flow validate")
    else:
        chk("Task integrity", "pass", "no tasks yet")

    # Learnings
    if LEARNINGS_DIR.exists():
        count = len(list(LEARNINGS_DIR.glob("*.json")))
        patterns_dir = TASKS_DIR / "patterns"
        patterns = len(list(patterns_dir.glob("*.json"))) if patterns_dir.exists() else 0
        chk("Learnings", "pass", f"{count} learnings, {patterns} promoted patterns")
        if count >= 20 and patterns == 0:
            chk("Consolidation", "warn", f"{count} learnings not consolidated", "cc-flow consolidate")
    else:
        chk("Learnings", "pass", "none yet (use cc-flow learn)")

    # Config + Claude Code env
    if CONFIG_FILE.exists():
        chk("Config", "pass", f"{len(safe_json_load(CONFIG_FILE, default={}))} settings")
    else:
        chk("Config", "pass", "using defaults")

    in_claude = bool(os.environ.get("CLAUDE_CODE") or os.environ.get("CLAUDE_PROJECT_DIR")
                     or os.environ.get("CLAUDE_PLUGIN_ROOT"))
    chk("Claude Code", "pass" if in_claude else "warn",
        "running inside Claude Code" if in_claude else "not detected (standalone mode)")

    return checks


def cmd_doctor(args):
    """Health check — validate environment, tools, config, and task integrity."""
    checks = _doctor_checks()
    fmt = getattr(args, "format", "text") or "text"

    if fmt == "json":
        passed = sum(1 for c in checks if c["status"] == "pass")
        warned = sum(1 for c in checks if c["status"] == "warn")
        failed = sum(1 for c in checks if c["status"] == "fail")
        print(json.dumps({
            "success": failed == 0,
            "checks": checks,
            "summary": {"pass": passed, "warn": warned, "fail": failed},
        }))
    else:
        icons = {"pass": "✓", "warn": "⚠", "fail": "✗"}
        print("## cc-flow Doctor\n")
        for c in checks:
            icon = icons.get(c["status"], "?")
            print(f"  {icon} {c['name']}: {c['message']}")
            if c.get("fix"):
                print(f"    → fix: {c['fix']}")
        passed = sum(1 for c in checks if c["status"] == "pass")
        print(f"\n  {passed}/{len(checks)} checks passed")

    if any(c["status"] == "fail" for c in checks):
        sys.exit(1)


STATUS_STYLE = {
    "todo": {"mermaid": ":::todo", "icon": "○"},
    "in_progress": {"mermaid": ":::inprog", "icon": "◐"},
    "done": {"mermaid": ":::done", "icon": "●"},
    "blocked": {"mermaid": ":::blocked", "icon": "✗"},
}


def _graph_mermaid(filtered, edges, as_json=False):
    """Render Mermaid graph."""
    lines = [
        "graph TD",
        "    classDef todo fill:#f9f9f9,stroke:#999,color:#333",
        "    classDef inprog fill:#fff3cd,stroke:#ffc107,color:#333",
        "    classDef done fill:#d4edda,stroke:#28a745,color:#333",
        "    classDef blocked fill:#f8d7da,stroke:#dc3545,color:#333",
    ]
    for tid, t in sorted(filtered.items()):
        label = t.get("title", tid)[:40]
        size = f" [{t.get('size', '')}]" if t.get("size") else ""
        style = STATUS_STYLE.get(t.get("status", "todo"), {}).get("mermaid", "")
        lines.append(f'    {tid.replace(".", "_")}["{tid}: {label}{size}"]{style}')
    for src, dst in edges:
        lines.append(f"    {src.replace('.', '_')} --> {dst.replace('.', '_')}")
    lines.append("\n    %% Legend: todo=gray, in_progress=yellow, done=green, blocked=red")
    text = "\n".join(lines)

    if as_json:
        print(json.dumps({"success": True, "format": "mermaid",
                          "nodes": len(filtered), "edges": len(edges), "mermaid": text}))
    else:
        print(f"```mermaid\n{text}\n```")


def _graph_ascii(filtered, edges):
    """Render ASCII dependency tree."""
    has_incoming = {dst for _, dst in edges}
    roots = [tid for tid in filtered if tid not in has_incoming] or sorted(filtered.keys())[:1]
    children = {}
    for src, dst in edges:
        children.setdefault(src, []).append(dst)

    printed = set()

    def print_tree(tid, prefix="", is_last=True):
        icon = STATUS_STYLE.get(filtered[tid]["status"], {}).get("icon", "?")
        connector = "└── " if is_last else "├── "
        if tid in printed:
            print(f"{prefix}{connector}{icon} {tid} (↻ ref)")
            return
        printed.add(tid)
        t = filtered[tid]
        title = t.get("title", "")[:35]
        size = f" [{t.get('size', '')}]" if t.get("size") else ""
        print(f"{prefix}{connector}{icon} {tid}: {title}{size}")
        kids = children.get(tid, [])
        for i, kid in enumerate(kids):
            print_tree(kid, prefix + ("    " if is_last else "│   "), i == len(kids) - 1)

    for i, root in enumerate(sorted(roots)):
        if i > 0:
            print()
        epic_id = filtered[root].get("epic", "")
        if i == 0 and epic_id:
            epic_spec = EPICS_DIR / f"{epic_id}.md"
            if epic_spec.exists():
                title = epic_spec.read_text().split("\n", 1)[0].lstrip("# ").replace("Epic:", "").strip()
                print(f"📋 {title}" if title else f"📋 {epic_id}")
        print_tree(root, "", i == len(roots) - 1)

    done = sum(1 for t in filtered.values() if t["status"] == "done")
    print(f"\n── {done}/{len(filtered)} done, {len(edges)} dependencies ──")


def _graph_dot(filtered, edges):
    """Render Graphviz DOT format."""
    fill = {"todo": "#f9f9f9", "in_progress": "#fff3cd", "done": "#d4edda", "blocked": "#f8d7da"}
    lines = ["digraph tasks {", "    rankdir=LR;", '    node [shape=box, style=filled];']
    for tid, t in sorted(filtered.items()):
        label = f"{tid}\\n{t.get('title', '')[:30]}"
        color = fill.get(t.get("status", "todo"), "#f9f9f9")
        lines.append(f'    "{tid}" [label="{label}", fillcolor="{color}"];')
    for src, dst in edges:
        lines.append(f'    "{src}" -> "{dst}";')
    lines.append("}")
    print("\n".join(lines))


def cmd_graph(args):
    """Generate dependency graph in Mermaid, ASCII, or DOT format."""
    tasks = all_tasks()
    epic_filter = getattr(args, "epic", "") or ""
    fmt = getattr(args, "format", "mermaid") or "mermaid"

    filtered = {tid: t for tid, t in tasks.items() if not epic_filter or t.get("epic") == epic_filter}
    if not filtered:
        _error("No tasks found")

    edges = [(dep, tid) for tid, t in filtered.items() for dep in t.get("depends_on", []) if dep in filtered]

    if fmt == "mermaid":
        _graph_mermaid(filtered, edges, getattr(args, "json", False))
    elif fmt == "ascii":
        _graph_ascii(filtered, edges)
    elif fmt == "dot":
        _graph_dot(filtered, edges)
    else:
        _error(f"Unknown format: {fmt}. Use: mermaid, ascii, dot")


def main():
    """Entry point — delegates to cc_flow.cli for parsing and dispatch."""
    sys.path.insert(0, str(Path(__file__).parent))
    from cc_flow.cli import build_parser

    parser = build_parser()
    args = parser.parse_args()

    # Build command dispatch table
    cmds = {
        "init": cmd_init, "list": cmd_list, "epics": cmd_epics, "tasks": cmd_tasks,
        "show": cmd_show, "ready": cmd_ready, "start": cmd_start, "done": cmd_done,
        "block": cmd_block, "progress": cmd_progress, "status": cmd_status,
        "version": cmd_version, "validate": cmd_validate, "next": cmd_next,
        "scan": cmd_scan, "route": cmd_route, "learn": cmd_learn,
        "learnings": cmd_learnings, "log": cmd_log, "summary": cmd_summary,
        "archive": cmd_archive, "stats": cmd_stats, "consolidate": cmd_consolidate,
        "history": cmd_history, "config": cmd_config, "graph": cmd_graph,
        "doctor": cmd_doctor, "dashboard": cmd_dashboard, "rollback": cmd_rollback,
        "search": cmd_search, "compact": cmd_compact, "github-search": cmd_github_search,
    }

    # Subcommand dispatch for nested commands
    subcmd_map = {
        "epic": {"epic_cmd": {"create": cmd_epic_create, "close": cmd_epic_close,
                               "import": cmd_epic_import, "reset": cmd_epic_reset}},
        "task": {"task_cmd": {"create": cmd_task_create, "reset": cmd_task_reset,
                               "set-spec": cmd_task_set_spec}},
    }

    if args.command in subcmd_map:
        for attr, handlers in subcmd_map[args.command].items():
            sub = getattr(args, attr, None)
            if sub in handlers:
                handlers[sub](args)
            else:
                parser.print_help()
                sys.exit(1)
    elif args.command == "auto":
        cmd_auto(args)
    elif args.command == "session":
        cmd_session(args)
    elif args.command == "dep" and getattr(args, "dep_cmd", None) == "add":
        cmd_dep_add(args)
    elif args.command in cmds:
        cmds[args.command](args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
