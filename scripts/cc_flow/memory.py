"""cc-flow memory — persistent cross-session knowledge via Supermemory.

API reference: https://supermemory.ai/docs/api-reference/manage-documents/add-document

Features:
- save: store knowledge with tags, metadata, and custom IDs
- search: semantic search with rerank and query rewriting
- forget: remove outdated knowledge
- sync: batch upload local learnings (idempotent via custom_id)
- recall: search learnings and integrate into route decisions
"""

import json
import os
import subprocess

from cc_flow.core import LEARNINGS_DIR, error, now_iso, safe_json_load

_ERRORS = (RuntimeError, TimeoutError, OSError, ValueError, KeyError)


def _get_client():
    """Get Supermemory client. Returns None if not configured."""
    api_key = os.environ.get("SUPERMEMORY_API_KEY", "")
    if not api_key:
        return None
    try:
        from supermemory import Supermemory
        return Supermemory(api_key=api_key)
    except ImportError:
        return None


def _project_context():
    """Get current project context for entity_context."""
    try:
        branch = subprocess.run(
            ["git", "branch", "--show-current"],
            check=False, capture_output=True, text=True, timeout=5,
        ).stdout.strip()
        repo = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            check=False, capture_output=True, text=True, timeout=5,
        ).stdout.strip()
    except (subprocess.TimeoutExpired, OSError):
        return "cc-flow project"
    else:
        return f"Project: {repo}, Branch: {branch}"


def cmd_memory_save(args):
    """Save knowledge to Supermemory with semantic tags and context."""
    client = _get_client()
    if not client:
        error("SUPERMEMORY_API_KEY not set. Get one at https://supermemory.ai")

    content = args.content
    tags = [t.strip() for t in (getattr(args, "tags", "") or "").split(",") if t.strip()]
    tags.append("cc-flow")
    custom_id = getattr(args, "id", "") or ""

    try:
        kwargs = {
            "content": content,
            "container_tags": tags,
            "entity_context": _project_context(),
            "metadata": {"source": "cc-flow", "saved_at": now_iso()},
        }
        if custom_id:
            kwargs["custom_id"] = custom_id

        result = client.add(**kwargs)
        print(json.dumps({
            "success": True,
            "id": getattr(result, "id", None),
            "tags": tags,
        }))
    except _ERRORS as exc:
        error(f"Failed to save: {exc}")


def cmd_memory_search(args):
    """Semantic search across stored knowledge with rerank."""
    client = _get_client()
    if not client:
        error("SUPERMEMORY_API_KEY not set")

    query = " ".join(args.query) if args.query else ""
    if not query:
        error("Provide a search query")

    limit = getattr(args, "limit", 5) or 5

    try:
        results = client.search.execute(
            q=query,
            container_tags=["cc-flow"],
            limit=limit,
            rerank=True,
            rewrite_query=True,
            include_summary=True,
        )
        items = [
            {
                "content": (getattr(chunk, "content", "") or "")[:300],
                "score": getattr(chunk, "score", 0) or 0,
                "summary": getattr(chunk, "summary", "") or "",
            }
            for chunk in getattr(results, "results", [])
        ]

        print(json.dumps({
            "success": True,
            "query": query,
            "results": items,
            "total": len(items),
        }))
    except _ERRORS as exc:
        error(f"Search failed: {exc}")


def cmd_memory_forget(args):
    """Remove knowledge from Supermemory."""
    client = _get_client()
    if not client:
        error("SUPERMEMORY_API_KEY not set")

    try:
        result = client.memories.forget(
            container_tag="cc-flow",
            content=args.content,
            reason=getattr(args, "reason", "") or "outdated",
        )
        print(json.dumps({
            "success": True,
            "forgotten": getattr(result, "message", "done"),
        }))
    except _ERRORS as exc:
        error(f"Forget failed: {exc}")


def cmd_memory_sync(args):
    """Sync local learnings to Supermemory (idempotent via custom_id)."""
    client = _get_client()
    if not client:
        error("SUPERMEMORY_API_KEY not set")

    if not LEARNINGS_DIR.exists():
        print(json.dumps({"success": True, "synced": 0, "message": "No learnings"}))
        return

    synced = 0
    skipped = 0
    for f in sorted(LEARNINGS_DIR.glob("*.json")):
        data = safe_json_load(f, default=None)
        if not data:
            continue
        if data.get("synced_to_supermemory"):
            skipped += 1
            continue

        content = (
            f"Task: {data.get('task', '')}\n"
            f"Outcome: {data.get('outcome', '')}\n"
            f"Approach: {data.get('approach', '')}\n"
            f"Lesson: {data.get('lesson', '')}\n"
            f"Score: {data.get('score', 0)}"
        )
        outcome_tag = data.get("outcome", "unknown")

        try:
            client.add(
                content=content,
                custom_id=f"cc-flow-learning-{f.stem}",
                container_tags=["cc-flow", "learning", outcome_tag],
                entity_context=_project_context(),
                metadata={
                    "source": "cc-flow-sync",
                    "file": f.name,
                    "score": data.get("score", 0),
                    "outcome": outcome_tag,
                },
            )
            data["synced_to_supermemory"] = True
            f.write_text(json.dumps(data, indent=2) + "\n")
            synced += 1
        except _ERRORS:
            continue

    print(json.dumps({"success": True, "synced": synced, "skipped": skipped}))


def cmd_memory_recall(args):
    """Search memories and format for routing decisions."""
    client = _get_client()
    if not client:
        # Fallback to local learnings
        print(json.dumps({"success": True, "source": "local", "results": []}))
        return

    query = " ".join(args.query) if args.query else ""
    if not query:
        error("Provide a query")

    try:
        results = client.search.execute(
            q=query,
            container_tags=["cc-flow", "learning"],
            limit=3,
            rerank=True,
            rewrite_query=True,
        )
        items = [
            {
                "content": getattr(chunk, "content", "")[:200],
                "score": getattr(chunk, "score", 0),
            }
            for chunk in getattr(results, "results", [])
        ]
        print(json.dumps({
            "success": True,
            "source": "supermemory",
            "query": query,
            "results": items,
        }))
    except _ERRORS:
        print(json.dumps({"success": True, "source": "local", "results": []}))
