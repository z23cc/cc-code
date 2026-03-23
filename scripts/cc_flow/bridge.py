"""cc-flow bridge — Morph × RepoPrompt × Supermemory collaboration.

Closes 4 feedback loops that were previously isolated:

P0:
  1. deep_search: Morph Search → RP Selection → RP Builder (search + understand)
  2. review_to_memory: RP Review verdict → Supermemory (knowledge accumulation)

P1:
  3. memory_enhanced_chat: Supermemory recall → inject into RP chat (memory-augmented AI)
  4. scan_to_memory: OODA findings → Supermemory (cross-project pattern library)
"""

import json
import os
from typing import Optional

from cc_flow.core import now_iso, safe_json_load

# Lazy imports to avoid circular deps and startup cost
_ERRORS = (RuntimeError, TimeoutError, OSError, ValueError, KeyError, ImportError)


# ── Helpers ──

def _get_supermemory():
    """Get Supermemory client (None if unavailable)."""
    api_key = os.environ.get("SUPERMEMORY_API_KEY", "")
    if not api_key:
        return None
    try:
        from supermemory import Supermemory
        return Supermemory(api_key=api_key)
    except ImportError:
        return None


def _recall_memories(query, tags=None, limit=3):
    """Search Supermemory and return list of content strings."""
    client = _get_supermemory()
    if not client:
        return []
    try:
        results = client.search.execute(
            q=query,
            container_tags=tags or ["cc-flow"],
            limit=limit,
            rerank=True,
            rewrite_query=True,
        )
        return [
            (getattr(chunk, "content", "") or "")[:300]
            for chunk in getattr(results, "results", [])
            if getattr(chunk, "content", "")
        ]
    except _ERRORS:
        return []


