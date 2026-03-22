"""cc-flow morph commands — apply, search, embed, compact, github-search."""

import json
import subprocess as _sp
import sys
from pathlib import Path

from cc_flow.core import error, get_morph_client


def cmd_apply(args):
    """Apply code changes to a file using Morph Fast Apply (10,500+ tok/s)."""
    client = get_morph_client()
    if not client:
        error("MORPH_API_KEY not set. Get one at https://morphllm.com/dashboard/api-keys")

    file_path = args.file
    if not Path(file_path).exists():
        error(f"File not found: {file_path}")

    instruction = args.instruction
    update = getattr(args, "update", "") or ""
    model = getattr(args, "model", "auto") or "auto"

    # Read update from stdin if not provided
    if not update and not sys.stdin.isatty():
        update = sys.stdin.read()
    if not update:
        error("Provide update via --update or stdin")

    try:
        result = client.apply_file(file_path, instruction, update, model)
        print(json.dumps({
            "success": True,
            "file": file_path,
            "chars": len(result),
            "model": model,
        }))
    except Exception as exc:
        error(f"apply failed: {exc}")


def cmd_embed(args):
    """Generate code embeddings using Morph Embedding (1536 dims)."""
    client = get_morph_client()
    if not client:
        error("MORPH_API_KEY not set. Get one at https://morphllm.com/dashboard/api-keys")

    input_text = getattr(args, "input", "") or ""
    input_file = getattr(args, "file", "") or ""

    if input_file:
        if not Path(input_file).exists():
            error(f"File not found: {input_file}")
        inputs = [Path(input_file).read_text()]
    elif input_text:
        inputs = [input_text]
    else:
        error("Provide --input 'text' or --file path")

    try:
        vectors = client.embed(inputs)
        print(json.dumps({
            "success": True,
            "dimensions": len(vectors[0]),
            "count": len(vectors),
            "preview": vectors[0][:5],  # First 5 dims as preview
        }))
    except Exception as exc:
        error(f"embed failed: {exc}")


def cmd_search(args):
    """Semantic code search via Morph WarpGrep, with grep+rerank fallback."""
    query = " ".join(args.query) if args.query else ""
    if not query:
        error("Provide a search query")

    search_dir = getattr(args, "dir", ".") or "."
    fmt = getattr(args, "format", "text") or "text"
    do_rerank = getattr(args, "rerank", False)

    client = get_morph_client()

    # Try Morph WarpGrep first
    if client:
        try:
            result = client.search(query, search_dir)
            if result:
                if fmt == "json":
                    print(json.dumps({"success": True, "engine": "morph-warpgrep", "query": query, "results": result}))
                else:
                    print(f"## Search: {query} (morph warpgrep)\n")
                    print(result if isinstance(result, str) else json.dumps(result, indent=2))
                return
        except Exception:
            pass

    # Fallback to grep
    try:
        result = _sp.run(
            ["grep", "-rn", "--include=*.py", "--include=*.ts", "--include=*.js",
             "--include=*.go", "--include=*.rs", "--include=*.md",
             "-i", query, search_dir],
            check=False, capture_output=True, text=True, timeout=15,
        )
        lines = [ln for ln in result.stdout.strip().split("\n") if ln.strip()][:30]

        # Rerank with Morph if requested
        engine = "grep"
        if do_rerank and lines:
            if client:
                try:
                    ranked = client.rerank(query, lines, top_n=min(10, len(lines)))
                    lines = [r["document"] for r in ranked]
                    engine = "grep+rerank"
                except Exception:
                    engine = "grep (rerank failed)"
            else:
                engine = "grep (rerank skipped: MORPH_API_KEY not set)"

        if fmt == "json":
            print(json.dumps({"success": True, "engine": engine, "query": query,
                              "results": lines, "count": len(lines)}))
        else:
            print(f"## Search: {query} ({engine})\n")
            for line in lines:
                print(f"  {line}")
    except (_sp.TimeoutExpired, OSError):
        error("Search failed")


def cmd_compact(args):
    """Compress text via Morph Apply."""
    client = get_morph_client()
    if not client:
        error("MORPH_API_KEY not set")

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
            error("Provide --file or stdin")

    try:
        output = client.compact(content, ratio)
        savings = int((1 - len(output) / len(content)) * 100) if len(content) > 0 else 0
        print(json.dumps({"success": True, "original": len(content), "compact": len(output), "savings": f"{savings}%"}))
        if getattr(args, "output", ""):
            Path(args.output).write_text(output)
        else:
            print(output)
    except Exception as exc:
        error(f"compact failed: {exc}")


def cmd_github_search(args):
    """Search GitHub repos via gh CLI."""
    query = " ".join(args.query) if args.query else ""
    if not query:
        error("Provide a search query")

    repo = getattr(args, "repo", "") or ""
    url = getattr(args, "url", "") or ""
    if not repo and not url:
        error("Provide --repo owner/repo or --url github-url")

    target = repo or url.replace("https://github.com/", "").rstrip("/")
    try:
        result = _sp.run(
            ["gh", "search", "code", query, "--repo", target, "--json", "repository,path,textMatches", "-L", "10"],
            check=False, capture_output=True, text=True, timeout=30,
        )
        if result.returncode == 0 and result.stdout.strip():
            data = json.loads(result.stdout)
            print(f"## GitHub Search: {query} in {target}\n")
            for item in data:
                path = item.get("path", "")
                repo_name = item.get("repository", {}).get("nameWithOwner", "")
                print(f"  {repo_name}/{path}")
                for match in item.get("textMatches", [])[:2]:
                    print(f"    > {match.get('fragment', '')[:100]}")
            print(f"\n  {len(data)} results found")
        else:
            error(f"gh search failed: {result.stderr[:200]}")
    except (OSError, _sp.TimeoutExpired) as exc:
        error(f"GitHub search error: {exc}")
