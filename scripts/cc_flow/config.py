"""cc-flow config commands — version, config, history."""

import json
from datetime import datetime

from cc_flow import VERSION
from cc_flow.core import (
    COMPLETED_DIR, CONFIG_FILE, DEFAULT_CONFIG, all_tasks, safe_json_load,
)


def cmd_version(_args):
    """Print cc-flow version."""
    print(json.dumps({"success": True, "version": VERSION}))


def cmd_history(_args):
    """Task completion timeline with velocity trends."""
    tasks = all_tasks()
    archived = []
    if COMPLETED_DIR.exists():
        for f in COMPLETED_DIR.glob("*.json"):
            try:
                archived.append(json.loads(f.read_text()))
            except json.JSONDecodeError:
                continue

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
