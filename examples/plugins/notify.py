"""cc-flow plugin: notify — show desktop notification on task events.

Install: cp notify.py .tasks/plugins/
Usage:   cc-flow done <id>  → triggers notification

Works on macOS (osascript), Linux (notify-send), or plain terminal bell.
"""

import subprocess
import sys

PLUGIN_NAME = "notify"
PLUGIN_VERSION = "1.0.0"
PLUGIN_DESCRIPTION = "Desktop notifications on task lifecycle events"


def _notify(title, message):
    """Send a notification (best-effort, no error on failure)."""
    if sys.platform == "darwin":
        subprocess.run(
            ["osascript", "-e", f'display notification "{message}" with title "{title}"'],
            check=False, capture_output=True,
        )
    elif sys.platform.startswith("linux"):
        subprocess.run(
            ["notify-send", title, message],
            check=False, capture_output=True,
        )
    else:
        print(f"\a[{title}] {message}")  # Terminal bell fallback


def on_task_done(task):
    """Called when a task is completed."""
    _notify("cc-flow: Task Done", f"{task.get('id', '?')}: {task.get('title', '')}")


def on_task_block(task):
    """Called when a task is blocked."""
    _notify("cc-flow: Task Blocked", f"{task.get('id', '?')}: {task.get('blocked_reason', '')}")
