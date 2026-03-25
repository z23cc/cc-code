"""cc-flow — task & workflow manager for cc-code plugin.

Usage:
    cc-flow <command>          (after pip install -e .)

Package structure (58 modules):
  cc_flow/
    entry.py         → lazy-loaded command dispatch
    cli.py           → argparse CLI definitions
    core.py          → shared constants, atomic writes, ID resolution
    go.py            → unified entry (route → complexity → execute)
    autopilot.py     → 3-engine guided execution with checkpoints
    multi_plan.py    → 3-engine collaborative planning
    multi_review.py  → multi-engine parallel review + consensus
    adversarial_review.py → 3-engine adversarial debate
    unified_review.py → auto-escalate review (debate > consensus > agent)
    skill_chains.py  → chain definitions loader (chains.json)
    skill_flow.py    → skill flow graph, context protocol
    work.py          → task execution with worker isolation
    auto.py          → OODA-loop autoimmune scanner
    quality.py       → verify (lint + test), scan
    rp.py            → RepoPrompt dual-transport SDK
    bridge.py        → Morph × RP × Supermemory bridge
    repl.py          → interactive REPL
    + 41 more modules (views, analytics, config, etc.)
"""

VERSION = "5.26.0"
