"""cc-flow intelligence — unified module for AI routing, failure recovery, learning, and verification.

Facade that consolidates 4 intelligence modules into one import path:
  from cc_flow.intelligence import ai_route, record_failure, on_chain_complete, verify_plan

Sub-modules (kept as implementation files, imported here):
  ai_router      — LLM-based chain selection with cache
  failure_engine — 3-engine methodology switching on failures
  auto_learn     — automatic feedback loops (wisdom, metrics, Q-learning)
  plan_verify    — 3-engine plan-to-diff verification
"""

# ── AI Router ──
from cc_flow.ai_router import (  # noqa: F401
    ai_route,
)

# ── Auto Learn ──
from cc_flow.auto_learn import (  # noqa: F401
    on_chain_complete,
    on_research_complete,
    on_review_complete,
    on_routing_complete,
)

# ── Failure Engine ──
from cc_flow.failure_engine import (  # noqa: F401
    diagnose_and_switch,
    get_failure_state,
    record_failure,
    record_success,
    should_switch_methodology,
)

# ── Plan Verify ──
from cc_flow.plan_verify import (  # noqa: F401
    verify_plan,
)