def _save_memory(content, tags, custom_id=None):
    """Save content to Supermemory. Returns True on success."""
    client = _get_supermemory()
    if not client:
        return False
    try:
        import subprocess
        branch = subprocess.run(
            ["git", "branch", "--show-current"],
            check=False, capture_output=True, text=True, timeout=5,
        ).stdout.strip()
        context = f"Branch: {branch}" if branch else "cc-flow"
    except _ERRORS:
        context = "cc-flow"

    try:
        kwargs = {
            "content": content,
            "container_tags": ["cc-flow"] + tags,
            "entity_context": context,
            "metadata": {"source": "cc-flow-bridge", "saved_at": now_iso()},
        }
        if custom_id:
            kwargs["custom_id"] = custom_id
        client.add(**kwargs)
        return True
    except _ERRORS:
        return False


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# P0-1: deep_search — Morph Search → RP Selection → RP Builder
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def deep_search(query, *, response_type="question", max_files=10,
                window=None, tab=None):
    """Morph semantic search → RP file selection → RP context_builder.

    Chain: Morph finds relevant files → RP selects them → Builder analyzes.
    Combines Morph's speed with RP's depth.

    Returns dict with search results, selected files, and builder analysis.
    """
    result = {"query": query, "steps": []}

    # Step 1: Morph Search to find relevant files
    files_found = []
    try:
        from cc_flow.core import get_morph_client
        morph = get_morph_client()
        if morph:
            search_result = morph.search(query, directory=".", max_turns=4)
            # Extract file paths from search results
            for line in search_result.splitlines():
                if ":" in line and not line.startswith(" "):
                    filepath = line.split(":")[0].strip()
                    if filepath and not filepath.startswith("#"):
                        if filepath not in files_found:
                            files_found.append(filepath)
            files_found = files_found[:max_files]
            result["steps"].append({
                "tool": "morph_search",
                "files_found": len(files_found),
                "files": files_found,
            })
    except _ERRORS as e:
        result["steps"].append({"tool": "morph_search", "error": str(e)})

    # Fallback: grep-based search if Morph found nothing
    if not files_found:
        try:
            import subprocess
            grep_result = subprocess.run(
                ["grep", "-rl", "--include=*.py", "--include=*.ts",
                 "--include=*.js", "--include=*.go", "-i", query, "."],
                capture_output=True, text=True, timeout=10,
            )
            files_found = [
                f.strip() for f in grep_result.stdout.splitlines()
                if f.strip()
            ][:max_files]
            result["steps"].append({
                "tool": "grep_fallback",
                "files_found": len(files_found),
            })
        except _ERRORS:
            pass

    if not files_found:
        result["analysis"] = "No relevant files found for query."
        return result

    # Step 2: RP Selection — add found files to context
    try:
        from cc_flow import rp
        if rp.is_available():
            rp.select_set(files_found, window=window, tab=tab)
            result["steps"].append({
                "tool": "rp_select",
                "files_selected": len(files_found),
            })
    except _ERRORS as e:
        result["steps"].append({"tool": "rp_select", "error": str(e)})

    # Step 3: RP Builder — deep analysis with the selected context
    try:
        from cc_flow import rp
        if rp.is_available():
            analysis = rp.builder(
                query,
                response_type=response_type,
                window=window, tab=tab,
                raw_json=True,
            )
            result["steps"].append({"tool": "rp_builder", "success": True})
            result["analysis"] = analysis
        else:
            result["analysis"] = f"RP unavailable. Files found: {files_found}"
    except _ERRORS as e:
        result["steps"].append({"tool": "rp_builder", "error": str(e)})
        result["analysis"] = f"Builder failed. Files found: {files_found}"

    return result


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# P0-2: review_to_memory — RP Review → Supermemory
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def review_to_memory(verdict, task_id, findings="", backend="agent"):
    """Save review verdict and findings to Supermemory.

    Called after a code review produces a verdict. Captures:
    - What was reviewed (task_id)
    - The verdict (SHIP / NEEDS_WORK / MAJOR_RETHINK)
    - Key findings (what was wrong or good)
    - Which backend produced the review

    These memories help future reviews catch similar issues.
    """
    if verdict == "SHIP" and not findings:
        # Don't clutter memory with routine SHIPs
        return False

    content = (
        f"Code Review: {task_id}\n"
        f"Verdict: {verdict}\n"
        f"Backend: {backend}\n"
    )
    if findings:
        # Truncate to keep memory focused
        content += f"Findings:\n{findings[:500]}\n"

    tags = ["review", verdict.lower()]
    custom_id = f"cc-flow-review-{task_id}-{now_iso()[:10]}"

    return _save_memory(content, tags, custom_id=custom_id)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# P1-1: memory_enhanced_chat — Supermemory → RP Chat
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def memory_enhanced_chat(message, *, mode="chat", new_chat=True,
                         window=None, tab=None):
    """Recall relevant memories → inject into RP chat as context.

    Searches Supermemory for past experiences related to the message,
    then prepends them to the RP chat prompt for memory-augmented AI.
    """
    result = {"message": message, "memories_injected": 0}

    # Step 1: Recall relevant memories
    memories = _recall_memories(message, tags=["cc-flow"], limit=3)

    # Step 2: Build enhanced message
    if memories:
        memory_block = "\n".join(
            f"- {m}" for m in memories
        )
        enhanced = (
            f"{message}\n\n"
            f"<past_experience>\n"
            f"Relevant past experiences from this project:\n"
            f"{memory_block}\n"
            f"</past_experience>"
        )
        result["memories_injected"] = len(memories)
    else:
        enhanced = message

    # Step 3: Send to RP chat
    try:
        from cc_flow import rp
        if rp.is_available():
            response = rp.chat(
                enhanced,
                mode=mode,
                new_chat=new_chat,
                window=window, tab=tab,
            )
            result["response"] = response
            result["success"] = True
        else:
            result["success"] = False
            result["error"] = "RP unavailable"
    except _ERRORS as e:
        result["success"] = False
        result["error"] = str(e)

    return result


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# P1-2: scan_to_memory — OODA findings → Supermemory
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def scan_to_memory(findings, scan_type="auto"):
    """Save OODA scan findings to Supermemory for cross-project reuse.

    Only saves P1/P2 (high-severity) findings to avoid clutter.
    These can be recalled when working on similar code in other projects.

    Args:
        findings: list of dicts with {severity, category, message, file, ...}
        scan_type: "code", "test", "full", "deep"
    """
    high_severity = [
        f for f in findings
        if f.get("severity", "P4") in ("P1", "P2")
    ]

    if not high_severity:
        return {"saved": 0, "skipped": len(findings)}

    saved = 0
    for finding in high_severity[:10]:  # Cap at 10 per scan
        content = (
            f"Scan Finding ({scan_type}):\n"
            f"Severity: {finding.get('severity', 'P2')}\n"
            f"Category: {finding.get('category', 'unknown')}\n"
            f"Issue: {finding.get('message', '')}\n"
        )
        if finding.get("file"):
            content += f"File: {finding['file']}\n"
        if finding.get("sample"):
            content += f"Example: {finding['sample'][:200]}\n"

        tags = [
            "scan",
            finding.get("category", "unknown"),
            finding.get("severity", "P2").lower(),
        ]

        if _save_memory(content, tags):
            saved += 1

    return {"saved": saved, "skipped": len(findings) - saved}


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# P2-1: structure_to_embed — RP Code Structure → Morph Embed
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def structure_to_embed(paths, *, window=None, tab=None):
    """Extract code structure via RP → embed via Morph → enable similarity search.

    Generates function-level embeddings from RP codemaps.
    Returns indexed functions with vectors for similarity queries.
    """
    result = {"paths": paths, "functions": [], "embedded": 0}

    # Step 1: Get code structure from RP
    signatures = []
    try:
        from cc_flow import rp
        if rp.is_available():
            raw = rp.structure(paths, window=window, tab=tab)
            # Parse function signatures from structure output
            for line in raw.splitlines():
                line = line.strip()
                if line and (
                    "def " in line or "class " in line or
                    "func " in line or "function " in line or
                    "fn " in line
                ):
                    signatures.append(line[:200])
            result["functions_found"] = len(signatures)
    except _ERRORS as e:
        result["structure_error"] = str(e)

    if not signatures:
        return result

    # Step 2: Embed signatures via Morph
    try:
        from cc_flow.embeddings import embed_texts
        embedded = embed_texts(signatures)
        if embedded:
            result["embedded"] = len(embedded)
            result["functions"] = [
                {"signature": sig, "has_vector": vec is not None}
                for sig, vec in embedded
            ]
    except _ERRORS as e:
        result["embed_error"] = str(e)

    return result


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# P2-2: recall_for_review — Supermemory → RP Review context
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def recall_for_review(task_description):
    """Recall past review findings relevant to current task.

    Searches Supermemory for past NEEDS_WORK/MAJOR_RETHINK reviews
    related to the current task, returning actionable context to
    inject into the review prompt.
    """
    memories = _recall_memories(
        task_description,
        tags=["cc-flow", "review"],
        limit=3,
    )
    if not memories:
        return None

    return (
        "Past review findings for similar code:\n"
        + "\n".join(f"- {m}" for m in memories)
    )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CLI commands
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def cmd_deep_search(args):
    """Morph search → RP select → RP builder (deep understanding)."""
    query = " ".join(args.query) if args.query else ""
    if not query:
        from cc_flow.core import error
        error("Provide a search query")

    response_type = getattr(args, "type", "question") or "question"
    result = deep_search(query, response_type=response_type)
    print(json.dumps(result, indent=2, default=str))


