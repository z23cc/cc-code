"""cc-flow routing — unified module for routing, Q-learning, and learnings.

Facade consolidating 3 legacy routing modules:
  route_learn — keyword-based routing (legacy, replaced by AI router)
  qrouter     — Q-learning adaptive routing
  learning    — learnings store (learn, consolidate)

Note: AI router (in intelligence.py) is the primary routing path.
These modules provide learning/feedback support.
"""

# ── Q-Learning ──
# ── Learnings ──
from cc_flow.learning import (  # noqa: F401
    cmd_consolidate,
    cmd_learn,
    cmd_learnings,
)
from cc_flow.qrouter import (  # noqa: F401
    q_route,
    q_update,
)
