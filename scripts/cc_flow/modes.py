"""Session-scoped safety modes — toggleable guards injected through hooks.

Modes:
  careful  — warn on destructive operations (rm -rf, DROP TABLE, git push -f, etc.)
  freeze   — block edits outside a frozen directory
  guard    — careful + freeze combined (maximum safety)

State is persisted in ~/.cc-code/modes.json so hooks can read it.
"""

import json
import os
from pathlib import Path

from cc_flow import skin


def _modes_file() -> Path:
    """Return path to the modes state file (~/.cc-code/modes.json)."""
    return Path.home() / ".cc-code" / "modes.json"


def get_modes() -> dict:
    """Read current mode state. Returns dict with careful, freeze, guard keys."""
    path = _modes_file()
    defaults = {"careful": False, "freeze": False, "freeze_dir": "", "guard": False}
    if not path.exists():
        return defaults
    try:
        data = json.loads(path.read_text())
        # Merge with defaults so new keys are always present
        for k, v in defaults.items():
            data.setdefault(k, v)
        return data
    except (json.JSONDecodeError, OSError):
        return defaults


def set_mode(name: str, enabled: bool, **kwargs) -> dict:
    """Toggle a mode and persist. Returns updated modes dict."""
    modes = get_modes()
    modes[name] = enabled

    # Handle compound guard mode
    if name == "guard":
        modes["careful"] = enabled
        modes["freeze"] = enabled
        if not enabled:
            modes["freeze_dir"] = ""

    # Handle freeze directory
    if name == "freeze" and "freeze_dir" in kwargs:
        modes["freeze_dir"] = kwargs["freeze_dir"] if enabled else ""

    if name == "guard" and "freeze_dir" in kwargs and enabled:
        modes["freeze_dir"] = kwargs["freeze_dir"]

    # Clear freeze_dir when disabling freeze
    if name == "freeze" and not enabled:
        modes["freeze_dir"] = ""

    # Persist
    path = _modes_file()
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(modes, indent=2) + "\n")
    tmp.replace(path)  # atomic

    return modes


def cmd_careful(args):
    """Enable or disable careful mode (warns on destructive operations)."""
    enable = getattr(args, "enable", False)
    disable = getattr(args, "disable", False)

    if not enable and not disable:
        # Show current state
        modes = get_modes()
        if modes["careful"]:
            skin.success("Careful mode is ON -- destructive operations will trigger warnings")
        else:
            skin.info("Careful mode is OFF")
        return

    enabled = enable and not disable
    modes = set_mode("careful", enabled)
    if enabled:
        skin.success("Careful mode ENABLED -- will warn on: rm -rf, DROP TABLE, git push -f, git reset --hard")
    else:
        skin.info("Careful mode disabled")


def cmd_freeze(args):
    """Freeze edits to a specific directory only."""
    disable = getattr(args, "disable", False)
    freeze_dir = getattr(args, "directory", None) or ""

    if disable:
        modes = set_mode("freeze", False)
        skin.info("Freeze mode disabled -- edits allowed everywhere")
        return

    if not freeze_dir:
        # Show current state
        modes = get_modes()
        if modes["freeze"]:
            skin.success(f"Freeze mode is ON -- edits restricted to: {modes['freeze_dir']}")
        else:
            skin.info("Freeze mode is OFF")
        return

    # Resolve to absolute path
    freeze_dir = str(Path(freeze_dir).resolve())
    if not os.path.isdir(freeze_dir):
        skin.error(f"Directory does not exist: {freeze_dir}")
        return

    modes = set_mode("freeze", True, freeze_dir=freeze_dir)
    skin.success(f"Freeze mode ENABLED -- edits restricted to: {freeze_dir}")


def cmd_guard(args):
    """Maximum safety: freeze + careful combined."""
    enable = getattr(args, "enable", False)
    disable = getattr(args, "disable", False)
    freeze_dir = getattr(args, "directory", None) or ""

    if not enable and not disable:
        modes = get_modes()
        if modes["guard"]:
            skin.success(f"Guard mode is ON (careful + freeze to: {modes['freeze_dir']})")
        else:
            skin.info("Guard mode is OFF")
        return

    if disable:
        modes = set_mode("guard", False)
        skin.info("Guard mode disabled (careful + freeze both OFF)")
        return

    # Enable guard
    if not freeze_dir:
        # Default to current working directory
        freeze_dir = os.getcwd()

    freeze_dir = str(Path(freeze_dir).resolve())
    if not os.path.isdir(freeze_dir):
        skin.error(f"Directory does not exist: {freeze_dir}")
        return

    modes = set_mode("guard", True, freeze_dir=freeze_dir)
    skin.success(f"Guard mode ENABLED (careful + freeze to: {freeze_dir})")
