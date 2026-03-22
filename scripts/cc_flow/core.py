"""Core utilities for cc-flow — shared across all command modules."""

import json
import os
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
    """Convert title to URL-safe slug."""
    return "-".join(title.lower().split()[:4]).replace("/", "-").replace(".", "")


def allocate_epic_num(meta):
    """Allocate next epic number and increment counter."""
    n = meta["next_epic"]
    meta["next_epic"] = n + 1
    return n


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
