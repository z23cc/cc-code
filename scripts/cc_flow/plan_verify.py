"""cc-flow plan-verify — 3-engine plan-to-diff verification.

After execution, 3 engines independently check: did we build what we planned?
Each engine cross-references the plan against the actual git diff,
classifying every plan item as DONE / NOT_DONE / PARTIAL.

Architecture:
  1. Extract plan items (from skill context or plan file)
  2. Get actual diff (git diff)
  3. 3 engines independently verify (parallel)
  4. Consensus: items confirmed by 2+ engines = verified
  5. Output: verification report + shipping gate
"""

import json
import re
import shutil
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor

from cc_flow.core import TASKS_DIR, atomic_write, now_iso

VERIFY_PROMPT = """\
You are **{label}** verifying plan implementation.

## Plan (what was supposed to be built):
{plan}

## Actual Diff (what was actually built):
```
{diff}
```

For EACH plan item, classify:
- **DONE**: fully implemented in the diff
- **PARTIAL**: started but incomplete
- **NOT_DONE**: not found in the diff
- **EXTRA**: in the diff but not in the plan (scope creep?)

Output as JSON array:
[
  {{"item": "plan item text", "status": "DONE|PARTIAL|NOT_DONE|EXTRA", "evidence": "file/line or why missing"}},
  ...
]

End with:
{{"ready_to_ship": true/false, "done_count": N, "total": N, "completion_pct": N}}"""


def _exec_engine(engine, prompt, timeout=300):
    """Execute prompt on engine."""
    if engine == "claude":
        cmd = ["claude", "-p", "--output-format", "text", prompt]
    elif engine == "codex":
        cmd = ["codex", "exec", prompt]
    elif engine == "gemini":
        cmd_path = shutil.which("gemini") or shutil.which("gemini-cli")
        if not cmd_path:
            return None
        cmd = [cmd_path, "-p", prompt]
    else:
        return None

    try:
        r = subprocess.run(cmd, check=False, capture_output=True, text=True, timeout=timeout)
        raw = (r.stderr or "") + "\n" + (r.stdout or "") if engine == "codex" else r.stdout
        return raw.strip()
    except (subprocess.TimeoutExpired, OSError):
        return None


def _parse_verification(text):
    """Parse verification JSON from engine output."""
    if not text:
        return None
    # Find JSON array
    match = re.search(r'\[[\s\S]*\]', text)
    if match:
        try:
            items = json.loads(match.group())
            return items
        except json.JSONDecodeError:
            pass
    # Find summary JSON
    summary_match = re.search(r'\{[^{}]*"ready_to_ship"[^{}]*\}', text)
    if summary_match:
        try:
            return json.loads(summary_match.group())
        except json.JSONDecodeError:
            pass
    return None


