"""cc-flow config commands — version, config, history, clean."""

import json
from datetime import datetime, timezone

from cc_flow import VERSION
from cc_flow.core import (
    COMPLETED_DIR,
    CONFIG_FILE,
    DEFAULT_CONFIG,
    TASKS_DIR,
    all_tasks,
    safe_json_load,
)


def cmd_version(_args):
    """Print cc-flow version."""
    print(json.dumps({"success": True, "version": VERSION}))


def _safe_load_json(path):
    """Load JSON file, return None on decode error."""
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError:
        return None


def _load_archived_tasks():
    """Load archived task JSON files, skipping corrupt ones."""
    if not COMPLETED_DIR.exists():
        return []
    return [t for f in COMPLETED_DIR.glob("*.json") if (t := _safe_load_json(f)) is not None]


def cmd_history(_args):
    """Task completion timeline with velocity trends."""
    tasks = all_tasks()
    archived = _load_archived_tasks()

    all_done = [t for t in list(tasks.values()) + archived if t.get("completed")]
    all_done.sort(key=lambda t: t.get("completed", ""))

    if not all_done:
        print(json.dumps({"success": True, "entries": [], "count": 0}))
        return

    by_date = {}
    for t in all_done:
        by_date.setdefault(t["completed"][:10], []).append(t)

    dates = sorted(by_date.keys())
    entries = [{"date": d, "count": len(by_date[d]),
                "tasks": [{"id": t["id"], "title": t.get("title", "")} for t in by_date[d]]}
               for d in dates]

    if len(dates) >= 2:
        days = max((datetime.fromisoformat(dates[-1]) - datetime.fromisoformat(dates[0])).days, 1)
        daily_velocity = round(len(all_done) / days, 1)
    else:
        daily_velocity = len(all_done)

    print(json.dumps({
        "success": True, "entries": entries[-20:], "count": len(all_done),
        "daily_velocity": daily_velocity,
        "date_range": f"{dates[0]} → {dates[-1]}" if len(dates) >= 2 else dates[0],
    }))


def cmd_config(args):
    """View/set cc-flow configuration."""
    config = DEFAULT_CONFIG.copy()
    if CONFIG_FILE.exists():
        config.update(safe_json_load(CONFIG_FILE, default={}))

    if args.key and args.value:
        val = args.value
        if val.lower() in ("true", "false"):
            val = val.lower() == "true"
        elif val.isdigit():
            val = int(val)
        config[args.key] = val
        CONFIG_FILE.write_text(json.dumps(config, indent=2) + "\n")
        print(json.dumps({"success": True, "key": args.key, "value": val}))
    elif args.key:
        print(json.dumps({"success": True, "key": args.key, "value": config.get(args.key)}))
    else:
        print(json.dumps({"success": True, "config": config}))


PROFILES = {
    "default": {},
    "fast": {
        "max_iterations": 10,
        "default_size": "S",
        "routing_confidence_threshold": 20,
    },
    "strict": {
        "max_iterations": 30,
        "auto_consolidate": True,
        "auto_learn_on_done": True,
        "routing_confidence_threshold": 50,
        "scan_tools": ["ruff", "mypy", "bandit"],
    },
    "minimal": {
        "max_iterations": 5,
        "auto_consolidate": False,
        "auto_learn_on_done": False,
        "scan_tools": ["ruff"],
    },
}


def cmd_profile(args):
    """Apply a configuration profile or list available profiles."""
    action = getattr(args, "action", "list")

    if action == "list":
        result = {name: {"keys": len(overrides), "description": _profile_desc(name)}
                  for name, overrides in PROFILES.items()}
        print(json.dumps({"success": True, "profiles": result}))
        return

    name = getattr(args, "name", "")
    if name not in PROFILES:
        from cc_flow.core import error
        error(f"Unknown profile: {name}. Available: {', '.join(PROFILES.keys())}")

    config = DEFAULT_CONFIG.copy()
    config.update(PROFILES[name])
    CONFIG_FILE.write_text(json.dumps(config, indent=2) + "\n")
    print(json.dumps({"success": True, "profile": name, "config": config}))


def _profile_desc(name):
    """Brief description of a profile."""
    descs = {
        "default": "Standard settings",
        "fast": "Quick iterations, lower thresholds",
        "strict": "Thorough checks, higher confidence requirements",
        "minimal": "Lightweight, fewer tools, no auto-learning",
    }
    return descs.get(name, "")


def _age_days(path):
    """Get file age in days from modification time."""
    mtime = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
    return (datetime.now(timezone.utc) - mtime).days


def cmd_clean(args):
    """Remove old sessions and archived data. Default: older than 30 days."""
    max_age = getattr(args, "days", 30) or 30
    dry_run = getattr(args, "dry_run", False)
    removed = {"sessions": 0, "archived": 0}

    # Clean old sessions
    sessions_dir = TASKS_DIR / "sessions"
    if sessions_dir.exists():
        for f in sessions_dir.glob("*.json"):
            if _age_days(f) > max_age:
                if not dry_run:
                    f.unlink()
                removed["sessions"] += 1

    # Clean old archived tasks/epics
    if COMPLETED_DIR.exists():
        for f in COMPLETED_DIR.iterdir():
            if _age_days(f) > max_age:
                if not dry_run:
                    f.unlink()
                removed["archived"] += 1

    total = removed["sessions"] + removed["archived"]
    print(json.dumps({
        "success": True,
        "dry_run": dry_run,
        "removed": removed,
        "total": total,
        "max_age_days": max_age,
        "message": f"{'Would remove' if dry_run else 'Removed'} {total} files older than {max_age} days",
    }))
