"""Performance tracking — records command execution times.

Stores timing data in .tasks/perf.jsonl (JSON-lines, append-only).
Provides analytics: slowest commands, average times, trends.
"""

import json
import time

from cc_flow.core import TASKS_DIR

PERF_FILE = TASKS_DIR / "perf.jsonl"
MAX_ENTRIES = 500  # Keep last N entries


class PerfTimer:
    """Context manager to time command execution."""

    def __init__(self, command):
        self.command = command
        self.start = None

    def __enter__(self):
        self.start = time.monotonic()
        return self

    def __exit__(self, *_exc):
        elapsed_ms = int((time.monotonic() - self.start) * 1000)
        _append_entry(self.command, elapsed_ms)


MAX_FILE_BYTES = 50_000  # 50KB max


def _append_entry(command, elapsed_ms):
    """Append a timing entry to perf.jsonl with size guard."""
    PERF_FILE.parent.mkdir(parents=True, exist_ok=True)
    entry = json.dumps({"cmd": command, "ms": elapsed_ms, "ts": time.time()})
    with open(PERF_FILE, "a") as f:
        f.write(entry + "\n")

    # Trim if too many entries or file too large
    if PERF_FILE.exists():
        size = PERF_FILE.stat().st_size
        if size > MAX_FILE_BYTES:
            lines = PERF_FILE.read_text().strip().split("\n")
            trimmed = lines[-MAX_ENTRIES // 2:]  # Keep only recent half
            PERF_FILE.write_text("\n".join(trimmed) + "\n")


def load_perf_data():
    """Load all performance entries."""
    if not PERF_FILE.exists():
        return []
    entries = []
    for line in PERF_FILE.read_text().strip().split("\n"):
        if line.strip():
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return entries


def cmd_perf(args):
    """Show command performance analytics."""
    entries = load_perf_data()
    if not entries:
        print(json.dumps({"success": True, "entries": 0, "message": "No performance data yet."}))
        return

    # Aggregate by command
    by_cmd = {}
    for e in entries:
        cmd = e["cmd"]
        if cmd not in by_cmd:
            by_cmd[cmd] = {"count": 0, "total_ms": 0, "max_ms": 0, "min_ms": float("inf")}
        by_cmd[cmd]["count"] += 1
        by_cmd[cmd]["total_ms"] += e["ms"]
        by_cmd[cmd]["max_ms"] = max(by_cmd[cmd]["max_ms"], e["ms"])
        by_cmd[cmd]["min_ms"] = min(by_cmd[cmd]["min_ms"], e["ms"])

    # Build sorted summary
    summary = []
    for cmd, stats in sorted(by_cmd.items(), key=lambda x: -x[1]["total_ms"]):
        avg = stats["total_ms"] // stats["count"]
        summary.append({
            "command": cmd,
            "calls": stats["count"],
            "avg_ms": avg,
            "max_ms": stats["max_ms"],
            "min_ms": stats["min_ms"] if stats["min_ms"] != float("inf") else 0,
        })

    # Find slowest single execution
    slowest = max(entries, key=lambda e: e["ms"])

    top = getattr(args, "top", 10) or 10
    print(json.dumps({
        "success": True,
        "total_entries": len(entries),
        "commands": summary[:top],
        "slowest_single": {"command": slowest["cmd"], "ms": slowest["ms"]},
    }))
