"""cc-flow search, export, and embedding-powered commands."""

import json
from pathlib import Path

from cc_flow.core import (
    EPICS_DIR,
    TASKS_SUBDIR,
    all_tasks,
    error,
)
from cc_flow.views import _task_counts


def cmd_export(args):
    """Export an epic and its tasks as a self-contained markdown report."""
    epic_id = args.id
    epic_path = EPICS_DIR / f"{epic_id}.md"
    if not epic_path.exists():
        error(f"Epic not found: {epic_id}")

    tasks = all_tasks()
    epic_tasks = sorted(
        [t for t in tasks.values() if t.get("epic") == epic_id],
        key=lambda t: t["id"],
    )
    counts = _task_counts(epic_tasks)

    lines = [
        f"# {epic_id}",
        "",
        f"**Progress:** {counts['done']}/{counts['total']} ({counts['pct']}%)",
        f"**Status:** {counts['done']} done, {counts['in_progress']} in progress, "
        f"{counts['blocked']} blocked, {counts['todo']} todo",
        "",
        "## Spec",
        "",
        epic_path.read_text().strip(),
        "",
        "## Tasks",
        "",
    ]

    status_icon = {"todo": "[ ]", "in_progress": "[~]", "done": "[x]", "blocked": "[!]"}
    for t in epic_tasks:
        icon = status_icon.get(t["status"], "[ ]")
        line = f"- {icon} **{t['id']}**: {t.get('title', '')}"
        if t.get("summary"):
            line += f" — {t['summary']}"
        lines.append(line)

    output = "\n".join(lines) + "\n"

    out_file = getattr(args, "output", "") or ""
    if out_file:
        Path(out_file).write_text(output)
        print(json.dumps({"success": True, "epic": epic_id, "file": out_file,
                          "tasks": len(epic_tasks)}))
    else:
        print(output)


def _score_task(tid, task, query):
    """Score a task's relevance to query. Returns 0 if no match."""
    score = 0
    title = task.get("title", "").lower()
    if query in title:
        score += 3
    elif any(w in title for w in query.split()):
        score += 1
    spec_path = TASKS_SUBDIR / f"{tid}.md"
    if spec_path.exists() and query in spec_path.read_text().lower():
        score += 2
    return score


def _find_matching_epics(query):
    """Find epics whose spec contains the query."""
    if not EPICS_DIR.exists():
        return []
    return [f.stem for f in EPICS_DIR.glob("*.md") if query in f.read_text().lower()]


def _semantic_find(query, tasks):
    """Use Morph embeddings for semantic search."""
    from cc_flow.embeddings import semantic_search
    documents = [
        {"id": tid, "text": f"{t.get('title', '')} {t.get('summary', '')}",
         "title": t.get("title", ""), "status": t["status"], "epic": t.get("epic", "")}
        for tid, t in tasks.items()
    ]
    return semantic_search(query, documents, top_n=20)


def cmd_find(args):
    """Search across task titles, specs, and epic specs."""
    query = " ".join(args.query).lower() if args.query else ""
    if not query:
        error("Provide a search query")

    tasks = all_tasks()
    use_semantic = getattr(args, "semantic", False)

    if use_semantic:
        results = _semantic_find(query, tasks)
        if results is not None:
            print(json.dumps({
                "success": True, "query": query, "engine": "embedding",
                "tasks": results, "total": len(results),
            }))
            return

    matches = [
        {"id": tid, "title": t.get("title", ""), "status": t["status"],
         "epic": t.get("epic", ""), "score": score}
        for tid, t in tasks.items()
        if (score := _score_task(tid, t, query)) > 0
    ]
    matches.sort(key=lambda m: -m["score"])

    print(json.dumps({
        "success": True,
        "query": query,
        "engine": "keyword",
        "tasks": matches[:20],
        "epics": _find_matching_epics(query),
        "total": len(matches),
    }))


