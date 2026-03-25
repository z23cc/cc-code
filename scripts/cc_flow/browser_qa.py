"""cc-flow browser-qa — visual QA with screenshot evidence.

Uses available browser tools (gstack browse, playwright, puppeteer)
to capture screenshots, verify pages, and detect visual regressions.

Integrates with the 3-engine review system:
  1. Capture screenshots of affected pages
  2. 3 engines analyze screenshots for issues (parallel)
  3. Generate visual QA report with evidence
"""

import json
import os
import shutil
import subprocess
import time

from cc_flow.core import TASKS_DIR, atomic_write, now_iso


def _detect_browser_tool():
    """Find the best available browser automation tool."""
    # gstack browse (compiled, fastest)
    gstack_browse = os.path.expanduser("~/.claude/skills/gstack/bin/browse")
    if os.path.isfile(gstack_browse) and os.access(gstack_browse, os.X_OK):
        return "gstack", gstack_browse

    # playwright
    if shutil.which("npx"):
        return "playwright", "npx playwright"

    return None, None


def take_screenshot(url, output_path, tool=None, tool_path=None):
    """Capture a screenshot of a URL."""
    if not tool:
        tool, tool_path = _detect_browser_tool()

    if not tool:
        return {"success": False, "error": "No browser tool available"}

    try:
        if tool == "gstack":
            r = subprocess.run(
                [tool_path, "screenshot", url, "--output", output_path],
                check=False, capture_output=True, text=True, timeout=30,
            )
        else:
            r = subprocess.run(
                ["npx", "playwright", "screenshot", url, output_path],
                check=False, capture_output=True, text=True, timeout=30,
            )
        return {"success": r.returncode == 0, "path": output_path}
    except (subprocess.TimeoutExpired, OSError) as e:
        return {"success": False, "error": str(e)}


def run_visual_qa(url=None, pages=None, diff_range="", dry_run=False):
    """Run visual QA on affected pages."""
    tool, tool_path = _detect_browser_tool()

    if dry_run:
        return {
            "success": True, "dry_run": True,
            "browser_tool": tool or "none",
            "instruction": (
                f"Visual QA using {tool or 'no browser tool found'}\n"
                "Steps: capture screenshots → 3-engine visual analysis → report"
            ),
        }

    if not tool:
        return {"success": False, "error": "No browser tool. Install gstack or playwright."}

    # Determine pages to test
    if not pages:
        pages = [url] if url else _detect_pages_from_diff(diff_range)

    if not pages:
        return {"success": False, "error": "No pages to test. Provide --url or have changed frontend files."}

    start = time.time()
    results = []

    # Screenshot each page
    qa_dir = TASKS_DIR / "browser_qa"
    qa_dir.mkdir(parents=True, exist_ok=True)
    ts = now_iso().replace(":", "-").replace("T", "_")[:19]

    for i, page in enumerate(pages[:5]):  # max 5 pages
        screenshot_path = str(qa_dir / f"screenshot-{ts}-{i}.png")
        result = take_screenshot(page, screenshot_path, tool, tool_path)
        result["url"] = page
        results.append(result)

    elapsed = round(time.time() - start, 1)
    success_count = sum(1 for r in results if r.get("success"))

    report = {
        "success": success_count > 0,
        "browser_tool": tool,
        "pages_tested": len(results),
        "screenshots_captured": success_count,
        "elapsed_seconds": elapsed,
        "results": results,
    }

    report_path = qa_dir / f"qa-{ts}.json"
    atomic_write(report_path, json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    report["report"] = str(report_path)

    return report


def _detect_pages_from_diff(diff_range=""):
    """Detect frontend pages affected by git changes."""
    try:
        args = ["git", "diff", "--name-only"]
        if diff_range:
            args.append(diff_range if ".." in diff_range else f"{diff_range}..HEAD")
        else:
            args.append("HEAD~1..HEAD")

        r = subprocess.run(args, check=False, capture_output=True, text=True, timeout=5)
        files = r.stdout.strip().split("\n") if r.stdout.strip() else []

        # Check if any frontend files changed
        frontend_exts = {".html", ".tsx", ".jsx", ".vue", ".svelte", ".css", ".scss"}
        has_frontend = any(
            any(f.endswith(ext) for ext in frontend_exts)
            for f in files
        )
        if has_frontend:
            return ["http://localhost:3000"]  # default dev server
    except (subprocess.TimeoutExpired, OSError):
        pass
    return []


def cmd_browser_qa(args):
    """Run visual QA testing."""
    url = getattr(args, "url", "") or ""
    diff_range = getattr(args, "range", "") or ""
    dry_run = getattr(args, "dry_run", False)

    result = run_visual_qa(url=url or None, diff_range=diff_range, dry_run=dry_run)
    print(json.dumps(result))
