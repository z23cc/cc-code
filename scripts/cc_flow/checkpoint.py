"""cc-flow checkpoint — save/compare workflow state snapshots."""

import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from cc_flow import skin


def _checkpoints_dir() -> Path:
    """Return path to the checkpoints directory."""
    return Path(".tasks") / ".checkpoints"


def _checkpoint_path(name: str) -> Path:
    """Return path to a specific checkpoint file."""
    return _checkpoints_dir() / f"{name}.json"


def _git_sha() -> str:
    """Get current git HEAD SHA (short)."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True, text=True, timeout=5,
        )
        return result.stdout.strip() if result.returncode == 0 else "unknown"
    except (OSError, subprocess.TimeoutExpired):
        return "unknown"


def _git_branch() -> str:
    """Get current git branch name."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True, text=True, timeout=5,
        )
        return result.stdout.strip() if result.returncode == 0 else "unknown"
    except (OSError, subprocess.TimeoutExpired):
        return "unknown"


def _count_files() -> int:
    """Count tracked files in the repo."""
    try:
        result = subprocess.run(
            ["git", "ls-files"],
            capture_output=True, text=True, timeout=10,
        )
        if result.returncode == 0:
            return len([l for l in result.stdout.strip().splitlines() if l])
        return 0
    except (OSError, subprocess.TimeoutExpired):
        return 0


def _count_tests() -> int:
    """Estimate test count by running cc-flow validate --json or counting test files."""
    try:
        result = subprocess.run(
            ["python", "-m", "cc_flow", "validate", "--json"],
            capture_output=True, text=True, timeout=15,
        )
        if result.returncode == 0 and result.stdout.strip():
            data = json.loads(result.stdout.strip())
            return data.get("test_count", 0)
    except (OSError, subprocess.TimeoutExpired, json.JSONDecodeError, ValueError):
        pass
    # Fallback: count test_*.py files
    count = 0
    for root, _dirs, files in os.walk("tests"):
        for f in files:
            if f.startswith("test_") and f.endswith(".py"):
                count += 1
    return count


def _files_changed_since(ref_sha: str) -> list[str]:
    """List files changed since a given git SHA."""
    if ref_sha == "unknown":
        return []
    try:
        result = subprocess.run(
            ["git", "diff", "--name-only", ref_sha, "HEAD"],
            capture_output=True, text=True, timeout=10,
        )
        if result.returncode == 0:
            return [l for l in result.stdout.strip().splitlines() if l]
        return []
    except (OSError, subprocess.TimeoutExpired):
        return []


def _create(name: str) -> None:
    """Save a checkpoint with current state."""
    cp_dir = _checkpoints_dir()
    cp_dir.mkdir(parents=True, exist_ok=True)

    data = {
        "name": name,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "git_sha": _git_sha(),
        "branch": _git_branch(),
        "files_count": _count_files(),
        "test_count": _count_tests(),
    }

    path = _checkpoint_path(name)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2) + "\n")
    tmp.replace(path)  # atomic

    skin.success(f"Checkpoint '{name}' created")
    skin.dim(f"  SHA: {data['git_sha']}  branch: {data['branch']}  "
             f"files: {data['files_count']}  tests: {data['test_count']}")


def _verify(name: str) -> None:
    """Compare current state vs a saved checkpoint."""
    path = _checkpoint_path(name)
    if not path.exists():
        skin.error(f"Checkpoint '{name}' not found")
        return

    saved = json.loads(path.read_text())
    current_sha = _git_sha()
    current_files = _count_files()
    current_tests = _count_tests()

    skin.heading(f"Verify: '{name}' vs current")

    # Git SHA
    if saved["git_sha"] == current_sha:
        skin.success(f"Same commit: {current_sha}")
    else:
        skin.info(f"Commit moved: {saved['git_sha']} -> {current_sha}")

    # Files changed
    changed = _files_changed_since(saved["git_sha"])
    if changed:
        skin.warning(f"{len(changed)} files changed since checkpoint")
        for f in changed[:10]:
            skin.dim(f"  {f}")
        if len(changed) > 10:
            skin.dim(f"  ... and {len(changed) - 10} more")
    else:
        skin.success("No files changed since checkpoint")

    # File count delta
    file_delta = current_files - saved["files_count"]
    if file_delta > 0:
        skin.info(f"Files: {saved['files_count']} -> {current_files} (+{file_delta} new)")
    elif file_delta < 0:
        skin.warning(f"Files: {saved['files_count']} -> {current_files} ({file_delta} deleted)")
    else:
        skin.success(f"File count unchanged: {current_files}")

    # Test count delta
    test_delta = current_tests - saved["test_count"]
    if test_delta > 0:
        skin.success(f"Tests: {saved['test_count']} -> {current_tests} (+{test_delta})")
    elif test_delta < 0:
        skin.warning(f"Tests: {saved['test_count']} -> {current_tests} ({test_delta})")
    else:
        skin.info(f"Test count unchanged: {current_tests}")


