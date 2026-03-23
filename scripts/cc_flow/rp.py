"""Unified RepoPrompt interface — auto-routes between rp-cli and MCP.

Transport selection (first match wins):
1. CC_RP_TRANSPORT env var: "cli" or "mcp"
2. cc-flow config: rp.transport
3. Auto-detect: MCP if in Claude Code session with RP MCP configured, else CLI

When to use which:
- CLI:  cc-flow scripts, Ralph, chained operations, pipe to files
- MCP:  Claude Code sessions, persistent tab binding, structured JSON

Both transports share the same Python API. Callers never need to know which
transport is active — just call rp.tree(), rp.chat(), etc.

Provides:
- Detection of rp-cli and RP MCP availability
- All RP operations with timeout, error handling, JSON parsing
- Window/tab state persistence (shared across worktrees via .git/cc-flow-state/)
- Worktree-aware workspace management
- Composite operations (setup-review, full review flow)
"""

import json
import os
import shlex
import shutil
import subprocess
from pathlib import Path
from typing import Any, Optional

from cc_flow.core import atomic_write, safe_json_load, state_dir

# --- Configuration ---

DEFAULT_TIMEOUT = int(os.environ.get("CC_RP_TIMEOUT", "1200"))  # 20 min
RP_SESSION_FILE = "rp-session.json"


# --- Transport detection ---

def find_rp_cli() -> Optional[str]:
    """Find rp-cli binary. Returns path or None."""
    rp = shutil.which("rp-cli")
    if rp:
        return rp
    home_rp = os.path.expanduser("~/RepoPrompt/repoprompt_cli")
    if os.path.isfile(home_rp) and os.access(home_rp, os.X_OK):
        return home_rp
    local_rp = "/usr/local/bin/rp-cli"
    if os.path.isfile(local_rp) and os.access(local_rp, os.X_OK):
        return local_rp
    return None


def is_mcp_available() -> bool:
    """Check if RP MCP tools are available in the current environment.

    MCP is available when running inside Claude Code with RP MCP server configured.
    Detection order:
    1. CLAUDE_CODE_SESSION env var (explicit session marker)
    2. CC_RP_MCP env var (explicit MCP override, e.g. set by hooks)
    3. Plugin-level .mcp.json discovery (Claude Code loads MCP via plugins)
    4. MCP socket file (RepoPrompt MCP Server running)
    """
    # Explicit session marker
    if os.environ.get("CLAUDE_CODE_SESSION"):
        return True
    # Explicit MCP override (useful when plugin provides MCP)
    if os.environ.get("CC_RP_MCP", "").lower() in ("1", "true"):
        return True
    # Plugin-level MCP discovery — Claude Code loads RP MCP via plugin .mcp.json
    # Check if discovery.json references RepoPrompt
    rp_mcp_dir = os.path.expanduser("~/Library/Application Support/RepoPrompt/MCP")
    discovery = os.path.join(rp_mcp_dir, "discovery.json")
    if os.path.isfile(discovery):
        try:
            import json as _json
            data = _json.loads(Path(discovery).read_text())
            servers = data.get("mcpServers", {})
            if "RepoPrompt" in servers:
                return True
        except (OSError, ValueError, KeyError):
            pass
    # MCP socket (RepoPrompt MCP Server actively running)
    mcp_socket = os.path.expanduser("~/Library/Application Support/RepoPrompt/mcp.sock")
    if os.path.exists(mcp_socket):
        return True
    return False


def detect_transport() -> str:
    """Detect the best transport to use.

    Returns: "cli", "mcp", or "none"
    """
    # Explicit override
    explicit = os.environ.get("CC_RP_TRANSPORT", "").lower()
    if explicit in ("cli", "mcp"):
        return explicit

    # Config override
    try:
        from cc_flow.core import CONFIG_FILE
        config = safe_json_load(CONFIG_FILE, default={})
        configured = config.get("rp.transport", "")
        if configured in ("cli", "mcp"):
            return configured
    except Exception:
        pass

    # Auto-detect
    has_cli = find_rp_cli() is not None
    has_mcp = is_mcp_available()

    if has_mcp and has_cli:
        # In Claude Code session → prefer MCP for persistent binding
        # In scripts/Ralph → prefer CLI for chaining
        if os.environ.get("CC_RALPH") == "1":
            return "cli"
        if os.environ.get("CLAUDE_CODE_SESSION"):
            return "mcp"
        return "cli"  # Default to CLI outside Claude Code
    if has_mcp:
        return "mcp"
    if has_cli:
        return "cli"
    return "none"