def cmd_similar(args):
    """Find tasks similar to a given task using embeddings."""
    from cc_flow.embeddings import semantic_search

    task_id = args.id
    tasks = all_tasks()
    if task_id not in tasks:
        error(f"Task not found: {task_id}")

    source = tasks[task_id]
    query_text = f"{source.get('title', '')} {source.get('summary', '')}"
    documents = [
        {"id": tid, "text": f"{t.get('title', '')} {t.get('summary', '')}",
         "title": t.get("title", ""), "status": t["status"], "epic": t.get("epic", "")}
        for tid, t in tasks.items()
        if tid != task_id
    ]

    results = semantic_search(query_text, documents, top_n=getattr(args, "top", 5) or 5)
    if results is None:
        error("Embedding unavailable. Set MORPH_API_KEY to enable semantic search.")

    print(json.dumps({
        "success": True,
        "source": {"id": task_id, "title": source.get("title", "")},
        "similar": results,
        "total": len(results),
    }))


def cmd_priority(args):
    """Show all non-done tasks sorted by priority across all epics."""
    tasks = all_tasks()
    status_filter = getattr(args, "status", "") or ""

    active = [
        {
            "id": tid, "title": t.get("title", ""), "status": t["status"],
            "priority": t.get("priority", 999), "epic": t.get("epic", ""),
            "size": t.get("size", "M"),
            "ready": all(tasks.get(d, {}).get("status") == "done" for d in t.get("depends_on", [])),
        }
        for tid, t in tasks.items()
        if t["status"] != "done" and (not status_filter or t["status"] == status_filter)
    ]
    active.sort(key=lambda t: (0 if t["ready"] else 1, t["priority"], t["id"]))

    print(json.dumps({
        "success": True, "tasks": active, "total": len(active),
        "ready_count": sum(1 for t in active if t["ready"]),
    }))


def _task_documents(tasks):
    """Build document list from tasks for embedding operations."""
    return [
        {"id": tid, "text": f"{t.get('title', '')} {t.get('summary', '')}".strip()}
        for tid, t in tasks.items()
    ]


def cmd_index(_args):
    """Pre-build embedding index for all tasks."""
    from cc_flow.embeddings import build_index
    tasks = all_tasks()
    result = build_index(_task_documents(tasks))
    if result is None:
        error("Embedding unavailable. Set MORPH_API_KEY.")
    print(json.dumps({"success": True, **result}))


def cmd_dedupe(args):
    """Detect near-duplicate tasks using embedding similarity."""
    from cc_flow.embeddings import find_duplicates
    tasks = all_tasks()
    threshold = getattr(args, "threshold", 0.85) or 0.85
    duplicates = find_duplicates(_task_documents(tasks), threshold=threshold)
    if duplicates is None:
        error("Embedding unavailable. Set MORPH_API_KEY.")
    print(json.dumps({
        "success": True, "duplicates": duplicates, "count": len(duplicates),
        "threshold": threshold, "total_tasks": len(tasks),
    }))


def cmd_suggest(args):
    """Suggest approach for a task based on similar completed tasks."""
    from cc_flow.embeddings import semantic_search

    task_id = args.id
    tasks = all_tasks()
    if task_id not in tasks:
        error(f"Task not found: {task_id}")

    source = tasks[task_id]
    query_text = f"{source.get('title', '')} {source.get('summary', '')}"
    completed = [
        {"id": tid, "text": f"{t.get('title', '')} {t.get('summary', '')}",
         "title": t.get("title", ""), "summary": t.get("summary", "")}
        for tid, t in tasks.items()
        if t["status"] == "done" and tid != task_id
    ]

    if not completed:
        print(json.dumps({"success": True, "id": task_id, "suggestions": [],
                          "reason": "No completed tasks to learn from"}))
        return

    results = semantic_search(query_text, completed, top_n=3)
    if results is None:
        error("Embedding unavailable. Set MORPH_API_KEY.")

    suggestions = [
        {"based_on": r["id"], "title": r.get("title", ""),
         "summary": r.get("summary", ""), "similarity": r["score"]}
        for r in results if r["score"] > 0.2
    ]
    print(json.dumps({
        "success": True, "id": task_id, "title": source.get("title", ""),
        "suggestions": suggestions,
    }))