def _compare(name1: str, name2: str) -> None:
    """Diff two checkpoints."""
    path1 = _checkpoint_path(name1)
    path2 = _checkpoint_path(name2)

    if not path1.exists():
        skin.error(f"Checkpoint '{name1}' not found")
        return
    if not path2.exists():
        skin.error(f"Checkpoint '{name2}' not found")
        return

    cp1 = json.loads(path1.read_text())
    cp2 = json.loads(path2.read_text())

    skin.heading(f"Compare: '{name1}' vs '{name2}'")
    rows = [
        ("Timestamp", cp1["timestamp"], cp2["timestamp"]),
        ("Git SHA", cp1["git_sha"], cp2["git_sha"]),
        ("Branch", cp1["branch"], cp2["branch"]),
        ("Files", str(cp1["files_count"]), str(cp2["files_count"])),
        ("Tests", str(cp1["test_count"]), str(cp2["test_count"])),
    ]
    skin.table(["Field", name1, name2], rows)

    # Deltas
    file_delta = cp2["files_count"] - cp1["files_count"]
    test_delta = cp2["test_count"] - cp1["test_count"]
    print()
    sign_f = "+" if file_delta >= 0 else ""
    sign_t = "+" if test_delta >= 0 else ""
    skin.info(f"File delta: {sign_f}{file_delta}  |  Test delta: {sign_t}{test_delta}")

    # Files changed between the two SHAs
    if cp1["git_sha"] != "unknown" and cp2["git_sha"] != "unknown":
        changed = _files_changed_since(cp1["git_sha"])
        if changed:
            skin.info(f"{len(changed)} files changed between checkpoints")


def _list() -> None:
    """Show all checkpoints with timestamps."""
    cp_dir = _checkpoints_dir()
    if not cp_dir.exists():
        skin.info("No checkpoints found")
        return

    files = sorted(cp_dir.glob("*.json"))
    if not files:
        skin.info("No checkpoints found")
        return

    rows = []
    for f in files:
        try:
            data = json.loads(f.read_text())
            ts = data.get("timestamp", "?")
            # Truncate timestamp for display
            if len(ts) > 19:
                ts = ts[:19].replace("T", " ")
            rows.append((
                data.get("name", f.stem),
                ts,
                data.get("git_sha", "?"),
                data.get("branch", "?"),
                str(data.get("files_count", "?")),
                str(data.get("test_count", "?")),
            ))
        except (json.JSONDecodeError, OSError):
            rows.append((f.stem, "?", "?", "?", "?", "?"))

    skin.heading("Checkpoints")
    skin.table(["Name", "Timestamp", "SHA", "Branch", "Files", "Tests"], rows)


def cmd_checkpoint_create(args) -> None:
    """Handle: cc-flow checkpoint create <name>."""
    name = getattr(args, "name", None)
    if not name:
        skin.error("Name required: cc-flow checkpoint create <name>")
        return
    _create(name)


def cmd_checkpoint_verify(args) -> None:
    """Handle: cc-flow checkpoint verify <name>."""
    name = getattr(args, "name", None)
    if not name:
        skin.error("Name required: cc-flow checkpoint verify <name>")
        return
    _verify(name)


def cmd_checkpoint_compare(args) -> None:
    """Handle: cc-flow checkpoint compare <name1> <name2>."""
    name1 = getattr(args, "name1", None)
    name2 = getattr(args, "name2", None)
    if not name1 or not name2:
        skin.error("Two names required: cc-flow checkpoint compare <name1> <name2>")
        return
    _compare(name1, name2)


def cmd_checkpoint_list(args) -> None:
    """Handle: cc-flow checkpoint list."""
    _list()
