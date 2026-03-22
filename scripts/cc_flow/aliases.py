"""cc-flow aliases — custom command shortcuts.

Store aliases in .tasks/aliases.json. Example:
  cc-flow alias set s "status"
  cc-flow alias set td "task create --epic epic-1 --title"
  cc-flow s  →  cc-flow status
"""

import json

from cc_flow.core import TASKS_DIR, error, safe_json_load

ALIAS_FILE = TASKS_DIR / "aliases.json"


def _load_aliases():
    return safe_json_load(ALIAS_FILE, default={})


def _save_aliases(aliases):
    ALIAS_FILE.parent.mkdir(parents=True, exist_ok=True)
    ALIAS_FILE.write_text(json.dumps(aliases, indent=2) + "\n")


def cmd_alias_list(_args):
    """List all defined aliases."""
    aliases = _load_aliases()
    print(json.dumps({"success": True, "aliases": aliases, "count": len(aliases)}))


def cmd_alias_set(args):
    """Set an alias: cc-flow alias set <name> <command>."""
    name = args.name
    command = " ".join(args.target)
    if not command:
        error("Provide a command for the alias")

    aliases = _load_aliases()
    aliases[name] = command
    _save_aliases(aliases)
    print(json.dumps({"success": True, "name": name, "command": command}))


def cmd_alias_remove(args):
    """Remove an alias."""
    name = args.name
    aliases = _load_aliases()
    if name not in aliases:
        error(f"Alias not found: {name}")
    del aliases[name]
    _save_aliases(aliases)
    print(json.dumps({"success": True, "removed": name}))


def resolve_alias(cmd, argv):
    """If cmd is an alias, return expanded (cmd, argv). Otherwise return None."""
    aliases = _load_aliases()
    if cmd in aliases:
        expanded = aliases[cmd].split()
        return expanded[0], expanded[1:] + argv
    return None
