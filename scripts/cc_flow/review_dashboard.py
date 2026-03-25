"""cc-flow review dashboard — review history, trends, readiness gate.

Reads .tasks/reviews/*.json to provide:
  1. Dashboard: summary of all reviews (verdicts, engines, trends)
  2. Readiness gate: is the code ready to ship?
  3. Engine stats: which engine finds the most issues?
"""

import json
from datetime import datetime, timezone

from cc_flow.core import TASKS_DIR

REVIEWS_DIR = TASKS_DIR / "reviews"


def _load_reviews():
    """Load all review/consensus/debate JSON files."""
    if not REVIEWS_DIR.exists():
        return []

    reviews = []
    for f in sorted(REVIEWS_DIR.glob("*.json")):
        try:
            data = json.loads(f.read_text())
            data["_file"] = f.name
            data["_type"] = f.name.split("-")[0]  # consensus, debate, review, adversarial, pua
            reviews.append(data)
        except (json.JSONDecodeError, OSError):
            pass
    return reviews


def _extract_timestamp(review):
    """Extract timestamp from review data or filename."""
    ts = review.get("timestamp", "")
    if ts:
        return ts
    # Parse from filename: consensus-2026-03-24_15-26-27.json
    name = review.get("_file", "")
    parts = name.replace(".json", "").split("-", 1)
    if len(parts) > 1:
        return parts[1].replace("_", "T").replace("-", ":", 2)
    return ""


def dashboard():
    """Build review dashboard summary."""
    reviews = _load_reviews()
    if not reviews:
        return {"success": True, "total_reviews": 0, "message": "No review history yet."}

    # Separate by type
    consensus_reviews = [r for r in reviews if r["_type"] == "consensus"]
    debates = [r for r in reviews if r["_type"] == "debate"]
    adversarial = [r for r in reviews if r["_type"] == "adversarial"]
    pua_reviews = [r for r in reviews if r["_type"] == "pua"]
    per_engine = [r for r in reviews if r["_type"] == "review"]

    # Verdict counts (from consensus/debate/adversarial)
    all_sessions = consensus_reviews + debates + adversarial
    verdicts = {}
    for r in all_sessions:
        v = r.get("consensus", {}).get("verdict", r.get("verdict", "UNKNOWN"))
        verdicts[v] = verdicts.get(v, 0) + 1

    # Engine stats
    engine_stats = {}  # engine → {total, ship, needs_work, issues_found}
    for r in per_engine:
        engine = r.get("engine", "unknown")
        verdict = r.get("verdict", "UNKNOWN")
        issues = len(r.get("findings", []))
        if engine not in engine_stats:
            engine_stats[engine] = {"total": 0, "ship": 0, "needs_work": 0, "issues_found": 0}
        engine_stats[engine]["total"] += 1
        if verdict == "SHIP":
            engine_stats[engine]["ship"] += 1
        elif verdict in ("NEEDS_WORK", "MAJOR_RETHINK"):
            engine_stats[engine]["needs_work"] += 1
        engine_stats[engine]["issues_found"] += issues

    # Most recent review
    latest = all_sessions[-1] if all_sessions else None
    latest_verdict = None
    latest_time = None
    if latest:
        latest_verdict = latest.get("consensus", {}).get("verdict", latest.get("verdict"))
        latest_time = _extract_timestamp(latest)

    # Trend: last 5 sessions
    recent = all_sessions[-5:]
    recent_verdicts = []
    for r in recent:
        v = r.get("consensus", {}).get("verdict", r.get("verdict", "?"))
        recent_verdicts.append(v)

    # Issues trend
    total_issues = sum(
        r.get("consensus", {}).get("total_findings", r.get("total_issues", 0))
        for r in all_sessions
    )

    return {
        "success": True,
        "total_reviews": len(all_sessions),
        "total_per_engine": len(per_engine),
        "verdicts": verdicts,
        "latest": {"verdict": latest_verdict, "time": latest_time},
        "trend": recent_verdicts,
        "total_issues_found": total_issues,
        "engine_stats": engine_stats,
        "pua_sessions": len(pua_reviews),
        "debate_sessions": len(debates),
    }


def readiness_gate():
    """Check if code is ready to ship based on review history.

    Gate rules:
      1. Must have at least 1 review session
      2. Most recent review must be SHIP
      3. No unresolved MAJOR_RETHINK in last 3 reviews
    """
    reviews = _load_reviews()
    all_sessions = [r for r in reviews if r["_type"] in ("consensus", "debate", "adversarial")]

    if not all_sessions:
        return {
            "ready": False,
            "reason": "No review history. Run: cc-flow review",
            "gate_checks": {"has_review": False},
        }

    latest = all_sessions[-1]
    latest_verdict = latest.get("consensus", {}).get("verdict", latest.get("verdict", "UNKNOWN"))

    # Check last 3 for MAJOR_RETHINK
    recent = all_sessions[-3:]
    has_rethink = any(
        r.get("consensus", {}).get("verdict", r.get("verdict")) == "MAJOR_RETHINK"
        for r in recent
    )

    # Staleness check: latest review must be < 2 hours old
    latest_time = _extract_timestamp(latest)
    stale = False
    if latest_time:
        try:
            ts = datetime.fromisoformat(latest_time.replace("Z", "+00:00"))
            age_hours = (datetime.now(timezone.utc) - ts).total_seconds() / 3600
            stale = age_hours > 2
        except (ValueError, TypeError):
            pass

    ready = latest_verdict == "SHIP" and not has_rethink and not stale

    return {
        "ready": ready,
        "latest_verdict": latest_verdict,
        "stale": stale,
        "has_rethink": has_rethink,
        "reason": (
            "Ready to ship" if ready
            else f"Latest verdict: {latest_verdict}" if latest_verdict != "SHIP"
            else "Review is stale (>2h)" if stale
            else "Recent MAJOR_RETHINK found"
        ),
        "gate_checks": {
            "has_review": True,
            "latest_ship": latest_verdict == "SHIP",
            "no_rethink": not has_rethink,
            "fresh": not stale,
        },
    }


# ── CLI ──

def cmd_review_dashboard(args):
    """Show review history dashboard or check readiness."""
    subcmd = getattr(args, "dashboard_cmd", "") or ""

    if subcmd == "gate":
        result = readiness_gate()
        print(json.dumps({"success": True, **result}))
    else:
        result = dashboard()
        print(json.dumps(result))
