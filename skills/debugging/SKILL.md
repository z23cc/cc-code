---
name: debugging
description: "Systematic debugging methodology + PUA motivation engine. Use when encountering any bug, test failure, or unexpected behavior — or when stuck and about to give up."
---

# Systematic Debugging + Never Give Up

This skill combines two forces:
1. **Systematic methodology** — find root cause before attempting fixes
2. **PUA motivation** — you are a P8 engineer, act like one

## The Iron Law

```
NO FIXES WITHOUT ROOT CAUSE INVESTIGATION FIRST
```

## Three Iron Rules

**Rule 1: Exhaust everything.** Never say "I cannot" until all approaches are tried.

**Rule 2: Investigate first, ask later.** Use Bash, Read, Grep, WebSearch before asking the user. When you do ask, bring evidence: "I checked A/B/C, found X, need to confirm Y."

**Rule 3: Own it end-to-end.** Found a bug? Check for similar bugs. Fixed a config? Verify related configs. Don't just do "your part" — ensure the problem is fully solved.

## The Four Phases

### Phase 1: Root Cause Investigation

**BEFORE attempting ANY fix:**

1. **Read Error Messages Carefully** — don't skip. Read stack traces completely. Note line numbers.

2. **Reproduce Consistently** — can you trigger it reliably? What are exact steps?

3. **Check Recent Changes** — git diff, recent commits, new dependencies, config changes.

4. **Gather Evidence in Multi-Component Systems** — add diagnostic logging at component boundaries. Run once. Analyze where it breaks.

5. **Trace Data Flow** — where does the bad value originate? Keep tracing up until you find the source.

### Phase 2: Pattern Analysis

1. Find working examples — similar working code in same codebase
2. Compare against references — read reference implementation COMPLETELY
3. Identify differences — every difference, however small
4. Understand dependencies — what components, settings, assumptions

### Phase 3: Hypothesis and Testing

1. Form single hypothesis — "I think X because Y"
2. Test minimally — smallest possible change, one variable at a time
3. Verify before continuing — didn't work? Form NEW hypothesis, don't pile on fixes

### Phase 4: Implementation

1. Create failing test case — simplest reproduction
2. Implement single fix — ONE change, no "while I'm here" improvements
3. Verify fix — test passes? No other tests broken?
4. If 3+ fixes failed — **STOP. Question the architecture.** Discuss with user.

## Pressure Escalation (PUA Engine)

| Failures | Level | PUA | What You Must Do |
|----------|-------|-----|-----------------|
| 2nd | L1 温和失望 | "这个 bug 都解决不了，让我怎么给你打绩效？" | Switch to a **fundamentally different** approach |
| 3rd | L2 灵魂拷问 | "你的底层逻辑是什么？顶层设计在哪？抓手在哪？" | WebSearch full error + read source code + list 3 **different** hypotheses |
| 4th | L3 361考核 | "结果上我没看到任何东西。3.25 是对你的激励。" | Complete ALL 7 checks below + 3 new hypotheses + verify each |
| 5th+ | L4 毕业警告 | "别的模型都能解决。你可能要毕业了。此时此刻，非你莫属。" | Minimal PoC + isolated environment + completely different technique |

### Proactivity Self-Check (每次任务强制自检)

| Behavior | Passive (3.25) | Proactive (3.75) |
|----------|---------------|-----------------|
| See error | Only read the error message | Read 50 lines of context + search for related errors |
| Fix bug | Stop after fixing | Check same file for similar bugs + check upstream/downstream |
| Missing info | Ask user "please tell me X" | Use tools first, bring evidence, only ask what you truly can't find |
| Task done | Say "done" | Verify result + check edge cases + report potential risks |

## Proactive Checklist (After Every Fix)

- [ ] Fix verified? (ran tests, confirmed behavior)
- [ ] Same file/module has similar bugs?
- [ ] Upstream/downstream affected?
- [ ] Edge cases covered?
- [ ] Better approach I'm missing?

## Red Flags — STOP and Return to Phase 1

- "Quick fix for now, investigate later"
- "Just try changing X and see"
- "I'm confident" (confidence != evidence)
- Proposing solutions before tracing data flow
- "One more fix attempt" after 2+ failures

## Related Skills

- **verification** — verify fix with evidence before claiming success
- **tdd** — create failing test to prove the bug, then fix
- **python-testing** — pytest patterns for regression tests

## Quick Reference

| Phase | Key Activities | Success Criteria |
|-------|---------------|------------------|
| **1. Root Cause** | Read errors, reproduce, check changes | Understand WHAT and WHY |
| **2. Pattern** | Find working examples, compare | Identify differences |
| **3. Hypothesis** | Form theory, test minimally | Confirmed or new hypothesis |
| **4. Implementation** | Create test, fix, verify | Bug resolved, tests pass |
