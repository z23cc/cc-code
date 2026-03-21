---
team: "bug-fix"
agent: "researcher"
description: "Profile and optimize Python code. TRIGGER: 'slow', 'optimize', 'bottleneck', 'performance', 'speed up', '太慢了', '优化性能'. Profiles first, then fixes."
---

Performance optimization with **team** dispatch.

## Default Team: researcher → build-fixer → code-reviewer

### Step 1: Dispatch researcher
1. Identify the slow code path
2. Profile: `python -m cProfile -s cumulative`
3. Analyze top 10 time-consuming functions
4. Check for anti-patterns (N+1, `x in list`, sequential I/O, string concat)
5. Write findings to `/tmp/cc-team-research.md`

### Step 2: Dispatch build-fixer
- Apply targeted fixes based on profiling data
- Verify with before/after timing
- Max 50 lines diff per optimization

### Step 3: Dispatch code-reviewer
- Review optimizations, ensure correctness preserved
- Verdict: SHIP / NEEDS_WORK
