"""cc-flow GitHub integration — import issues, create issues from tasks.

Requires `gh` CLI (GitHub CLI) to be installed and authenticated.
"""

import json
import subprocess

from cc_flow.core import (
    EPICS_DIR,
    TASKS_SUBDIR,
    all_tasks,
    error,
    now_iso,
    save_task,
)


def _gh(args_list, timeout=15):
    """Run a gh CLI command, return parsed JSON or None."""
    try:
        result = subprocess.run(
            ["gh", *args_list],
            check=False, capture_output=True, text=True, timeout=timeout,
        )
        if result.returncode != 0:
            return None
        return json.loads(result.stdout) if result.stdout.strip() else None
    except (subprocess.TimeoutExpired, OSError, json.JSONDecodeError):
        return None


def cmd_gh_import(args):
    """Import GitHub issues as cc-flow tasks."""
    epic_id = args.epic
    if not (EPICS_DIR / f"{epic_id}.md").exists():
        error(f"Epic not found: {epic_id}")

    label = getattr(args, "label", "") or ""
    limit = getattr(args, "limit", 20) or 20

    gh_args = ["issue", "list", "--json", "number,title,state,labels,body", "--limit", str(limit)]
    if label:
        gh_args.extend(["--label", label])

    issues = _gh(gh_args)
    if issues is None:
        error("Failed to fetch issues. Is `gh` CLI installed and authenticated?")

    existing = all_tasks()
    imported = 0

    for issue in issues:
        if issue["state"] != "OPEN":
            continue

        # Skip if already imported (check by title match)
        title = f"GH-{issue['number']}: {issue['title']}"
        if any(t.get("title") == title for t in existing.values()):
            continue

        # Find next task number
        epic_tasks = [t for t in existing.values() if t.get("epic") == epic_id]
        task_num = len(epic_tasks) + imported + 1
        task_id = f"{epic_id}.{task_num}"

        task_data = {
            "id": task_id, "epic": epic_id, "title": title,
            "status": "todo", "depends_on": [],
            "created": now_iso(), "gh_issue": issue["number"],
            "tags": [lbl["name"] for lbl in issue.get("labels", [])],
        }
        save_task(TASKS_SUBDIR / f"{task_id}.json", task_data)

        # Save issue body as spec
        body = issue.get("body", "") or f"# GH-{issue['number']}: {issue['title']}\n\nImported from GitHub."
        (TASKS_SUBDIR / f"{task_id}.md").write_text(body)
        imported += 1

    print(json.dumps({
        "success": True, "imported": imported, "epic": epic_id,
        "total_issues": len(issues),
    }))


def cmd_gh_export(args):
    """Create GitHub issues from cc-flow tasks."""
    tasks = all_tasks()
    epic_filter = getattr(args, "epic", "") or ""
    dry_run = getattr(args, "dry_run", False)

    to_export = [
        t for t in tasks.values()
        if t["status"] in ("todo", "in_progress")
        and (not epic_filter or t.get("epic") == epic_filter)
        and not t.get("gh_issue")  # Not already linked
    ]

    if not to_export:
        print(json.dumps({"success": True, "exported": 0, "reason": "No unlinked tasks to export"}))
        return

    created = []
    for t in to_export:
        title = t.get("title", t["id"])
        body = f"**Task:** {t['id']}\n**Epic:** {t.get('epic', '')}\n**Status:** {t['status']}"

        spec_path = TASKS_SUBDIR / f"{t['id']}.md"
        if spec_path.exists():
            body += f"\n\n---\n\n{spec_path.read_text()}"

        if dry_run:
            created.append({"id": t["id"], "title": title, "action": "dry-run"})
            continue

        result = _gh(["issue", "create", "--title", title, "--body", body], timeout=30)
        if result:
            # Link back to task
            t["gh_issue"] = result.get("number")
            save_task(TASKS_SUBDIR / f"{t['id']}.json", t)
            created.append({"id": t["id"], "title": title, "gh_issue": result.get("number")})

    print(json.dumps({
        "success": True, "exported": len(created),
        "dry_run": dry_run, "tasks": created,
    }))


def cmd_gh_status(_args):
    """Show GitHub repo status alongside cc-flow tasks."""
    repo_info = _gh(["repo", "view", "--json", "name,owner,url,defaultBranchRef"])
    open_issues = _gh(["issue", "list", "--state", "open", "--json", "number", "--limit", "100"])
    open_prs = _gh(["pr", "list", "--state", "open", "--json", "number", "--limit", "100"])

    tasks = all_tasks()
    linked = sum(1 for t in tasks.values() if t.get("gh_issue"))

    print(json.dumps({
        "success": True,
        "repo": {
            "name": repo_info.get("name", "?") if repo_info else "unknown",
            "url": repo_info.get("url", "") if repo_info else "",
        },
        "github": {
            "open_issues": len(open_issues) if open_issues else 0,
            "open_prs": len(open_prs) if open_prs else 0,
        },
        "cc_flow": {
            "total_tasks": len(tasks),
            "linked_to_gh": linked,
            "unlinked": len(tasks) - linked,
        },
    }))
