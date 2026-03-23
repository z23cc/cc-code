"""Core utilities for cc-flow — shared across all command modules."""

import json
import os
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

TASKS_DIR = Path(".tasks")
EPICS_DIR = TASKS_DIR / "epics"
TASKS_SUBDIR = TASKS_DIR / "tasks"
COMPLETED_DIR = TASKS_DIR / "completed"
META_FILE = TASKS_DIR / "meta.json"
LEARNINGS_DIR = TASKS_DIR / "learnings"
CONFIG_FILE = TASKS_DIR / "config.json"
LOG_FILE = Path("improvement-results.tsv")

ROUTE_STATS_FILE = TASKS_DIR / "route_stats.json"
SESSION_DIR = TASKS_DIR / ".sessions"


# ── Cross-worktree state sharing ──

def _git_common_dir():
    """Return the git common dir (shared across worktrees).

    In a worktree, `git rev-parse --git-common-dir` returns the main repo's
    .git directory, which is shared. In a normal checkout, it returns .git.
    """
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--git-common-dir"],
            capture_output=True, text=True, check=True,
        )
        return Path(result.stdout.strip())
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def state_dir():
    """Return the shared state directory for cross-worktree task state.

    Priority:
    1. CC_FLOW_STATE_DIR env var (explicit override)
    2. <git-common-dir>/cc-flow-state/ (shared across worktrees)
    3. .tasks/ (fallback — same as TASKS_DIR)
    """
    env = os.environ.get("CC_FLOW_STATE_DIR")
    if env:
        p = Path(env)
        p.mkdir(parents=True, exist_ok=True)
        return p

    git_common = _git_common_dir()
    if git_common and git_common.is_dir():
        p = git_common / "cc-flow-state"
        p.mkdir(parents=True, exist_ok=True)
        return p

    return TASKS_DIR


def state_tasks_dir():
    """Return the shared task state directory."""
    d = state_dir() / "tasks"
    d.mkdir(parents=True, exist_ok=True)
    return d


def load_task_state(task_id):
    """Load runtime state for a task from the shared state directory.

    Runtime state (status, assignee, started, completed) is stored separately
    from the task spec so it can be shared across worktrees without merge conflicts.
    Returns empty dict if no state file exists.
    """
    state_file = state_tasks_dir() / f"{task_id}.json"
    return safe_json_load(state_file, default={})


def save_task_state(task_id, state):
    """Save runtime state for a task to the shared state directory."""
    state_file = state_tasks_dir() / f"{task_id}.json"
    atomic_write(state_file, json.dumps(state, indent=2) + "\n")


def load_task_merged(task_id):
    """Load task with spec (from .tasks/) merged with runtime state (from shared dir).

    Spec fields: id, epic, title, depends_on, size, tags, priority
    Runtime fields: status, assignee, started, completed, duration_sec, summary, diff
    """
    task_file = TASKS_SUBDIR / f"{task_id}.json"
    spec = safe_json_load(task_file, default=None)
    if spec is None:
        return None
    runtime = load_task_state(task_id)
    # Runtime fields override spec fields (runtime is source of truth for state)
    merged = {**spec, **runtime}
    return merged

DEFAULT_CONFIG = {
    "auto_consolidate": True,
    "max_iterations": 20,
    "default_size": "M",
    "scan_tools": ["ruff", "mypy", "bandit"],
    "auto_learn_on_done": True,
    "routing_confidence_threshold": 30,
}

_MISSING = object()


