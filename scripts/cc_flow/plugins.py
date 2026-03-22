"""cc-flow plugin system — discover, load, and manage user plugins.

Plugin structure (.tasks/plugins/my_plugin.py):

    PLUGIN_NAME = "my-plugin"
    PLUGIN_VERSION = "1.0.0"
    PLUGIN_DESCRIPTION = "What this plugin does"

    # Optional: register custom commands
    def register_commands(subparsers):
        p = subparsers.add_parser("my-cmd", help="My custom command")
        p.add_argument("--foo", default="bar")

    # Optional: handle custom commands
    def handle_command(cmd, args):
        if cmd == "my-cmd":
            print(json.dumps({"success": True, "foo": args.foo}))
            return True
        return False

    # Optional: lifecycle hooks
    def on_task_start(task):
        '''Called when a task is started.'''

    def on_task_done(task):
        '''Called when a task is completed.'''

    def on_task_block(task):
        '''Called when a task is blocked.'''
"""

import importlib.util
import json

from cc_flow.core import TASKS_DIR, error

# Plugin code can raise anything — use broad tuple for safety
_PLUGIN_ERRORS = (ImportError, AttributeError, TypeError, ValueError,
                  RuntimeError, OSError, KeyError, json.JSONDecodeError)

PLUGINS_DIR = TASKS_DIR / "plugins"
PLUGIN_REGISTRY_FILE = TASKS_DIR / "plugins.json"

_loaded_plugins = {}


def _load_plugin(path):
    """Load a single plugin module from file path."""
    name = path.stem
    if name in _loaded_plugins:
        return _loaded_plugins[name]

    spec = importlib.util.spec_from_file_location(f"cc_flow_plugin_{name}", str(path))
    if not spec or not spec.loader:
        return None

    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except _PLUGIN_ERRORS as exc:
        return {"name": name, "error": str(exc)}

    plugin_info = {
        "name": getattr(module, "PLUGIN_NAME", name),
        "version": getattr(module, "PLUGIN_VERSION", "0.0.0"),
        "description": getattr(module, "PLUGIN_DESCRIPTION", ""),
        "path": str(path),
        "module": module,
    }
    _loaded_plugins[name] = plugin_info
    return plugin_info


def discover_plugins():
    """Find and load all plugins from .tasks/plugins/."""
    if not PLUGINS_DIR.exists():
        return []
    plugins = []
    for f in sorted(PLUGINS_DIR.glob("*.py")):
        if f.name.startswith("_"):
            continue
        info = _load_plugin(f)
        if info:
            plugins.append(info)
    return plugins


def _get_registry():
    """Load plugin enabled/disabled state."""
    if PLUGIN_REGISTRY_FILE.exists():
        try:
            return json.loads(PLUGIN_REGISTRY_FILE.read_text())
        except (json.JSONDecodeError, OSError):
            pass
    return {"enabled": {}, "disabled": []}


def _save_registry(reg):
    """Save plugin registry."""
    PLUGIN_REGISTRY_FILE.write_text(json.dumps(reg, indent=2) + "\n")


def is_enabled(plugin_name):
    """Check if a plugin is enabled (default: enabled)."""
    reg = _get_registry()
    return plugin_name not in reg.get("disabled", [])


# ── Lifecycle hook dispatch ──

def fire_hook(hook_name, **kwargs):
    """Call a lifecycle hook on all enabled plugins."""
    results = []
    for plugin in discover_plugins():
        if "error" in plugin:
            continue
        if not is_enabled(plugin["name"]):
            continue
        module = plugin.get("module")
        hook_fn = getattr(module, hook_name, None)
        if hook_fn and callable(hook_fn):
            try:
                hook_fn(**kwargs)
                results.append({"plugin": plugin["name"], "hook": hook_name, "status": "ok"})
            except _PLUGIN_ERRORS as exc:
                results.append({"plugin": plugin["name"], "hook": hook_name, "status": "error",
                                "error": str(exc)})
    return results


# ── Plugin command registration ──

def register_plugin_commands(subparsers):
    """Let plugins register their custom commands."""
    for plugin in discover_plugins():
        if "error" in plugin or not is_enabled(plugin["name"]):
            continue
        module = plugin.get("module")
        register_fn = getattr(module, "register_commands", None)
        if register_fn and callable(register_fn):
            try:
                register_fn(subparsers)
            except _PLUGIN_ERRORS:
                pass


def dispatch_plugin_command(cmd, args):
    """Try to dispatch a command to a plugin. Returns True if handled."""
    for plugin in discover_plugins():
        if "error" in plugin or not is_enabled(plugin["name"]):
            continue
        module = plugin.get("module")
        handler = getattr(module, "handle_command", None)
        if handler and callable(handler):
            try:
                if handler(cmd, args):
                    return True
            except _PLUGIN_ERRORS:
                pass
    return False


# ── CLI commands for plugin management ──

def cmd_plugin_list(_args):
    """List all installed plugins."""
    plugins = discover_plugins()
    reg = _get_registry()
    disabled = reg.get("disabled", [])

    result = []
    for p in plugins:
        if "error" in p:
            result.append({"name": p.get("name", "?"), "status": "error", "error": p["error"]})
        else:
            name = p["name"]
            result.append({
                "name": name,
                "version": p["version"],
                "description": p["description"],
                "enabled": name not in disabled,
            })

    print(json.dumps({"success": True, "plugins": result, "count": len(result),
                       "dir": str(PLUGINS_DIR)}))


def cmd_plugin_enable(args):
    """Enable a plugin."""
    name = args.name
    reg = _get_registry()
    disabled = reg.get("disabled", [])
    if name in disabled:
        disabled.remove(name)
        reg["disabled"] = disabled
        _save_registry(reg)
    print(json.dumps({"success": True, "plugin": name, "enabled": True}))


def cmd_plugin_disable(args):
    """Disable a plugin."""
    name = args.name
    reg = _get_registry()
    disabled = reg.get("disabled", [])
    if name not in disabled:
        disabled.append(name)
        reg["disabled"] = disabled
        _save_registry(reg)
    print(json.dumps({"success": True, "plugin": name, "enabled": False}))


def cmd_plugin_create(args):
    """Scaffold a new plugin."""
    name = args.name
    PLUGINS_DIR.mkdir(parents=True, exist_ok=True)
    plugin_file = PLUGINS_DIR / f"{name}.py"

    if plugin_file.exists():
        error(f"Plugin already exists: {plugin_file}")

    template = f'''"""cc-flow plugin: {name}"""

import json

PLUGIN_NAME = "{name}"
PLUGIN_VERSION = "1.0.0"
PLUGIN_DESCRIPTION = "Description of {name} plugin"


def register_commands(subparsers):
    """Register custom commands."""
    p = subparsers.add_parser("{name}", help=PLUGIN_DESCRIPTION)
    p.add_argument("--example", default="hello")


def handle_command(cmd, args):
    """Handle custom commands. Return True if handled."""
    if cmd == "{name}":
        print(json.dumps({{"success": True, "plugin": PLUGIN_NAME,
                          "example": args.example}}))
        return True
    return False


def on_task_done(task):
    """Called when a task is completed."""
    pass
'''
    plugin_file.write_text(template)
    print(json.dumps({"success": True, "name": name, "file": str(plugin_file)}))
