"""cc-flow skill store — search and install skills from skills.sh ecosystem.

Wraps the `npx skills` CLI to integrate with the Vercel skills marketplace.
"""

import json
import subprocess

from cc_flow.core import error


def _run_skills(args_list, timeout=30):
    """Run npx skills command."""
    try:
        result = subprocess.run(
            ["npx", "skills", *args_list],
            check=False, capture_output=True, text=True, timeout=timeout,
        )
        return result.stdout.strip(), result.stderr.strip(), result.returncode
    except (subprocess.TimeoutExpired, OSError):
        return "", "timeout or npx not available", 1


def cmd_skills_find(args):
    """Search skills.sh for agent skills by keyword."""
    query = " ".join(args.query) if args.query else ""
    if not query:
        error("Provide a search query. Example: cc-flow skills find react testing")

    out, err, code = _run_skills(["find", query], timeout=30)
    if code != 0 and "not found" in err:
        error("skills CLI not available. Install: npm i -g skills")

    # Output raw results (skills CLI has its own formatting)
    if out:
        print(out)
    else:
        print(json.dumps({"success": False, "error": "No skills found", "query": query}))


def cmd_skills_add(args):
    """Install a skill from skills.sh."""
    package = args.package
    if not package:
        error("Provide a package. Example: cc-flow skills add vercel-labs/agent-skills@react-best-practices")

    global_flag = ["-g"] if getattr(args, "global_install", False) else []
    out, err, code = _run_skills(["add", package, "-y", *global_flag], timeout=60)

    if code == 0:
        print(json.dumps({"success": True, "package": package, "output": out[:200]}))
    else:
        print(json.dumps({"success": False, "package": package, "error": err[:200]}))


def cmd_skills_list(_args):
    """List installed skills."""
    out, _err, _code = _run_skills(["list"], timeout=15)
    if out:
        print(out)
    else:
        print(json.dumps({"success": True, "skills": [], "message": "No skills installed"}))