def require_rp_cli() -> str:
    """Ensure rp-cli is available. Raises RuntimeError if not found."""
    rp = find_rp_cli()
    if not rp:
        raise RuntimeError(
            "rp-cli not found. Install from RepoPrompt: Settings → MCP Server → Install CLI to PATH"
        )
    return rp


def rp_version() -> Optional[str]:
    """Get rp-cli version string. Returns None if unavailable."""
    rp = find_rp_cli()
    if not rp:
        return None
    try:
        result = subprocess.run(
            [rp, "--version"], capture_output=True, text=True, timeout=5,
        )
        return result.stdout.strip() or result.stderr.strip() or None
    except (subprocess.TimeoutExpired, subprocess.CalledProcessError, OSError):
        return None


def is_available() -> bool:
    """Check if any RP transport is available."""
    return detect_transport() != "none"


def available_transports() -> dict:
    """Return availability status of each transport."""
    return {
        "cli": find_rp_cli() is not None,
        "mcp": is_mcp_available(),
        "active": detect_transport(),
    }


# --- MCP transport helpers ---

def mcp_tool_call(tool: str, params: dict) -> str:
    """Generate an MCP tool call instruction for Claude Code.

    When transport is MCP, operations return instructions that Claude Code
    should execute via its native MCP tool system. This enables persistent
    tab binding and structured JSON responses.

    In practice, Claude Code skill/command layers should check transport
    and call MCP tools directly when transport is "mcp".
    """
    return json.dumps({
        "mcp_tool": f"repoprompt__{tool}",
        "params": params,
        "hint": "Call this MCP tool directly via Claude Code's tool system",
    })


# MCP tool name mapping (RP MCP tool names)
MCP_TOOLS = {
    "select": "manage_selection",
    "builder": "context_builder",
    "chat": "chat_send",
    "read": "read_file",
    "search": "file_search",
    "tree": "get_file_tree",
    "structure": "get_code_structure",
    "context": "workspace_context",
    "prompt": "prompt",
    "chats": "chats",
    "models": "list_models",
    "edit": "apply_edits",
    "file": "file_actions",
    "workspace": "manage_workspaces",
    "windows": "list_windows",
    "git": "git",
}


# --- Core execution ---

def run(
    args: list[str],
    *,
    timeout: Optional[int] = None,
    window: Optional[int] = None,
    tab: Optional[str] = None,
    raw_json: bool = False,
    quiet: bool = False,
    fail_fast: bool = False,
) -> subprocess.CompletedProcess:
    """Run rp-cli with error handling and timeout.

    Args:
        args: Command arguments (e.g., ["-e", "tree"])
        timeout: Max seconds. Default from CC_RP_TIMEOUT env or 1200s.
        window: Target window ID (prepended as -w <id>)
        tab: Target tab name/UUID (prepended as -t <name>)
        raw_json: Add --raw-json flag
        quiet: Add -q flag
        fail_fast: Add --fail-fast flag

    Returns:
        CompletedProcess with stdout/stderr

    Raises:
        RuntimeError: On rp-cli not found, timeout, or execution error
    """
    if timeout is None:
        timeout = DEFAULT_TIMEOUT

    rp = require_rp_cli()
    cmd = [rp]

    if window is not None:
        cmd.extend(["-w", str(window)])
    if tab is not None:
        cmd.extend(["-t", str(tab)])
    if raw_json:
        cmd.append("--raw-json")
    if quiet:
        cmd.append("-q")
    if fail_fast:
        cmd.append("--fail-fast")

    cmd.extend(args)

    try:
        return subprocess.run(
            cmd, capture_output=True, text=True, check=True, timeout=timeout
        )
    except subprocess.TimeoutExpired:
        raise RuntimeError(f"rp-cli timed out after {timeout}s: {' '.join(cmd)}")
    except subprocess.CalledProcessError as e:
        msg = (e.stderr or e.stdout or str(e)).strip()
        raise RuntimeError(f"rp-cli failed: {msg}")


