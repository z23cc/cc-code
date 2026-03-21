---
description: "Performance awareness — avoid common performance anti-patterns"
alwaysApply: true
---

# Performance Rules

- No N+1 queries — use joins, eager loading, or batch fetching
- No synchronous I/O in async code paths
- No unbounded queries — always add LIMIT or pagination
- No large objects in memory when streaming is possible
- Profile before optimizing — don't guess bottlenecks
- Add database indexes for frequently queried columns
- Cache expensive computations (but invalidate correctly)
- Prefer `O(n)` over `O(n²)` — watch for nested loops on collections
