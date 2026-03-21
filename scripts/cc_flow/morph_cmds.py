"""cc-flow morph_cmds commands."""

import json
import subprocess as _sp
import sys
from pathlib import Path

from cc_flow.core import (
    error, get_morph_client,
)


def cmd_search(args):
    """Semantic code search via Morph API, with grep fallback and optional rerank."""

    query = " ".join(args.query) if args.query else ""
    if not query:
        error("Provide a search query")

    search_dir = getattr(args, "dir", ".") or "."
    fmt = getattr(args, "format", "text") or "text"
    do_rerank = getattr(args, "rerank", False)

    # Try Morph Python client first
    client = get_morph_client()
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
        error("Search failed")


def cmd_compact(args):
    """Compress text via Morph API (Python)."""
    client = get_morph_client()
    if not client:
        error("MORPH_API_KEY not set. Get one at https://morphllm.com/dashboard/api-keys")

    ratio = float(getattr(args, "ratio", "0.3") or "0.3")
    input_file = getattr(args, "file", "") or ""

    if input_file:
        if not Path(input_file).exists():
            error(f"File not found: {input_file}")
        content = Path(input_file).read_text()
    else:
        import select
        if select.select([sys.stdin], [], [], 0.1)[0]:
            content = sys.stdin.read()
        else:
            error("Provide input via --file or stdin: cat file.txt | cc-flow compact")

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
        error(f"compact failed: {exc}")


def cmd_github_search(args):
    """Search GitHub repos — uses Morph Embedding + Rerank (Python)."""

    query = " ".join(args.query) if args.query else ""
    if not query:
        error("Provide a search query")

    repo = getattr(args, "repo", "") or ""
    url = getattr(args, "url", "") or ""

    if not repo and not url:
        error("Provide --repo owner/repo or --url github-url")

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
            error(f"gh search failed: {result.stderr[:200]}")
    except (OSError, _sp.TimeoutExpired) as exc:
        error(f"GitHub search error: {exc}")