def now_iso():
    """Return current UTC time as ISO 8601 string."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def error(msg, code=1):
    """Print JSON error and exit."""
    print(json.dumps({"success": False, "error": msg}))
    sys.exit(code)


# ── Atomic file operations ──

def atomic_write(path, content):
    """Write content to file atomically via temp file + rename.

    Prevents data corruption from partial writes or concurrent access.
    Works on all platforms (Unix, macOS, Windows).
    """
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(p.parent), suffix=".tmp")
    try:
        os.write(fd, content.encode("utf-8"))
        os.close(fd)
        os.replace(tmp, str(p))  # atomic on all platforms
    except BaseException:
        os.close(fd) if not os.get_inheritable(fd) else None
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


def _file_lock(f, exclusive=True):
    """Cross-platform file locking (Unix fcntl / Windows msvcrt)."""
    try:
        import fcntl
        fcntl.flock(f, fcntl.LOCK_EX if exclusive else fcntl.LOCK_SH)
    except ImportError:
        try:
            import msvcrt
            msvcrt.locking(f.fileno(), msvcrt.LK_LOCK if exclusive else msvcrt.LK_NBLCK, 1)
        except ImportError:
            pass  # No locking available — best effort


def _file_unlock(f):
    """Cross-platform file unlocking."""
    try:
        import fcntl
        fcntl.flock(f, fcntl.LOCK_UN)
    except ImportError:
        try:
            import msvcrt
            msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)
        except ImportError:
            pass


# ── JSON operations ──

def safe_read(path, default=""):
    """Read file text safely. Returns default on any failure."""
    try:
        return Path(path).read_text()
    except (OSError, UnicodeDecodeError):
        return default


def safe_json_load(path, default=_MISSING):
    """Safely load JSON from a file. Returns default on any failure."""
    p = Path(path)
    if not p.exists():
        if default is not _MISSING:
            return default
        error(f"File not found: {path}")
    try:
        return json.loads(p.read_text())
    except json.JSONDecodeError as exc:
        if default is not _MISSING:
            return default
        error(f"Corrupted JSON in {path}: {exc}")
    except OSError as exc:
        if default is not _MISSING:
            return default
        error(f"Cannot read {path}: {exc}")
    return default  # unreachable but satisfies type checker


def locked_meta_update(fn):
    """Read-modify-write meta.json with cross-platform file locking."""
    META_FILE.parent.mkdir(parents=True, exist_ok=True)
    META_FILE.touch(exist_ok=True)
    with open(META_FILE, "r+") as f:
        _file_lock(f)
        try:
            content = f.read().strip()
            try:
                meta = json.loads(content) if content else {"next_epic": 1}
            except json.JSONDecodeError:
                meta = {"next_epic": 1}
            result = fn(meta)
            f.seek(0)
            f.truncate()
            f.write(json.dumps(meta, indent=2) + "\n")
        finally:
            _file_unlock(f)
    return result


def load_meta():
    """Load .tasks/meta.json, returning defaults if missing."""
    return safe_json_load(META_FILE, default={"next_epic": 1})


def save_meta(meta):
    """Write meta.json atomically."""
    atomic_write(META_FILE, json.dumps(meta, indent=2) + "\n")


def slugify(title):
    """Convert title to URL-safe slug. Strips special characters."""
    import re
    clean = re.sub(r"[^a-z0-9\u4e00-\u9fff\s-]", "", title.lower())
    return "-".join(clean.split()[:4])


def allocate_epic_num(meta):
    """Allocate next epic number and increment counter."""
    n = meta["next_epic"]
    meta["next_epic"] = n + 1
    return n


def resolve_task_id(task_id):
    """Resolve a potentially abbreviated task ID to the full ID.

    Supports: exact match, prefix match, and epic-N.M → epic-N-slug.M shorthand.
    """
    if not TASKS_SUBDIR.exists():
        return task_id
    # Exact match
    if (TASKS_SUBDIR / f"{task_id}.json").exists():
        return task_id
    # Prefix match
    candidates = [f.stem for f in TASKS_SUBDIR.glob("*.json") if f.stem.startswith(task_id)]
    if len(candidates) == 1:
        return candidates[0]
    # Shorthand: epic-1.3 → epic-1-*.3
    if "." in task_id:
        prefix, num = task_id.rsplit(".", 1)
        candidates = [f.stem for f in TASKS_SUBDIR.glob("*.json")
                      if f.stem.startswith(prefix) and f.stem.endswith(f".{num}")]
        if len(candidates) == 1:
            return candidates[0]
    return task_id


def resolve_epic_id(epic_id):
    """Resolve a potentially abbreviated epic ID to the full ID.

    Tries exact match first, then prefix match. Returns the full ID
    or the original if no match found.
    """
    if not EPICS_DIR.exists():
        return epic_id
    # Exact match
    if (EPICS_DIR / f"{epic_id}.md").exists():
        return epic_id
    # Prefix match
    candidates = [f.stem for f in EPICS_DIR.glob("*.md") if f.stem.startswith(epic_id)]
    if len(candidates) == 1:
        return candidates[0]
    return epic_id


def load_task(path):
    """Load a task JSON file."""
    return safe_json_load(path)


def save_task(path, data):
    """Write task JSON atomically (prevents corruption on concurrent access)."""
    atomic_write(path, json.dumps(data, indent=2) + "\n")


def all_tasks():
    """Load all task JSON files from .tasks/tasks/."""
    tasks = {}
    if not TASKS_SUBDIR.exists():
        return tasks
    for f in sorted(TASKS_SUBDIR.glob("*.json")):
        d = safe_json_load(f, default=None)
        if d and "id" in d:
            tasks[d["id"]] = d
    return tasks


def get_morph_client():
    """Try to create a MorphClient. Returns None if API key not set."""
    try:
        morph_dir = Path(__file__).parent.parent
        sys.path.insert(0, str(morph_dir))
        from morph_client import MorphClient
        return MorphClient()
    except (ImportError, ValueError):
        return None
