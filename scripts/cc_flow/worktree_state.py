"""Cross-worktree state commands — state-path, migrate-state."""

import json

from cc_flow.core import (
    TASKS_SUBDIR,
    all_tasks,
    atomic_write,
    load_task,
    safe_json_load,
    save_task_state,
    state_dir,
    state_tasks_dir,
)

# Runtime fields that belong in shared state (not in spec)
_RUNTIME_FIELDS = {
    "status", "assignee", "started", "completed", "duration_sec",
    "summary", "git_sha_start", "blocked_reason", "blocked_at",
    "diff", "comments",
}


def cmd_state_path(args):
    """Print the resolved state directory path."""
    sd = state_dir()
    print(json.dumps({
        "success": True,
        "state_dir": str(sd),
        "tasks_dir": str(state_tasks_dir()),
    }))


def cmd_migrate_state(args):
    """Migrate runtime state from .tasks/tasks/*.json to shared state dir."""
    tasks = all_tasks()
    migrated = 0
    cleaned = 0

    for task_id, task_data in tasks.items():
        # Extract runtime fields
        runtime = {}
        for field in _RUNTIME_FIELDS:
            if field in task_data:
                runtime[field] = task_data[field]

        if not runtime:
            continue

        # Write to shared state dir
        save_task_state(task_id, runtime)
        migrated += 1

        # Optionally clean runtime fields from original JSON
        if getattr(args, "clean", False):
            task_file = TASKS_SUBDIR / f"{task_id}.json"
            original = safe_json_load(task_file, default={})
            spec_only = {k: v for k, v in original.items() if k not in _RUNTIME_FIELDS}
            atomic_write(task_file, json.dumps(spec_only, indent=2) + "\n")
            cleaned += 1

    print(json.dumps({
        "success": True,
        "migrated": migrated,
        "cleaned": cleaned,
        "state_dir": str(state_tasks_dir()),
    }))
