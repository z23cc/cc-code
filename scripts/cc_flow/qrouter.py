"""Q-Learning router — learns optimal command selection from history.

Inspired by ruflo's semantic-router. Uses weighted multi-factor scoring
with online gradient updates from success/failure signals.

Q-value update: Q(s,a) = Q(s,a) + lr * (reward - Q(s,a))
where reward = +1.0 (success), -0.5 (partial), -1.0 (failure)
"""

import json
import math

from cc_flow.core import TASKS_DIR, safe_json_load

QTABLE_FILE = TASKS_DIR / "qtable.json"

# Reward signals
REWARDS = {"success": 1.0, "partial": -0.3, "failed": -1.0}

# Learning rate and discount
LEARNING_RATE = 0.1
MIN_CONFIDENCE = 0.3

# Keyword categories for state representation
CATEGORIES = {
    "feature": ["feature", "add", "implement", "build", "create", "new"],
    "bugfix": ["bug", "fix", "error", "broken", "crash", "fail"],
    "refactor": ["refactor", "clean", "simplify", "improve", "optimize"],
    "test": ["test", "coverage", "spec", "assert", "tdd"],
    "security": ["security", "auth", "vulnerability", "inject", "xss"],
    "docs": ["doc", "readme", "changelog", "comment"],
    "deploy": ["deploy", "ci", "cd", "docker", "release"],
    "review": ["review", "audit", "check", "scan"],
}


def _classify_task(query):
    """Classify a task query into a category."""
    words = set(query.lower().split())
    scores = {}
    for cat, keywords in CATEGORIES.items():
        scores[cat] = sum(1 for kw in keywords if kw in words or any(kw in w for w in words))
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "general"


def _load_qtable():
    """Load Q-table from disk. Format: {category: {command: q_value}}."""
    return safe_json_load(QTABLE_FILE, default={})


def _save_qtable(qtable):
    """Persist Q-table."""
    QTABLE_FILE.parent.mkdir(parents=True, exist_ok=True)
    QTABLE_FILE.write_text(json.dumps(qtable, indent=2) + "\n")


def q_route(query):
    """Route a query using Q-table. Returns (command, confidence, category)."""
    category = _classify_task(query)
    qtable = _load_qtable()

    if category not in qtable or not qtable[category]:
        return None, 0, category

    q_values = qtable[category]
    best_cmd = max(q_values, key=q_values.get)
    best_q = q_values[best_cmd]

    # Convert Q-value to confidence (sigmoid-like)
    confidence = int(100 / (1 + math.exp(-best_q * 2)))

    if confidence < MIN_CONFIDENCE * 100:
        return None, confidence, category

    return best_cmd, confidence, category


def q_update(query, command, outcome):
    """Update Q-table from outcome. Returns updated Q-value.

    Args:
        query: original task description
        command: the command that was used (e.g. "/cc-debug")
        outcome: "success" | "partial" | "failed"
    """
    category = _classify_task(query)
    reward = REWARDS.get(outcome, 0.0)
    qtable = _load_qtable()

    if category not in qtable:
        qtable[category] = {}
    if command not in qtable[category]:
        qtable[category][command] = 0.0

    old_q = qtable[category][command]
    new_q = old_q + LEARNING_RATE * (reward - old_q)
    qtable[category][command] = round(new_q, 4)

    _save_qtable(qtable)
    return new_q


def q_stats():
    """Return Q-table statistics."""
    qtable = _load_qtable()
    stats = {}
    for cat, commands in qtable.items():
        best_cmd = max(commands, key=commands.get) if commands else None
        stats[cat] = {
            "best": best_cmd,
            "q_value": round(commands.get(best_cmd, 0), 3) if best_cmd else 0,
            "alternatives": len(commands),
        }
    return stats
