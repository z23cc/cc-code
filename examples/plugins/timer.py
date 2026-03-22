"""cc-flow plugin: timer — track time spent on tasks.

Install: cp timer.py .tasks/plugins/
Usage:   cc-flow timer start → start a pomodoro timer
         cc-flow timer stop  → stop and show elapsed

Also auto-logs time when tasks are started/done.
"""

import json
import time
from pathlib import Path

PLUGIN_NAME = "timer"
PLUGIN_VERSION = "1.0.0"
PLUGIN_DESCRIPTION = "Pomodoro timer + auto time tracking for tasks"

_TIMER_FILE = Path(".tasks/.timer")


def register_commands(subparsers):
    """Register timer commands."""
    p = subparsers.add_parser("timer", help="Pomodoro timer")
    p.add_argument("action", nargs="?", default="status", choices=["start", "stop", "status"])


def handle_command(cmd, args):
    """Handle timer commands."""
    if cmd != "timer":
        return False

    action = args.action

    if action == "start":
        _TIMER_FILE.parent.mkdir(parents=True, exist_ok=True)
        _TIMER_FILE.write_text(json.dumps({"started": time.time()}))
        print(json.dumps({"success": True, "action": "started", "message": "Timer started"}))

    elif action == "stop":
        if not _TIMER_FILE.exists():
            print(json.dumps({"success": False, "error": "No timer running"}))
            return True
        data = json.loads(_TIMER_FILE.read_text())
        elapsed = int(time.time() - data["started"])
        _TIMER_FILE.unlink()
        mins = elapsed // 60
        secs = elapsed % 60
        print(json.dumps({
            "success": True, "action": "stopped",
            "elapsed_sec": elapsed, "display": f"{mins}m {secs}s",
        }))

    else:  # status
        if _TIMER_FILE.exists():
            data = json.loads(_TIMER_FILE.read_text())
            elapsed = int(time.time() - data["started"])
            print(json.dumps({"success": True, "running": True, "elapsed_sec": elapsed}))
        else:
            print(json.dumps({"success": True, "running": False}))

    return True


def on_task_start(task):
    """Auto-start timer when task begins."""
    _TIMER_FILE.parent.mkdir(parents=True, exist_ok=True)
    _TIMER_FILE.write_text(json.dumps({
        "started": time.time(), "task_id": task.get("id", ""),
    }))
