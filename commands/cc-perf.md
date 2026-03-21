---
agent: "researcher"
description: "Profile and optimize Python code. TRIGGER: 'slow', 'optimize', 'bottleneck', 'performance', 'speed up', '太慢了', '优化性能'. Profiles first, then fixes."
---

Use the cc-performance skill to analyze and optimize code.

1. Identify the slow code path (ask user or check recent changes)
2. Run profiling: `python -m cProfile -s cumulative` on the target
3. Analyze the top 10 time-consuming functions
4. Check for common anti-patterns:
   - `x in list` → `x in set`
   - Sequential I/O → concurrent
   - String concatenation in loops → join
   - N+1 database queries → eager loading
5. Propose targeted fixes with benchmarks
6. Apply fixes and verify with before/after timing
