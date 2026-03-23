---
team: "bug-fix"
description: "Systematic debugging with PUA escalation. TRIGGER: 'debug', 'why is this broken', 'fix this bug', 'investigate error', '调试', '为什么报错', '修这个bug'. NOT for build errors (/fix)."
---

Activate the cc-debugging skill with **Bug Fix team** dispatch.

```bash
```

IRON LAW: NO FIXES WITHOUT ROOT CAUSE INVESTIGATION FIRST.

## Default Team: Bug Fix (researcher → build-fixer → code-reviewer)

### Step 1: Dispatch researcher
- Read errors, reproduce, check recent changes, trace data flow
- Apply 4-phase debugging: Root Cause → Pattern → Hypothesis → Implementation
- Write findings to `/tmp/cc-team-research.md`

### Step 2: Dispatch build-fixer
- Read researcher findings
- Implement single minimal fix based on root cause
- Create regression test
- Run verification (lint + type + test)

### Step 3: Dispatch code-reviewer
- Review the fix + regression test
- Verdict: SHIP / NEEDS_WORK / MAJOR_RETHINK
- If NEEDS_WORK → loop back to build-fixer (max 3 loops)

### PUA Escalation (if fix fails)
If fix fails 2+ times → PUA escalation activates (L1→L2→L3→L4).
If fix fails 3+ times → question the architecture, discuss with user.

## Auto-Learn After Fix

After a successful fix:
```bash
cc-flow learn --task "[bug description]" --outcome success \
  --approach "[root cause + fix approach]" \
  --lesson "[pattern to remember for next time]" \
  --score [1-5] --used-command /cc-debug
```