def exec_cmd(
    command: str,
    *,
    window: Optional[int] = None,
    tab: Optional[str] = None,
    timeout: Optional[int] = None,
    raw_json: bool = False,
) -> str:
    """Execute an rp-cli exec command and return stdout.

    Args:
        command: The exec command string (e.g., "tree", "select set src/")
        window/tab/timeout/raw_json: Passed to run()

    Returns:
        stdout as string
    """
    result = run(
        ["-e", command],
        window=window, tab=tab, timeout=timeout, raw_json=raw_json,
    )
    return result.stdout


def call_tool(
    tool: str,
    params: dict[str, Any],
    *,
    window: Optional[int] = None,
    tab: Optional[str] = None,
    timeout: Optional[int] = None,
) -> str:
    """Call an MCP tool directly with JSON params.

    Args:
        tool: Tool name (e.g., "apply_edits", "file_actions")
        params: JSON-serializable dict
        window/tab/timeout: Passed to run()

    Returns:
        stdout as string
    """
    result = run(
        ["-c", tool, "-j", json.dumps(params)],
        window=window, tab=tab, timeout=timeout,
    )
    return result.stdout


# --- Session state (persistent across worktrees) ---

def _session_path() -> Path:
    """Return path to rp session state file."""
    return state_dir() / RP_SESSION_FILE


def load_session() -> dict:
    """Load persistent RP session state (window, tab, chat_id, etc.)."""
    return safe_json_load(_session_path(), default={})


def save_session(data: dict) -> None:
    """Save RP session state."""
    p = _session_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    atomic_write(p, json.dumps(data, indent=2) + "\n")


def get_window_tab() -> tuple[Optional[int], Optional[str]]:
    """Get saved window and tab from session state."""
    s = load_session()
    return s.get("window"), s.get("tab")


def set_window_tab(window: int, tab: str, **extra) -> None:
    """Save window and tab to session state."""
    s = load_session()
    s.update({"window": window, "tab": tab, **extra})
    save_session(s)


# --- Repo root detection ---

