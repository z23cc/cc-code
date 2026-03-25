"""cc-flow engines — unified module for all multi-engine operations.

Facade that consolidates 5 engine modules into one import path:
  from cc_flow.engines import run_debate, run_pua, run_multi_review, cmd_unified_review

Sub-modules (kept as implementation files):
  unified_review     — auto-escalating review (dispatch layer)
  adversarial_review — 3-engine debate with RP context
  multi_review       — parallel consensus review
  pua_engine         — 3-model mutual PUA challenge
  review_setup       — engine detection and configuration
"""

# ── Unified Review (main entry point) ──
# ── Adversarial Debate ──
from cc_flow.adversarial_review import (  # noqa: F401
    run_debate,
)

# ── Multi-Review Consensus ──
# ── Shared Utilities ──
from cc_flow.multi_review import (  # noqa: F401  # noqa: F401
    _build_review_context,
    _detect_rp,
    build_consensus,
)

# ── PUA Engine ──
from cc_flow.pua_engine import (  # noqa: F401
    run_pua,
)

# ── Review Setup ──
from cc_flow.review_setup import (  # noqa: F401
    cmd_review_setup,
)
from cc_flow.unified_review import (  # noqa: F401
    cmd_unified_review,
)
