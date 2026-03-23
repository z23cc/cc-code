---
name: cc-performance
description: >
  Python performance profiling, optimization patterns, and benchmarking.
  TRIGGER: 'slow', 'profile', 'bottleneck', 'optimize', '慢', '性能', '优化'.
---

# Python Performance Optimization

## Profiling First — Never Optimize Blindly

```bash
# CPU profiling
python -m cProfile -s cumulative script.py
python -m cProfile -o output.prof script.py  # Save for analysis

# Line-by-line profiling
pip install line_profiler
kernprof -l -v script.py                     # @profile decorated functions

# Memory profiling
pip install memory_profiler
python -m memory_profiler script.py          # @profile decorated functions

# Quick timing
python -m timeit -n 1000 "your_expression"
```

## Common Optimization Patterns

### Data Structures

| Use Case | Slow | Fast |
|----------|------|------|
| Membership test | `x in list` O(n) | `x in set` O(1) |
| Key lookup | linear scan | `dict[key]` O(1) |
| Queue operations | `list.pop(0)` O(n) | `deque.popleft()` O(1) |
| Sorted insert | `list.append + sort` | `bisect.insort` O(log n) |
| Counter | manual dict | `collections.Counter` |

### I/O Bound

```python
# Sequential (slow)
for url in urls:
    response = requests.get(url)

# Concurrent threads (fast for I/O)
from concurrent.futures import ThreadPoolExecutor
with ThreadPoolExecutor(max_workers=10) as pool:
    results = list(pool.map(requests.get, urls))

# Async (fastest for many I/O ops)
async def fetch_all(urls):
    async with aiohttp.ClientSession() as session:
        tasks = [session.get(url) for url in urls]
        return await asyncio.gather(*tasks)
```

### CPU Bound

```python
# Single process (slow)
results = [heavy_compute(x) for x in data]

# Multi-process (fast for CPU)
from concurrent.futures import ProcessPoolExecutor
with ProcessPoolExecutor() as pool:
    results = list(pool.map(heavy_compute, data))
```

### Memory

```python
# Large list in memory (bad)
data = [process(x) for x in huge_file]

# Generator — lazy evaluation (good)
data = (process(x) for x in huge_file)

# __slots__ for many instances
class Point:
    __slots__ = ['x', 'y']
    def __init__(self, x, y):
        self.x = x
        self.y = y
```

### String Operations

```python
# O(n^2) concatenation
result = ""
for s in strings:
    result += s

# O(n) join
result = "".join(strings)
```

### Database

```python
# N+1 query (slow)
users = User.query.all()
for user in users:
    print(user.posts)  # Separate query per user!

# Eager loading (fast)
users = User.query.options(joinedload(User.posts)).all()

# Batch insert
db.session.add_all(objects)  # Not: for obj in objects: db.add(obj)
```

## Benchmarking

```python
import time
from functools import wraps

def benchmark(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed = time.perf_counter() - start
        print(f"{func.__name__}: {elapsed:.4f}s")
        return result
    return wrapper
```

## Related Skills

- **cc-python-patterns** — foundational patterns including concurrency
- **cc-deploy** — production performance considerations

## Quick Wins Checklist

- [ ] Use `set` for membership tests instead of `list`
- [ ] Use generators for large data processing
- [ ] Use `"".join()` instead of `+=` in loops
- [ ] Use `ThreadPoolExecutor` for I/O-bound tasks
- [ ] Use `ProcessPoolExecutor` for CPU-bound tasks
- [ ] Add database indexes for frequent queries
- [ ] Use eager loading to avoid N+1 queries
- [ ] Cache expensive computations with `@functools.lru_cache`
- [ ] Profile before optimizing — measure, don't guess
