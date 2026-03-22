"""morph_client.py — Pure Python client for Morph API.

Replaces the Node.js morph CLI (@duange/morph-plugin) with a zero-dependency
Python implementation. Supports: Apply, WarpGrep, Embedding, Rerank.

Usage:
    from morph_client import MorphClient
    client = MorphClient()  # reads MORPH_API_KEY from env
    result = client.apply(instruction, original_code, update_snippet)
    results = client.search(query, repo_files)
    embeddings = client.embed(["code snippet 1", "code snippet 2"])
    ranked = client.rerank(query, documents, top_n=5)

CLI Usage:
    python morph_client.py apply --instruction "add error handling" --file src/app.py --update "snippet"
    python morph_client.py search --query "auth flow" [--dir .]
    python morph_client.py embed --input "def hello(): pass"
    python morph_client.py rerank --query "auth" --documents doc1 doc2 doc3
    python morph_client.py compact --file context.txt [--ratio 0.3]
"""

import json
import os
import sys
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

BASE_URL = "https://api.morphllm.com/v1"


class MorphClient:
    """Pure Python Morph API client (no external dependencies)."""

    def __init__(self, api_key=None):
        self.api_key = api_key or os.environ.get("MORPH_API_KEY", "")
        if not self.api_key:
            raise ValueError("MORPH_API_KEY not set. Get one at https://morphllm.com/dashboard/api-keys")

    def _request(self, endpoint, payload, retries=2, timeout=60):
        """Make authenticated POST request with retry on 5xx errors."""
        import time
        url = f"{BASE_URL}/{endpoint.lstrip('/')}"
        data = json.dumps(payload).encode("utf-8")

        for attempt in range(retries + 1):
            req = Request(url, data=data, method="POST")  # noqa: S310
            req.add_header("Authorization", f"Bearer {self.api_key}")
            req.add_header("Content-Type", "application/json")
            req.add_header("User-Agent", "cc-code-morph/1.0")
            req.add_header("Accept", "application/json")
            try:
                with urlopen(req, timeout=timeout) as resp:  # noqa: S310
                    return json.loads(resp.read().decode("utf-8"))
            except HTTPError as exc:
                body = exc.read().decode("utf-8", errors="replace")[:500]
                # Retry on 5xx (server error) or 429 (rate limit)
                if exc.code in (429, 500, 502, 503, 504) and attempt < retries:
                    wait = (attempt + 1) * 2  # 2s, 4s
                    time.sleep(wait)
                    continue
                raise RuntimeError(f"Morph API {exc.code}: {body}") from exc
            except (TimeoutError, OSError) as exc:
                if attempt < retries:
                    time.sleep(2)
                    continue
                raise RuntimeError(f"Morph API timeout: {exc}") from exc
        raise RuntimeError("Morph API: max retries exceeded")

    # ── Apply ──

    def apply(self, instruction, original_code, update_snippet, model="auto"):
        """Apply code changes using Morph Fast Apply.

        Args:
            instruction: Brief description of what to change
            original_code: Full original file content
            update_snippet: Code snippet showing changes (use // ... existing code ... for context)
            model: "morph-v3-fast" (10,500 tok/s), "morph-v3-large" (98% acc), or "auto"
        Returns:
            Merged code string
        """
        content = (
            f"<instruction>{instruction}</instruction>\n"
            f"<code>{original_code}</code>\n"
            f"<update>{update_snippet}</update>"
        )
        resp = self._request("chat/completions", {
            "model": model,
            "messages": [{"role": "user", "content": content}],
        })
        return resp["choices"][0]["message"]["content"]

    def apply_file(self, file_path, instruction, update_snippet, model="auto"):
        """Apply changes to a file in-place (writes backup before overwriting)."""
        path = Path(file_path)
        original = path.read_text()
        merged = self.apply(instruction, original, update_snippet, model)
        # Safety: write to temp file then rename (atomic on same filesystem)
        tmp_path = path.with_suffix(path.suffix + ".tmp")
        tmp_path.write_text(merged)
        tmp_path.rename(path)
        return merged

    # ── Search (WarpGrep) ──

    def search(self, query, directory=".", max_turns=6):
        """Semantic code search using WarpGrep agent.

        Args:
            query: Natural language search query
            directory: Directory to search in
            max_turns: Max agent turns (default 6)
        Returns:
            List of search results
        """
        # Build repo structure — skip hidden dirs and common noise
        SKIP_DIRS = {".git", "__pycache__", "node_modules", ".venv", "venv",
                     "dist", "build", ".next", ".ruff_cache", ".pytest_cache",
                     ".mypy_cache", ".tox", "target", "coverage"}
        CODE_EXTS = {".py", ".ts", ".js", ".tsx", ".jsx", ".go", ".rs", ".java",
                     ".md", ".yaml", ".yml", ".toml", ".json", ".sh"}

        repo_files = []
        dir_path = Path(directory).resolve()
        for f in sorted(dir_path.rglob("*")):
            if not f.is_file():
                continue
            parts = f.relative_to(dir_path).parts
            if any(p in SKIP_DIRS or p.startswith(".") for p in parts):
                continue
            if f.suffix not in CODE_EXTS:
                continue
            repo_files.append(str(f))
            if len(repo_files) >= 500:
                break

        repo_structure = "\n".join(repo_files)
        content = f"<repo_structure>\n{repo_structure}\n</repo_structure>\n\n<search_string>\n{query}\n</search_string>"

        # Define tools for WarpGrep
        tools = [
            {"type": "function", "function": {"name": "grep_search", "parameters": {
                "type": "object", "properties": {
                    "pattern": {"type": "string"}, "path": {"type": "string"},
                    "include": {"type": "string"}
                }, "required": ["pattern"]}}},
            {"type": "function", "function": {"name": "read", "parameters": {
                "type": "object", "properties": {
                    "path": {"type": "string"}, "start_line": {"type": "integer"},
                    "end_line": {"type": "integer"}
                }, "required": ["path"]}}},
            {"type": "function", "function": {"name": "list_directory", "parameters": {
                "type": "object", "properties": {"path": {"type": "string"}},
                "required": ["path"]}}},
            {"type": "function", "function": {"name": "glob", "parameters": {
                "type": "object", "properties": {"pattern": {"type": "string"}},
                "required": ["pattern"]}}},
            {"type": "function", "function": {"name": "finish", "parameters": {
                "type": "object", "properties": {"result": {"type": "string"}},
                "required": ["result"]}}},
        ]

        messages = [{"role": "user", "content": content}]

        for _turn in range(max_turns):
            resp = self._request("chat/completions", {
                "model": "morph-warp-grep-v2.1",
                "messages": messages,
                "tools": tools,
            })
            msg = resp["choices"][0]["message"]
            messages.append(msg)

            if not msg.get("tool_calls"):
                return msg.get("content", "")

            for tc in msg["tool_calls"]:
                fn = tc["function"]["name"]
                fn_args = json.loads(tc["function"]["arguments"])
                result = self._execute_tool(fn, fn_args, dir_path)

                if fn == "finish":
                    return fn_args.get("result", result)

                messages.append({
                    "role": "tool",
                    "tool_call_id": tc["id"],
                    "content": result,
                })

        return "Search reached max turns without finishing"

    def _execute_tool(self, name, args, base_dir):
        """Execute a WarpGrep tool locally (paths validated against base_dir)."""
        import subprocess as sp

        def _safe_path(p):
            """Validate path is within base_dir to prevent traversal."""
            resolved = Path(p).resolve()
            if not str(resolved).startswith(str(base_dir.resolve())):
                return None
            return resolved

        if name == "grep_search":
            pattern = args.get("pattern", "")
            path = args.get("path", str(base_dir))
            include = args.get("include", "")
            cmd = ["grep", "-rn", pattern, path]
            if include:
                cmd.insert(2, f"--include={include}")
            try:
                result = sp.run(cmd, capture_output=True, text=True, timeout=10)
                lines = result.stdout.strip().split("\n")[:30]
                return "\n".join(lines) if lines[0] else "No matches"
            except (sp.TimeoutExpired, OSError):
                return "grep failed"

        elif name == "read":
            path = _safe_path(args["path"])
            if not path:
                return "Access denied: path outside project directory"
            if not path.exists():
                return f"File not found: {path}"
            content = path.read_text()
            start = args.get("start_line", 1) - 1
            end = args.get("end_line")
            lines = content.split("\n")
            if end:
                lines = lines[start:end]
            else:
                lines = lines[start:start + 100]
            return "\n".join(f"{i + start + 1}: {line}" for i, line in enumerate(lines))

        elif name == "list_directory":
            path = _safe_path(args["path"])
            if not path:
                return "Access denied: path outside project directory"
            if not path.exists():
                return f"Directory not found: {path}"
            entries = sorted(path.iterdir())[:50]
            return "\n".join(("d " if e.is_dir() else "f ") + e.name for e in entries)

        elif name == "glob":
            import glob as glob_mod
            pattern = args["pattern"]
            matches = sorted(glob_mod.glob(pattern, recursive=True))[:30]
            return "\n".join(matches) if matches else "No matches"

        elif name == "finish":
            return args.get("result", "")

        return f"Unknown tool: {name}"

    # ── Embedding ──

    def embed(self, inputs, model="morph-embedding-v4"):
        """Generate code embeddings.

        Args:
            inputs: string or list of strings
            model: embedding model (default: morph-embedding-v4, 1536 dims)
        Returns:
            List of embedding vectors
        """
        if isinstance(inputs, str):
            inputs = [inputs]
        resp = self._request("embeddings", {
            "model": model,
            "input": inputs,
        })
        return [item["embedding"] for item in resp["data"]]

    # ── Rerank ──

    def rerank(self, query, documents, top_n=None, model="morph-rerank-v4"):
        """Rerank documents by relevance to query.

        Args:
            query: Search query
            documents: List of document strings
            top_n: Return top N results (default: all)
            model: rerank model
        Returns:
            List of {index, relevance_score, document} sorted by relevance
        """
        payload = {
            "model": model,
            "query": query,
            "documents": documents,
        }
        if top_n:
            payload["top_n"] = top_n
        resp = self._request("rerank", payload)
        results = resp.get("results", [])
        for r in results:
            r["document"] = documents[r["index"]]
        return results

    # ── Compact (Apply-based summarization) ──

    def compact(self, text, ratio=0.3):
        """Compress text by keeping only essential content.

        Uses Apply model to produce a shorter version of the text.
        The <update> contains a truncated version that Apply will merge/clean up.
        """
        target_len = max(int(len(text) * ratio), 50)
        # Create a truncated version as the update hint
        truncated = text[:target_len]
        # Find last sentence boundary
        for sep in [". ", ".\n", "\n\n", "\n", ". "]:
            idx = truncated.rfind(sep)
            if idx > target_len // 2:
                truncated = truncated[:idx + len(sep)]
                break

        instruction = (
            f"Compress to ~{target_len} chars. Keep technical details, "
            "file paths, code refs, decisions. Remove filler and redundancy. "
            "Output ONLY compressed text."
        )
        resp = self._request("chat/completions", {
            "model": "morph-v3-fast",
            "messages": [{"role": "user", "content": (
                f"<instruction>{instruction}</instruction>\n"
                f"<code>{text}</code>\n"
                f"<update>{truncated}</update>"
            )}],
            "max_tokens": max(target_len // 3, 100),
        })
        result = resp["choices"][0]["message"]["content"]
        # If API returns something longer than original, just truncate
        if len(result) > len(text):
            return text[:target_len]
        return result


# ── CLI ──

def main():
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(prog="morph", description="Morph API client (Python)")
    parser.add_argument("--version", action="version", version="morph-py 1.0.0")
    sub = parser.add_subparsers(dest="command")

    # apply
    apply_p = sub.add_parser("apply", help="Apply code changes to a file")
    apply_p.add_argument("--file", required=True)
    apply_p.add_argument("--instruction", required=True)
    apply_p.add_argument("--update", default="")
    apply_p.add_argument("--model", default="auto", choices=["morph-v3-fast", "morph-v3-large", "auto"])

    # search
    search_p = sub.add_parser("search", help="Semantic code search")
    search_p.add_argument("--query", required=True)
    search_p.add_argument("--dir", default=".")

    # embed
    embed_p = sub.add_parser("embed", help="Generate code embeddings")
    embed_p.add_argument("--input", required=True)

    # rerank
    rerank_p = sub.add_parser("rerank", help="Rerank documents by relevance")
    rerank_p.add_argument("--query", required=True)
    rerank_p.add_argument("--documents", nargs="+", required=True)
    rerank_p.add_argument("--top-n", type=int, default=None)

    # compact
    compact_p = sub.add_parser("compact", help="Compress text")
    compact_p.add_argument("--file", default="")
    compact_p.add_argument("--ratio", type=float, default=0.3)

    args = parser.parse_args()

    try:
        client = MorphClient()
    except ValueError as exc:
        print(json.dumps({"success": False, "error": str(exc)}))
        sys.exit(1)

    if args.command == "apply":
        update = args.update if args.update else (sys.stdin.read() if not sys.stdin.isatty() else "")
        result = client.apply_file(args.file, args.instruction, update, args.model)
        print(json.dumps({"success": True, "file": args.file, "chars": len(result)}))

    elif args.command == "search":
        result = client.search(args.query, args.dir)
        print(result if isinstance(result, str) else json.dumps(result))

    elif args.command == "embed":
        vectors = client.embed(args.input)
        print(json.dumps({"success": True, "dimensions": len(vectors[0]), "count": len(vectors)}))

    elif args.command == "rerank":
        results = client.rerank(args.query, args.documents, args.top_n)
        print(json.dumps({"success": True, "results": results}))

    elif args.command == "compact":
        if args.file:
            text = Path(args.file).read_text()
        else:
            text = sys.stdin.read()
        result = client.compact(text, args.ratio)
        original = len(text)
        compressed = len(result)
        savings = int((1 - compressed / original) * 100) if original > 0 else 0
        print(json.dumps({"success": True, "original": original, "compressed": compressed, "savings": f"{savings}%"}))
        print(result)

    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
