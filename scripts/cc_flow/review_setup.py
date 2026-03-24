"""Review backend detection and setup — cc-flow review-setup."""

import json
import os
import shutil

from cc_flow.core import CONFIG_FILE, safe_json_load


def _detect_backends():
    """Detect which review backends are available on this system."""
    backends = {}

    # Agent — always available
    backends["agent"] = {
        "available": True,
        "info": "Built-in cc-code reviewer agents (no setup needed)",
    }

    # RepoPrompt (rp-cli) — reuse rp.py detection for consistency
    try:
        from cc_flow.rp import find_rp_cli, is_mcp_available
        rp_available = find_rp_cli() is not None or is_mcp_available()
    except ImportError:
        # Fallback: manual check
        rp_path = os.path.expanduser("~/RepoPrompt/repoprompt_cli")
        rp_available = os.path.isfile(rp_path) and os.access(rp_path, os.X_OK)
        if not rp_available:
            rp_available = shutil.which("rp-cli") is not None
    backends["rp"] = {
        "available": rp_available,
        "info": "RepoPrompt GUI — deep file context via Builder (macOS/MCP)",
        "setup": None if rp_available else "Install RepoPrompt from https://repoprompt.com, then Settings → Install CLI to PATH",
    }

    # Codex CLI
    codex_available = shutil.which("codex") is not None
    backends["codex"] = {
        "available": codex_available,
        "info": "OpenAI Codex CLI — multi-model terminal review",
        "setup": None if codex_available else "Install: npm i -g @openai/codex",
    }

    # Export — always available
    backends["export"] = {
        "available": True,
        "info": "Export context markdown for external LLM (ChatGPT, Claude web)",
    }

    return backends


def _get_current_config():
    """Load current review config."""
    config = safe_json_load(CONFIG_FILE, default={})
    return {
        "review.backend": config.get("review.backend", "(not set → agent)"),
        "review.plan": config.get("review.plan", "(inherits default)"),
        "review.impl": config.get("review.impl", "(inherits default)"),
        "review.completion": config.get("review.completion", "(inherits default)"),
    }


def cmd_review_setup(args):
    """Detect available review backends and show/set configuration."""
    backends = _detect_backends()
    current = _get_current_config()

    # If --set provided, configure the backend
    backend_choice = getattr(args, "set", "") or ""
    if backend_choice:
        if backend_choice not in backends:
            print(json.dumps({
                "success": False,
                "error": f"Unknown backend: {backend_choice}. Choose from: {', '.join(backends.keys())}",
            }))
            return

        if not backends[backend_choice]["available"]:
            setup_hint = backends[backend_choice].get("setup", "")
            print(json.dumps({
                "success": False,
                "error": f"Backend '{backend_choice}' not available. {setup_hint}",
            }))
            return

        # Write to config
        config = safe_json_load(CONFIG_FILE, default={})
        scope = getattr(args, "scope", "") or ""
        if scope in ("plan", "impl", "completion"):
            config[f"review.{scope}"] = backend_choice
        else:
            config["review.backend"] = backend_choice
        CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
        CONFIG_FILE.write_text(json.dumps(config, indent=2) + "\n")

        print(json.dumps({
            "success": True,
            "message": f"Review backend set to '{backend_choice}'"
                       + (f" for {scope}" if scope else " (default)"),
        }))
        return

    # Detection mode — show what's available
    result = {
        "success": True,
        "backends": {},
        "current_config": current,
    }
    for name, info in backends.items():
        result["backends"][name] = {
            "available": info["available"],
            "info": info["info"],
        }
        if not info["available"] and info.get("setup"):
            result["backends"][name]["setup"] = info["setup"]

    print(json.dumps(result, indent=2))
