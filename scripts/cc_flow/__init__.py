"""cc-flow — task & workflow manager for cc-code plugin.

Usage:
    cc-flow <command>          (after pip install -e .)

Architecture (facade modules → implementation modules):

  Facades (unified import paths):
    engines.py       → unified_review, adversarial_review, multi_review, pua_engine, review_setup
    intelligence.py  → ai_router, failure_engine, auto_learn, plan_verify
    routing.py       → route_learn, qrouter, learning

  Execution pipeline:
    go.py            → unified entry (AI route → execute)
    skill_executor.py → run skills via claude -p subprocess
    auto_ops.py      → subprocess worktree/verify/commit
    autopilot.py     → 3-engine guided execution with checkpoints

  Core:
    entry.py         → lazy-loaded command dispatch
    cli.py           → argparse CLI definitions
    core.py          → shared constants, atomic writes

  External integrations:
    rp.py            → RepoPrompt dual-transport SDK
    bridge.py        → Morph × RP × Supermemory
    multi_plan.py    → 3-engine collaborative planning
    browser_qa.py    → visual QA with screenshots
"""

VERSION = "5.26.0"
