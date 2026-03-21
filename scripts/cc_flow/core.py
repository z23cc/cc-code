"""Core utilities for cc-flow — shared across all command modules."""

import json
import sys
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
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def error(msg, code=1):
    """Print JSON error and exit."""
    print(json.dumps({"success": False, "error": msg}))
    sys.exit(code)


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


def locked_meta_update(fn):
    """Read-modify-write meta.json with file locking."""
    import fcntl
    META_FILE.parent.mkdir(parents=True, exist_ok=True)
    META_FILE.touch(exist_ok=True)
    with open(META_FILE, "r+") as f:
        fcntl.flock(f, fcntl.LOCK_EX)
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
            fcntl.flock(f, fcntl.LOCK_UN)
    return result


def load_meta():
    return safe_json_load(META_FILE, default={"next_epic": 1})


def save_meta(meta):
    META_FILE.write_text(json.dumps(meta, indent=2) + "\n")


def slugify(title):
    return "-".join(title.lower().split()[:4]).replace("/", "-").replace(".", "")


def load_task(path):
    return safe_json_load(path)


def save_task(path, data):
    Path(path).write_text(json.dumps(data, indent=2) + "\n")


def all_tasks():
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
