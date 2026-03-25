"""cc-flow auto-ops — subprocess automation for worktree, commit, chain advance.

These operations were previously "instructions" that Claude had to execute.
Now they run as real subprocesses — zero manual intervention.
"""

import json
import os
import subprocess


def auto_worktree_create(name):
    """Create worktree via subprocess. Returns worktree path or None."""
    wt_script = _find_worktree_sh()
    if not wt_script:
        return None

    try:
        r = subprocess.run(
            ["bash", wt_script, "create", name],
            check=False, capture_output=True, text=True, timeout=30,
        )
        if r.returncode == 0:
            # Parse path from output
            for line in r.stdout.split("\n"):
                if "created:" in line or "already exists:" in line:
                    path = line.split(":")[-1].strip()
                    if path:
                        return path
            # Fallback: construct path
            repo_root = subprocess.run(
                ["git", "rev-parse", "--show-toplevel"],
                check=False, capture_output=True, text=True,
            ).stdout.strip()
            path = os.path.join(repo_root, ".claude", "worktrees", name)
            try:
                from cc_flow.dashboard_events import emit_worktree_event
                emit_worktree_event("create", name, path)
            except ImportError:
                pass
            return path
        return None
    except (subprocess.TimeoutExpired, OSError):
        return None


def auto_worktree_merge(name):
    """Merge worktree branch back to main and cleanup."""
    try:
        # Get current branch
        current = subprocess.run(
            ["git", "branch", "--show-current"],
            check=False, capture_output=True, text=True,
        ).stdout.strip()

        # Checkout main if not already
        if current != "main" and current != "master":
            subprocess.run(["git", "checkout", "main"], check=False, capture_output=True, timeout=10)

        # Merge
        r = subprocess.run(
            ["git", "merge", name, "--no-edit"],
            check=False, capture_output=True, text=True, timeout=30,
        )
        merged = r.returncode == 0

        # Remove worktree
        wt_script = _find_worktree_sh()
        if wt_script:
            subprocess.run(
                ["bash", wt_script, "remove", name],
                check=False, capture_output=True, timeout=15,
            )

        return merged
    except (subprocess.TimeoutExpired, OSError):
        return False


def auto_verify():
    """Run cc-flow verify. Returns True if all passed."""
    try:
        r = subprocess.run(
            ["cc-flow", "verify"],
            check=False, capture_output=True, text=True, timeout=300,
        )
        if r.stdout.strip():
            try:
                data = json.loads(r.stdout)
                return data.get("success", False)
            except json.JSONDecodeError:
                pass
        return r.returncode == 0
    except (subprocess.TimeoutExpired, OSError):
        return False


def auto_commit(message):
    """Stage all changes and commit. Returns True if successful."""
    try:
        # Stage
        subprocess.run(["git", "add", "-A"], check=False, capture_output=True, timeout=10)

        # Check if there's anything to commit
        status = subprocess.run(
            ["git", "diff", "--cached", "--quiet"],
            check=False, capture_output=True,
        )
        if status.returncode == 0:
            return True  # nothing to commit = success

        # Commit
        r = subprocess.run(
            ["git", "commit", "-m", message],
            check=False, capture_output=True, text=True, timeout=15,
        )
        return r.returncode == 0
    except (subprocess.TimeoutExpired, OSError):
        return False


def auto_chain_advance(data="{}"):
    """Advance chain to next step. Returns advance result or None."""
    try:
        r = subprocess.run(
            ["cc-flow", "chain", "advance", "--data", data],
            check=False, capture_output=True, text=True, timeout=10,
        )
        if r.stdout.strip():
            try:
                return json.loads(r.stdout)
            except json.JSONDecodeError:
                pass
        return None
    except (subprocess.TimeoutExpired, OSError):
        return None


def _find_worktree_sh():
    """Find worktree.sh script."""
    candidates = [
        os.path.join(os.environ.get("CLAUDE_PLUGIN_ROOT", ""), "scripts", "worktree.sh"),
        os.path.join(os.path.dirname(__file__), "..", "worktree.sh"),
    ]
    for path in candidates:
        if os.path.isfile(path):
            return path
    return None