def repo_root() -> str:
    """Get the git repo root (works in worktrees too)."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, check=True,
        )
        return result.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return os.getcwd()


# --- High-level operations (all rp-cli tools) ---

# Windows & Workspaces

def windows(*, raw_json: bool = False) -> str:
    """List all open RepoPrompt windows."""
    return exec_cmd("windows", raw_json=raw_json)


def workspace_list(*, window: Optional[int] = None) -> str:
    """List workspaces in a window."""
    return exec_cmd("workspace list", window=window)


def workspace_switch(
    name: str,
    *,
    window: Optional[int] = None,
    new_window: bool = False,
) -> str:
    """Switch to a workspace."""
    cmd = f"workspace switch {shlex.quote(name)}"
    if new_window:
        cmd += " --new-window"
    return exec_cmd(cmd, window=window)


def workspace_create(
    name: str,
    *,
    window: Optional[int] = None,
    folder_path: Optional[str] = None,
    new_window: bool = False,
    switch: bool = True,
) -> str:
    """Create a new workspace."""
    cmd = f"workspace create {shlex.quote(name)}"
    if folder_path:
        cmd += f" --folder-path {shlex.quote(folder_path)}"
    if new_window:
        cmd += " --new-window"
    if switch:
        cmd += " --switch"
    return exec_cmd(cmd, window=window)


def workspace_delete(
    name: str,
    *,
    window: Optional[int] = None,
    close_window: bool = False,
) -> str:
    """Delete a workspace."""
    cmd = f"workspace delete {shlex.quote(name)}"
    if close_window:
        cmd += " --close-window"
    return exec_cmd(cmd, window=window)


def workspace_tabs(*, window: Optional[int] = None) -> str:
    """List tabs in current workspace."""
    return exec_cmd("workspace tabs", window=window)


def tab_create(
    name: str = "",
    *,
    window: Optional[int] = None,
    mode: str = "blank",
    source_tab: Optional[str] = None,
) -> str:
    """Create a new compose tab."""
    cmd = f"tabs create"
    if name:
        cmd += f" {shlex.quote(name)}"
    if mode == "fork":
        cmd += " --mode fork"
        if source_tab:
            cmd += f" --source-tab {shlex.quote(source_tab)}"
    return exec_cmd(cmd, window=window)


def tab_close(
    name: str,
    *,
    window: Optional[int] = None,
    allow_active: bool = False,
) -> str:
    """Close a compose tab."""
    cmd = f"tabs close {shlex.quote(name)}"
    if allow_active:
        cmd += " --allow-active"
    return exec_cmd(cmd, window=window)


# Selection

def select_set(
    paths: list[str],
    *,
    window: Optional[int] = None,
    tab: Optional[str] = None,
) -> str:
    """Replace selection with given paths."""
    quoted = " ".join(shlex.quote(p) for p in paths)
    return exec_cmd(f"select set {quoted}", window=window, tab=tab)


def select_add(
    paths: list[str],
    *,
    window: Optional[int] = None,
    tab: Optional[str] = None,
) -> str:
    """Add paths to selection."""
    quoted = " ".join(shlex.quote(p) for p in paths)
    return exec_cmd(f"select add {quoted}", window=window, tab=tab)


def select_remove(
    paths: list[str],
    *,
    window: Optional[int] = None,
    tab: Optional[str] = None,
) -> str:
    """Remove paths from selection."""
    quoted = " ".join(shlex.quote(p) for p in paths)
    return exec_cmd(f"select remove {quoted}", window=window, tab=tab)


def select_clear(
    *,
    window: Optional[int] = None,
    tab: Optional[str] = None,
) -> str:
    """Clear all selection."""
    return exec_cmd("select clear", window=window, tab=tab)


def select_get(
    *,
    window: Optional[int] = None,
    tab: Optional[str] = None,
) -> str:
    """Get current selection."""
    return exec_cmd("select get", window=window, tab=tab)


# Context Builder

def builder(
    instructions: str,
    *,
    response_type: Optional[str] = None,
    window: Optional[int] = None,
    tab: Optional[str] = None,
    raw_json: bool = False,
) -> str:
    """Run context builder.

    Args:
        instructions: Task description
        response_type: clarify (default), question, plan, review
    """
    cmd = f"builder {shlex.quote(instructions)}"
    if response_type:
        cmd += f" --type {response_type}"
    return exec_cmd(cmd, window=window, tab=tab, raw_json=raw_json)


# Chat

def chat(
    message: str,
    *,
    new_chat: bool = False,
    mode: Optional[str] = None,
    chat_id: Optional[str] = None,
    chat_name: Optional[str] = None,
    window: Optional[int] = None,
    tab: Optional[str] = None,
) -> str:
    """Send a chat message.

    Args:
        mode: "chat" (default), "plan", "edit", or "review".
              plan/review use their own rp-cli shorthand commands.
    """
    # plan and review have dedicated rp-cli commands
    if mode == "plan":
        return plan(message, window=window, tab=tab)
    if mode == "review":
        return review(message, window=window, tab=tab)

    cmd = f"chat {shlex.quote(message)}"
    if new_chat:
        cmd += " --new"
    if chat_name:
        cmd += f" --chat-name {shlex.quote(chat_name)}"
    return exec_cmd(cmd, window=window, tab=tab)


def chat_send_file(
    message_file: str,
    *,
    new_chat: bool = False,
    chat_name: Optional[str] = None,
    mode: str = "chat",
    window: Optional[int] = None,
    tab: Optional[str] = None,
) -> str:
    """Send a chat message from file (for long prompts)."""
    message = Path(message_file).read_text()
    params: dict[str, Any] = {
        "message": message,
        "new_chat": new_chat,
        "mode": mode,
    }
    if chat_name:
        params["chat_name"] = chat_name
    return call_tool("chat_send", params, window=window, tab=tab)


def plan(
    message: str,
    *,
    window: Optional[int] = None,
    tab: Optional[str] = None,
) -> str:
    """Send a plan request (starts new chat in plan mode)."""
    return exec_cmd(f"plan {shlex.quote(message)}", window=window, tab=tab)


def review(
    message: str = "",
    *,
    window: Optional[int] = None,
    tab: Optional[str] = None,
) -> str:
    """Send a review request (starts new chat in review mode)."""
    if message:
        return exec_cmd(f"review {shlex.quote(message)}", window=window, tab=tab)
    return exec_cmd("review", window=window, tab=tab)


# File operations

def read_file(
    path: str,
    *,
    start_line: Optional[int] = None,
    limit: Optional[int] = None,
    window: Optional[int] = None,
    tab: Optional[str] = None,
) -> str:
    """Read a file."""
    cmd = f"read {shlex.quote(path)}"
    if start_line is not None:
        cmd += f" {start_line}"
    if limit is not None:
        cmd += f" {limit}"
    return exec_cmd(cmd, window=window, tab=tab)


def search(
    pattern: str,
    *,
    extensions: Optional[list[str]] = None,
    context_lines: Optional[int] = None,
    max_results: Optional[int] = None,
    window: Optional[int] = None,
    tab: Optional[str] = None,
) -> str:
    """Search for a pattern."""
    cmd = f"search {shlex.quote(pattern)}"
    if extensions:
        cmd += f" --extensions {','.join(extensions)}"
    if context_lines is not None:
        cmd += f" --context-lines {context_lines}"
    if max_results is not None:
        cmd += f" --max-results {max_results}"
    return exec_cmd(cmd, window=window, tab=tab)


def tree(
    *,
    mode: Optional[str] = None,
    max_depth: Optional[int] = None,
    path: Optional[str] = None,
    window: Optional[int] = None,
    tab: Optional[str] = None,
) -> str:
    """Get file tree."""
    cmd = "tree"
    if mode:
        cmd += f" --{mode}"  # --folders, --selected, etc.
    if max_depth is not None:
        cmd += f" --max-depth {max_depth}"
    if path:
        cmd += f" {shlex.quote(path)}"
    return exec_cmd(cmd, window=window, tab=tab)


def structure(
    paths: list[str],
    *,
    max_results: Optional[int] = None,
    window: Optional[int] = None,
    tab: Optional[str] = None,
) -> str:
    """Get code structure (codemaps)."""
    quoted = " ".join(shlex.quote(p) for p in paths)
    cmd = f"structure {quoted}"
    if max_results:
        cmd += f" --max-results {max_results}"
    return exec_cmd(cmd, window=window, tab=tab)


# Context & Prompt

def context(
    *,
    include_all: bool = False,
    window: Optional[int] = None,
    tab: Optional[str] = None,
) -> str:
    """Get workspace context."""
    cmd = "context"
    if include_all:
        cmd += " --all"
    return exec_cmd(cmd, window=window, tab=tab)


def prompt_get(
    *,
    window: Optional[int] = None,
    tab: Optional[str] = None,
) -> str:
    """Get current prompt."""
    return exec_cmd("prompt get", window=window, tab=tab)


def prompt_set(
    text: str,
    *,
    window: Optional[int] = None,
    tab: Optional[str] = None,
) -> str:
    """Set prompt text."""
    return call_tool("prompt", {"op": "set", "text": text}, window=window, tab=tab)


def prompt_export(
    path: str,
    *,
    window: Optional[int] = None,
    tab: Optional[str] = None,
) -> str:
    """Export full LLM-ready context to file."""
    return exec_cmd(f"prompt export {shlex.quote(path)}", window=window, tab=tab)


# Chats

def chats_list(
    *,
    scope: str = "workspace",
    limit: Optional[int] = None,
    window: Optional[int] = None,
    tab: Optional[str] = None,
) -> str:
    """List chats."""
    cmd = f"chats list --scope {scope}"
    if limit:
        cmd += f" --limit {limit}"
    return exec_cmd(cmd, window=window, tab=tab)


def chats_log(
    *,
    scope: str = "tab",
    chat_id: Optional[str] = None,
    limit: Optional[int] = None,
    include_diffs: bool = False,
    window: Optional[int] = None,
    tab: Optional[str] = None,
) -> str:
    """Get chat log/history."""
    cmd = f"chats log --scope {scope}"
    if chat_id:
        cmd += f" --chat-id {chat_id}"
    if limit:
        cmd += f" --limit {limit}"
    if include_diffs:
        cmd += " --include-diffs"
    return exec_cmd(cmd, window=window, tab=tab)


# Models

def models(
    *,
    window: Optional[int] = None,
) -> str:
    """List available AI model presets."""
    return exec_cmd("models", window=window)


# Edits & File Actions

def apply_edits(
    path: str,
    *,
    search: Optional[str] = None,
    replace: Optional[str] = None,
    rewrite: Optional[str] = None,
    edits: Optional[list[dict]] = None,
    replace_all: bool = False,
    verbose: bool = False,
    window: Optional[int] = None,
    tab: Optional[str] = None,
) -> str:
    """Apply file edits via MCP tool."""
    params: dict[str, Any] = {"path": path}
    if rewrite is not None:
        params["rewrite"] = rewrite
    elif edits is not None:
        params["edits"] = edits
    elif search is not None and replace is not None:
        params["search"] = search
        params["replace"] = replace
        if replace_all:
            params["all"] = True
    if verbose:
        params["verbose"] = True
    return call_tool("apply_edits", params, window=window, tab=tab)


def file_actions(
    action: str,
    path: str,
    *,
    content: Optional[str] = None,
    new_path: Optional[str] = None,
    window: Optional[int] = None,
    tab: Optional[str] = None,
) -> str:
    """Create, delete, or move files."""
    params: dict[str, Any] = {"action": action, "path": path}
    if content is not None:
        params["content"] = content
    if new_path is not None:
        params["new_path"] = new_path
    return call_tool("file_actions", params, window=window, tab=tab)


# Git

def git(
    op: str,
    *,
    repo_root_name: Optional[str] = None,
    compare: Optional[str] = None,
    detail: Optional[str] = None,
    count: Optional[int] = None,
    ref: Optional[str] = None,
    path: Optional[str] = None,
    lines: Optional[str] = None,
    artifacts: bool = False,
    window: Optional[int] = None,
    tab: Optional[str] = None,
) -> str:
    """Run git operations via RP."""
    cmd = f"git {op}"
    if repo_root_name:
        cmd += f" --repo-root {shlex.quote(repo_root_name)}"
    if compare:
        cmd += f" --compare {compare}"
    if detail:
        cmd += f" --{detail}"  # --files, --patches, --full
    if count:
        cmd += f" --count {count}"
    if ref:
        cmd += f" {shlex.quote(ref)}"
    if path:
        cmd += f" {shlex.quote(path)}"
    if lines:
        cmd += f" --lines {lines}"
    if artifacts:
        cmd += " --artifacts"
    return exec_cmd(cmd, window=window, tab=tab)


# --- Composite operations ---

def setup_review(
    summary: str,
    *,
    root: Optional[str] = None,
    create: bool = True,
    response_type: Optional[str] = None,
) -> dict:
    """Atomic setup: pick window matching repo root + run builder.

    Returns dict with window, tab, and optionally review response.
    Saves window/tab to session state for subsequent calls.
    """
    if root is None:
        root = repo_root()
    root = os.path.realpath(root)

    # Step 1: Find matching window
    raw = exec_cmd("windows", raw_json=True)
    try:
        win_data = json.loads(raw)
    except json.JSONDecodeError:
        win_data = raw

    # Parse windows - try to find one matching our repo root
    win_id = _find_window_for_root(root, raw)

    if win_id is None and create:
        # Auto-create workspace in new window
        ws_name = os.path.basename(root)
        try:
            workspace_create(ws_name, folder_path=root, new_window=True)
            # Re-scan to find the new window
            raw = exec_cmd("windows", raw_json=True)
            win_id = _find_window_for_root(root, raw)
        except RuntimeError:
            pass

    if win_id is None:
        raise RuntimeError(f"No RepoPrompt window matches repo root: {root}")

    # Step 2: Run builder
    builder_cmd = f"builder {json.dumps(summary)}"
    if response_type:
        builder_cmd += f" --type {response_type}"

    builder_out = exec_cmd(builder_cmd, window=win_id, raw_json=bool(response_type))

    # Parse tab from output
    tab_id = _parse_tab_from_output(builder_out)

    # Save session state
    session_data = {"window": win_id, "tab": tab_id, "repo_root": root}
    if response_type == "review":
        try:
            data = json.loads(builder_out)
            session_data["chat_id"] = data.get("review", {}).get("chat_id", "")
            session_data["review_response"] = data.get("review", {}).get("response", "")
        except json.JSONDecodeError:
            pass

    save_session(session_data)
    return session_data


def _find_window_for_root(root: str, windows_output: str) -> Optional[int]:
    """Parse windows output and find one matching repo root."""
    # Normalize root for comparison
    roots = [root]
    if root.startswith("/private/tmp/"):
        roots.append("/tmp/" + root[len("/private/tmp/"):])
    elif root.startswith("/tmp/"):
        roots.append("/private/tmp/" + root[len("/tmp/"):])

    # Try JSON parse first
    try:
        data = json.loads(windows_output)
        if isinstance(data, list):
            for win in data:
                wid = win.get("id") or win.get("window_id")
                for rp in win.get("root_paths", []):
                    if rp in roots:
                        return int(wid)
            # Single window with no roots - use it
            if len(data) == 1:
                wid = data[0].get("id") or data[0].get("window_id")
                if wid and not data[0].get("root_paths"):
                    return int(wid)
    except (json.JSONDecodeError, ValueError, TypeError):
        pass

    # Fallback: parse text output for window IDs
    import re
    for line in windows_output.splitlines():
        for r in roots:
            if r in line:
                m = re.search(r"(?:window|id)[:\s]*(\d+)", line, re.IGNORECASE)
                if m:
                    return int(m.group(1))
    return None


def _parse_tab_from_output(output: str) -> str:
    """Extract tab ID from builder output."""
    import re
    # Try JSON
    try:
        data = json.loads(output)
        return str(data.get("tab_id") or data.get("tab") or "")
    except (json.JSONDecodeError, ValueError):
        pass
    # Try T=<tab> pattern
    m = re.search(r"T=(\S+)", output)
    if m:
        return m.group(1)
    # Try "Tab: <id>" pattern
    m = re.search(r"(?:tab|Tab)[:\s]+(\S+)", output)
    if m:
        return m.group(1)
    return ""


# --- Worktree integration ---

def setup_worktree_workspace(
    worktree_path: str,
    *,
    window: Optional[int] = None,
) -> dict:
    """Create or switch to a workspace for a worktree.

    Each worktree gets its own RP workspace (named after the worktree dir).
    Uses MCP manage_workspaces when available (persistent binding, no subprocess).
    Falls back to CLI for scripts/Ralph.
    Returns session state with window and tab info.
    """
    wt_name = os.path.basename(worktree_path)
    wt_path = os.path.realpath(worktree_path)

    # Try to find existing workspace, or create new
    try:
        workspace_switch(wt_name, window=window)
    except RuntimeError:
        workspace_create(wt_name, folder_path=wt_path, window=window)

    session = {"workspace": wt_name, "worktree_path": wt_path}
    if window:
        session["window"] = window
    save_session(session)
    return session


def cleanup_worktree_workspace(
    worktree_path: str,
    *,
    window: Optional[int] = None,
    close_window: bool = False,
) -> None:
    """Remove workspace for a deleted worktree."""
    wt_name = os.path.basename(worktree_path)
    try:
        workspace_delete(wt_name, window=window, close_window=close_window)
    except RuntimeError:
        pass  # Workspace already gone


def worktree_git_status(
    branch: str,
    *,
    window: Optional[int] = None,
    tab: Optional[str] = None,
) -> str:
    """Get git status for a specific worktree by branch name.

    Uses RP's @main:<branch> syntax to target a worktree without switching
    workspace. Useful for monitoring parallel worktree progress.
    """
    return git(
        "status",
        repo_root_name=f"@main:{branch}",
        window=window,
        tab=tab,
    )


def worktree_diff(
    branch: str,
    *,
    compare: str = "main",
    detail: str = "files",
    window: Optional[int] = None,
    tab: Optional[str] = None,
) -> str:
    """Get diff for a worktree branch vs trunk.

    Uses RP's @main:<branch> syntax — no workspace switch needed.
    """
    return git(
        "diff",
        repo_root_name=f"@main:{branch}",
        compare=compare,
        detail=detail,
        window=window,
        tab=tab,
    )
