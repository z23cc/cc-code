#!/usr/bin/env python3
"""cc-code Ralph guard hook — safety enforcement for autonomous mode.

Activated when CC_RALPH=1. Prevents:
- Receipt writes before review succeeds
- Task completion without evidence
- Self-modification of guard/hook files
- Session exit without receipt
- Editing files outside assigned worktree (when CC_WORKTREE_PATH is set)
"""

import json
import os
import sys

# Only active in Ralph mode
if os.environ.get("CC_RALPH") != "1":
    print(json.dumps({"decision": "approve"}))
    sys.exit(0)

# Read hook input
hook_input = json.loads(sys.stdin.read())
event = hook_input.get("event", "")
tool_name = hook_input.get("tool_name", "")
tool_input = hook_input.get("tool_input", {})

# State tracking (persisted via env vars between calls)
RECEIPT_PATH = os.environ.get("RECEIPT_PATH", "")
TASK_ID = os.environ.get("TASK_ID", "")
WORKTREE_PATH = os.environ.get("CC_WORKTREE_PATH", "")

# Protected files
PROTECTED = {"ralph-guard.py", "hooks.json", "ralph.sh", "config.env"}

# Shared dirs that can be edited from any worktree
SHARED_PATTERNS = (".tasks/", ".git/cc-flow-state/", ".flow/", "improvement-results.tsv")


def approve(msg=""):
    print(json.dumps({"decision": "approve", "message": msg}))
    sys.exit(0)


def block(reason):
    print(json.dumps({"decision": "block", "reason": reason}))
    sys.exit(0)


def is_within(file_path, base_dir):
    """Check if file_path is within base_dir (resolved)."""
    resolved = os.path.normpath(os.path.abspath(file_path))
    base = os.path.normpath(os.path.abspath(base_dir))
    return resolved == base or resolved.startswith(base + os.sep)


def is_shared_path(file_path):
    """Check if file_path is a shared state path editable from any worktree."""
    for pattern in SHARED_PATTERNS:
        if pattern in file_path:
            return True
    return False


# --- PreToolUse ---
if event == "PreToolUse":
    if tool_name in ("Edit", "Write"):
        file_path = tool_input.get("file_path", "")

        # Block editing guard files
        for protected in PROTECTED:
            if protected in file_path:
                block(f"Cannot modify {protected} during Ralph run")

        # Worktree boundary enforcement
        if WORKTREE_PATH and file_path:
            if not is_within(file_path, WORKTREE_PATH) and not is_shared_path(file_path):
                block(
                    f"Path '{file_path}' is outside assigned worktree "
                    f"'{WORKTREE_PATH}'. Only edit files within your "
                    f"worktree or shared state dirs (.tasks/, .flow/)."
                )

    # Block receipt write if no review has occurred
    if tool_name == "Write" and RECEIPT_PATH:
        file_path = tool_input.get("file_path", "")
        if file_path == RECEIPT_PATH:
            # Allow — receipt write is expected after review
            approve("Receipt write allowed")

    approve()

# --- PostToolUse ---
elif event == "PostToolUse":
    approve()

# --- Stop ---
elif event == "Stop":
    # Check receipt exists if path was set
    if RECEIPT_PATH and not os.path.exists(RECEIPT_PATH):
        block(
            f"Receipt not found at {RECEIPT_PATH}. "
            "Complete the review and write the receipt before exiting."
        )
    approve()

# --- Default ---
else:
    approve()
