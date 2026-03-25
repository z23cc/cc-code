"""cc-flow auto-learn — automatic feedback loops for all subsystems.

Connects isolated subsystems so every execution generates learning:
  chain complete → wisdom + metrics
  review complete → wisdom + supermemory
  research complete → exploration cache
  AI router success → Q-learning feedback

Called automatically by chain executor, review, and autopilot.
No manual intervention needed.
"""

import subprocess


def on_chain_complete(chain_name, goal, steps_completed, total_steps, verdict="success"):
    """Auto-triggered when a chain finishes. Records wisdom + metrics."""
    _record_wisdom(
        category="learnings",
        content=f"Chain '{chain_name}' completed ({steps_completed}/{total_steps} steps) for: {goal}",
        source=f"chain:{chain_name}",
    )
    _record_chain_metrics(chain_name, steps_completed, total_steps, verdict)
    _feed_q_learning(goal, f"/cc-go chain:{chain_name}", verdict)
    try:
        from cc_flow.dashboard_events import emit_learn_update
        emit_learn_update("chain_complete", f"{chain_name}: {verdict} ({steps_completed}/{total_steps})")
    except ImportError:
        pass


def on_review_complete(verdict, engines_used, issues_found, pua_escalated=False):
    """Auto-triggered when review finishes. Records wisdom + pushes to supermemory."""
    engines_str = ", ".join(engines_used) if engines_used else "agent"
    pua_str = " (PUA escalated)" if pua_escalated else ""
    _record_wisdom(
        category="decisions",
        content=f"Review verdict: {verdict} by {engines_str}{pua_str}. {issues_found} issues found.",
        source="review",
    )
    if issues_found > 0:
        _push_to_supermemory(f"Review found {issues_found} issues (verdict: {verdict}). Engines: {engines_str}")
    try:
        from cc_flow.dashboard_events import emit_learn_update
        emit_learn_update("review_complete", f"{verdict} by {engines_str}, {issues_found} issues{pua_str}")
    except ImportError:
        pass


def on_research_complete(query, result_summary):
    """Auto-triggered when research/deep-search finishes. Caches for reuse."""
    _cache_exploration(query, result_summary)


def on_routing_complete(query, chain_selected, outcome):
    """Auto-triggered after AI router decision executes. Feeds Q-learning."""
    _feed_q_learning(query, chain_selected, outcome)


# ── Internal helpers ──

def _record_wisdom(category, content, source="auto"):
    """Append to wisdom store."""
    try:
        from cc_flow.wisdom import append_wisdom
        append_wisdom(category, content, source=source)
    except (ImportError, Exception):
        pass


def _record_chain_metrics(chain_name, steps_completed, total_steps, verdict):
    """Update chain metrics."""
    try:
        from cc_flow.skill_flow import record_chain_complete
        record_chain_complete(chain_name, steps_completed, total_steps)
    except (ImportError, Exception):
        pass


def _feed_q_learning(query, command, outcome):
    """Feed outcome to Q-learning router for future improvement."""
    try:
        from cc_flow.qrouter import q_update
        q_update(query, command, outcome)
    except (ImportError, Exception):
        pass


def _cache_exploration(query, result):
    """Cache research result for future reuse."""
    try:
        from cc_flow.wisdom import cache_exploration
        cache_exploration(query, result)
    except (ImportError, Exception):
        pass


def _push_to_supermemory(content):
    """Push to Supermemory for cross-session recall."""
    try:
        subprocess.run(
            ["cc-flow", "memory", "save", "--content", content],
            check=False, capture_output=True, text=True, timeout=10,
        )
    except (subprocess.TimeoutExpired, OSError):
        pass