def verify_plan(plan_text, diff_range="", timeout=300, dry_run=False):
    """3-engine plan-to-diff verification."""
    # Get diff
    diff_args = ["git", "diff"]
    if diff_range:
        diff_args.append(diff_range if ".." in diff_range else f"{diff_range}..HEAD")
    else:
        diff_args.append("HEAD~1..HEAD")

    try:
        r = subprocess.run(diff_args, check=False, capture_output=True, text=True, timeout=10)
        diff = r.stdout[:30000]
    except (subprocess.TimeoutExpired, OSError):
        diff = ""

    if not diff:
        return {"success": False, "error": "No diff found"}

    # Detect engines
    engines = {}
    if shutil.which("claude"):
        engines["claude"] = "Claude"
    if shutil.which("codex"):
        engines["codex"] = "Codex"
    if shutil.which("gemini") or shutil.which("gemini-cli"):
        engines["gemini"] = "Gemini"

    if dry_run:
        return {
            "success": True, "dry_run": True,
            "engines": list(engines.keys()),
            "plan_items": plan_text[:200],
            "diff_size": len(diff),
        }

    if not engines:
        return {"success": False, "error": "No engines available"}

    # 3-engine parallel verification
    start = time.time()
    results = {}

    with ThreadPoolExecutor(max_workers=len(engines)) as pool:
        futures = {}
        for engine, label in engines.items():
            prompt = VERIFY_PROMPT.format(
                label=label,
                plan=plan_text[:5000],
                diff=diff[:15000],
            )
            futures[pool.submit(_exec_engine, engine, prompt, timeout)] = engine

        for future in futures:
            engine = futures[future]
            try:
                output = future.result()
                parsed = _parse_verification(output) if output else None
                results[engine] = {"raw": output[:3000] if output else "", "parsed": parsed}
            except Exception:
                results[engine] = {"raw": "", "parsed": None}

    # Build consensus
    all_items = {}  # item_text → {engine: status}
    for engine, data in results.items():
        parsed = data.get("parsed")
        if isinstance(parsed, list):
            for item in parsed:
                text = item.get("item", "")
                if text:
                    all_items.setdefault(text, {})[engine] = item.get("status", "UNKNOWN")

    # Consensus: 2+ engines agree = confirmed
    verified_items = []
    for item_text, engine_statuses in all_items.items():
        status_counts = {}
        for status in engine_statuses.values():
            status_counts[status] = status_counts.get(status, 0) + 1
        consensus_status = max(status_counts, key=status_counts.get) if status_counts else "UNKNOWN"
        confidence = max(status_counts.values()) / len(engine_statuses) if engine_statuses else 0
        verified_items.append({
            "item": item_text,
            "status": consensus_status,
            "confidence": round(confidence, 2),
            "engines": engine_statuses,
        })

    done = sum(1 for i in verified_items if i["status"] == "DONE")
    partial = sum(1 for i in verified_items if i["status"] == "PARTIAL")
    not_done = sum(1 for i in verified_items if i["status"] == "NOT_DONE")
    total = len(verified_items)
    pct = round(done / total * 100) if total else 0
    ready = not_done == 0 and total > 0

    elapsed = round(time.time() - start, 1)

    # Save report
    report_dir = TASKS_DIR / "plan_verify"
    report_dir.mkdir(parents=True, exist_ok=True)
    ts = now_iso().replace(":", "-").replace("T", "_")[:19]
    report_path = report_dir / f"verify-{ts}.json"
    atomic_write(report_path, json.dumps({
        "timestamp": now_iso(), "ready_to_ship": ready,
        "done": done, "partial": partial, "not_done": not_done, "total": total,
        "completion_pct": pct, "items": verified_items,
        "engines": list(results.keys()), "elapsed_seconds": elapsed,
    }, indent=2, ensure_ascii=False) + "\n")

    return {
        "success": True,
        "ready_to_ship": ready,
        "completion_pct": pct,
        "done": done, "partial": partial, "not_done": not_done, "total": total,
        "items": verified_items[:10],
        "engines": list(results.keys()),
        "elapsed_seconds": elapsed,
        "report": str(report_path),
    }


def cmd_plan_verify(args):
    """Verify plan implementation against actual diff."""
    plan = getattr(args, "plan", "") or ""
    diff_range = getattr(args, "range", "") or ""
    timeout = getattr(args, "timeout", 300)
    dry_run = getattr(args, "dry_run", False)

    # Try to load plan from skill context if not provided
    if not plan:
        try:
            from cc_flow.skill_flow import load_skill_ctx
            for skill in ["cc-plan", "cc-multi-plan", "cc-brainstorm"]:
                ctx = load_skill_ctx(skill)
                if ctx:
                    plan = json.dumps(ctx)[:5000]
                    break
        except (ImportError, Exception):
            pass

    # Try plan files
    if not plan:
        plan_dir = TASKS_DIR / "plans"
        if plan_dir.exists():
            plan_files = sorted(plan_dir.glob("plan-*.md"), reverse=True)
            if plan_files:
                plan = plan_files[0].read_text()[:5000]

    if not plan and not dry_run:
        print(json.dumps({"success": False, "error": "No plan found. Provide --plan or run cc-flow multi-plan first."}))
        return

    result = verify_plan(plan or "No plan available", diff_range=diff_range, timeout=timeout, dry_run=dry_run)
    print(json.dumps(result))
