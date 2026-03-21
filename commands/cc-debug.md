---
description: "Systematic debugging with PUA escalation. TRIGGER: 'debug', 'why is this broken', 'fix this bug', 'investigate error', '调试', '为什么报错', '修这个bug'. NOT for build errors (/fix)."
---

Activate the cc-debugging skill (systematic 4-phase + PUA escalation).

IRON LAW: NO FIXES WITHOUT ROOT CAUSE INVESTIGATION FIRST.

Phase 1: Root Cause — read errors, reproduce, check recent changes, trace data flow
Phase 2: Pattern — find working examples, compare, identify differences
Phase 3: Hypothesis — form theory, test minimally, one variable at a time
Phase 4: Implementation — create failing test, implement single fix, verify

If fix fails 2+ times → PUA escalation activates (L1→L2→L3→L4).
If fix fails 3+ times → question the architecture, discuss with user.

For complex bugs, use `/team` (Bug Fix team: researcher → build-fixer → code-reviewer).
