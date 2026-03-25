"""cc-flow dashboard events — emit events to the visualization dashboard.

Sends events to the dashboard server (http://localhost:3777/api/events)
for real-time visualization of the 3-engine workflow.

Event types:
  router_decision  — AI Router selected a chain/command
  engine_start     — Engine (claude/codex/gemini) starting
  engine_complete  — Engine finished with verdict/output
  debate_round     — Debate round completed (R1/R2)
  debate_vote      — Final vote/verdict
  pua_round        — PUA challenge round
  pipeline_stage   — Pipeline stage transition (plan→execute→verify→commit)
  failure_switch   — Failure engine methodology switch
  learn_update     — Auto-learn recorded to wisdom/metrics
  worktree_event   — Worktree create/merge/remove
"""

import json
import os
import subprocess
import threading
import time

DASHBOARD_URL = os.environ.get("CC_DASHBOARD_URL", "http://localhost:3777")
_SESSION_ID = f"cc-{int(time.time())}"


def _post_event(event_type, phase=None, engine=None, data=None):
    """Post event to dashboard server (non-blocking background thread)."""
    def _send():
        try:
            payload = json.dumps({
                "session_id": _SESSION_ID,
                "event_type": event_type,
                "phase": phase,
                "engine": engine,
                "data": data or {},
            })
            subprocess.run(
                ["curl", "-s", "-X", "POST",
                 f"{DASHBOARD_URL}/api/events",
                 "-H", "Content-Type: application/json",
                 "-d", payload],
                check=False, capture_output=True, timeout=3,
            )
        except (subprocess.TimeoutExpired, OSError):
            pass  # Dashboard not running — silent fail

    threading.Thread(target=_send, daemon=True).start()


# ── Public API ──

def emit_router_decision(query, chain, complexity, engine, reason, cached=False):
    _post_event("router_decision", data={
        "query": query, "chain": chain, "complexity": complexity,
        "engine": engine, "reason": reason, "cached": cached,
    })


def emit_engine_start(engine, role, phase="review"):
    _post_event("engine_start", phase=phase, engine=engine, data={"role": role})


def emit_engine_complete(engine, verdict, issues=0, duration=0, phase="review"):
    _post_event("engine_complete", phase=phase, engine=engine, data={
        "verdict": verdict, "issues": issues, "duration_seconds": duration,
    })


def emit_debate_round(round_num, verdicts, total_issues=0):
    _post_event("debate_round", phase="review", data={
        "round": round_num, "verdicts": verdicts, "total_issues": total_issues,
    })


def emit_debate_vote(verdict, reason, engines_agree=0, engines_total=0):
    _post_event("debate_vote", phase="review", data={
        "verdict": verdict, "reason": reason,
        "agree": engines_agree, "total": engines_total,
    })


def emit_pua_round(round_num, author, challengers, issues, status):
    _post_event("pua_round", phase="pua", data={
        "round": round_num, "author": author, "challengers": challengers,
        "issues": issues, "status": status,
    })


def emit_pipeline_stage(stage, status="started", detail=None):
    _post_event("pipeline_stage", phase=stage, data={
        "status": status, "detail": detail or "",
    })


def emit_failure_switch(failures, methodology, diagnosis):
    _post_event("failure_switch", data={
        "failures": failures, "methodology": methodology, "diagnosis": diagnosis,
    })


def emit_learn_update(category, content):
    _post_event("learn_update", data={"category": category, "content": content[:200]})


def emit_worktree_event(action, name, path=None):
    _post_event("worktree_event", data={"action": action, "name": name, "path": path})
