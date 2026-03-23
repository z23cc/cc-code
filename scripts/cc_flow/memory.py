"""cc-flow memory — persistent cross-session knowledge via Supermemory.

Stores learnings, patterns, and project context in Supermemory's
semantic memory layer. Enables cross-project knowledge transfer.

Requires: SUPERMEMORY_API_KEY environment variable.
Install: pip install supermemory
"""

import json
import os

from cc_flow.core import error, now_iso


def _get_client():
    """Get Supermemory client. Returns None if not configured."""
    api_key = os.environ.get("SUPERMEMORY_API_KEY", "")
    if not api_key:
        return None
    try:
        from supermemory import Supermemory
        return Supermemory(api_key=api_key)
    except (ImportError, ValueError):
        return None


def cmd_memory_save(args):
    """Save a piece of knowledge to Supermemory."""
    client = _get_client()
    if not client:
        error("SUPERMEMORY_API_KEY not set. Get one at https://supermemory.ai")

    content = args.content
    tags = [t.strip() for t in (args.tags or "").split(",") if t.strip()]
    tags.append("cc-flow")

    try:
        result = client.add(
            content=content,
            container_tags=tags,
            metadata={"source": "cc-flow", "saved_at": now_iso()},
        )
        print(json.dumps({
            "success": True,
            "id": getattr(result, "id", None),
            "tags": tags,
        }))
    except (RuntimeError, TimeoutError, OSError, ValueError, KeyError) as exc:
        error(f"Failed to save memory: {exc}")


def cmd_memory_search(args):
    """Search Supermemory for relevant knowledge."""
    client = _get_client()
    if not client:
        error("SUPERMEMORY_API_KEY not set. Get one at https://supermemory.ai")

    query = " ".join(args.query) if args.query else ""
    if not query:
        error("Provide a search query")

    try:
        results = client.search.execute(
            q=query,
            container_tags=["cc-flow"],
            limit=getattr(args, "limit", 5) or 5,
            rerank=True,
        )
        items = [
            {"content": getattr(chunk, "content", "")[:200],
             "score": getattr(chunk, "score", 0)}
            for chunk in getattr(results, "results", [])
        ]

        print(json.dumps({
            "success": True,
            "query": query,
            "results": items,
            "total": len(items),
        }))
    except (RuntimeError, TimeoutError, OSError, ValueError, KeyError) as exc:
        error(f"Search failed: {exc}")


def cmd_memory_sync(args):
    """Sync local learnings to Supermemory."""
    from cc_flow.core import LEARNINGS_DIR, safe_json_load

    client = _get_client()
    if not client:
        error("SUPERMEMORY_API_KEY not set")

    if not LEARNINGS_DIR.exists():
        print(json.dumps({"success": True, "synced": 0, "message": "No learnings to sync"}))
        return

    synced = 0
    for f in sorted(LEARNINGS_DIR.glob("*.json")):
        data = safe_json_load(f, default=None)
        if not data:
            continue
        if data.get("synced_to_supermemory"):
            continue

        content = (
            f"Task: {data.get('task', '')}\n"
            f"Outcome: {data.get('outcome', '')}\n"
            f"Approach: {data.get('approach', '')}\n"
            f"Lesson: {data.get('lesson', '')}\n"
            f"Score: {data.get('score', 0)}"
        )

        try:
            client.add(
                content=content,
                container_tags=["cc-flow", "learning", data.get("outcome", "")],
                metadata={"source": "cc-flow-learning", "file": f.name},
            )
            data["synced_to_supermemory"] = True
            f.write_text(json.dumps(data, indent=2) + "\n")
            synced += 1
        except (RuntimeError, TimeoutError, OSError, ValueError, KeyError):
            continue

    print(json.dumps({"success": True, "synced": synced}))