def cmd_smart_chat(args):
    """Memory-enhanced RP chat (recall → inject → chat)."""
    message = getattr(args, "message", "")
    if not message:
        from cc_flow.core import error
        error("Provide a message")

    mode = getattr(args, "mode", "chat") or "chat"
    new_chat = getattr(args, "new", True)
    result = memory_enhanced_chat(message, mode=mode, new_chat=new_chat)
    print(json.dumps(result, indent=2, default=str))


def cmd_embed_structure(args):
    """RP code structure → Morph embed (function-level similarity search)."""
    paths = args.paths if args.paths else ["."]
    result = structure_to_embed(paths)
    print(json.dumps(result, indent=2, default=str))


def cmd_recall_review(args):
    """Recall past review findings for a task description."""
    query = " ".join(args.query) if args.query else ""
    if not query:
        from cc_flow.core import error
        error("Provide a task description")

    context = recall_for_review(query)
    print(json.dumps({
        "success": True,
        "query": query,
        "context": context or "(no past review findings)",
        "has_findings": context is not None,
    }, indent=2))


def cmd_bridge_status(args):
    """Show status of all three systems (Morph, RP, Supermemory)."""
    status = {}

    # Morph
    try:
        from cc_flow.core import get_morph_client
        morph = get_morph_client()
        status["morph"] = {"available": morph is not None}
    except _ERRORS:
        status["morph"] = {"available": False}

    # RepoPrompt
    try:
        from cc_flow import rp
        t = rp.available_transports()
        status["repoprompt"] = {
            "available": t["active"] != "none",
            "transport": t["active"],
            "cli": t["cli"],
            "mcp": t["mcp"],
            "version": rp.rp_version(),
        }
    except _ERRORS:
        status["repoprompt"] = {"available": False}

    # Supermemory
    sm = _get_supermemory()
    status["supermemory"] = {"available": sm is not None}

    # Bridge loops
    loops = [
        {"name": "deep-search", "chain": "Morph → RP", "cmd": "cc-flow deep-search"},
        {"name": "smart-chat", "chain": "SM → RP", "cmd": "cc-flow smart-chat"},
        {"name": "review-to-memory", "chain": "RP → SM", "cmd": "(auto on done)"},
        {"name": "scan-to-memory", "chain": "OODA → SM", "cmd": "(auto on deep scan)"},
        {"name": "embed-structure", "chain": "RP → Morph", "cmd": "cc-flow embed-structure"},
        {"name": "recall-review", "chain": "SM → RP", "cmd": "cc-flow recall-review"},
    ]
    status["bridge_loops"] = loops

    all_up = all(
        status[s].get("available", False)
        for s in ("morph", "repoprompt", "supermemory")
    )
    status["all_systems_connected"] = all_up

    print(json.dumps(status, indent=2, default=str))
