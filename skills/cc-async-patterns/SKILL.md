---
name: cc-async-patterns
description: >
  Python async/await patterns — asyncio, FastAPI, aiohttp, task groups, error handling for concurrent I/O.
  TRIGGER: 'async', 'await', 'asyncio', 'concurrent', 'aiohttp', 'task group', '异步', '并发'
  NOT FOR: CPU-bound parallelism, multiprocessing, threading
---

# Async Python Patterns

## When to Use Async

- **Yes**: I/O-bound (HTTP calls, DB queries, file reads, WebSocket)
- **No**: CPU-bound (use `multiprocessing` instead)
- **Rule**: If you're `await`ing, it should be async. If you're computing, keep it sync.

## Core Patterns

### Basic Async Function

```python
import asyncio

async def fetch_user(user_id: str) -> User:
    async with aiohttp.ClientSession() as session:
        async with session.get(f"/api/users/{user_id}") as resp:
            data = await resp.json()
            return User(**data)
```

### Concurrent Execution (gather)

```python
async def fetch_all_users(ids: list[str]) -> list[User]:
    tasks = [fetch_user(uid) for uid in ids]
    return await asyncio.gather(*tasks, return_exceptions=True)
```

### Task Groups (Python 3.11+, preferred over gather)

```python
async def fetch_all_users(ids: list[str]) -> list[User]:
    results = []
    async with asyncio.TaskGroup() as tg:
        for uid in ids:
            tg.create_task(fetch_user(uid))
    # All tasks complete or all cancelled on first exception
```

### Semaphore for Rate Limiting

```python
sem = asyncio.Semaphore(10)  # Max 10 concurrent

async def fetch_limited(url: str) -> str:
    async with sem:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                return await resp.text()
```

### Timeout

```python
async def fetch_with_timeout(url: str) -> str:
    async with asyncio.timeout(5.0):  # Python 3.11+
        return await fetch(url)

# Or for older Python:
result = await asyncio.wait_for(fetch(url), timeout=5.0)
```

## FastAPI Patterns

```python
from fastapi import FastAPI, Depends, HTTPException
from contextlib import asynccontextmanager

# Lifespan for startup/shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    pool = await create_db_pool()
    yield {"db": pool}
    await pool.close()

app = FastAPI(lifespan=lifespan)

# Async endpoint
@app.get("/users/{user_id}")
async def get_user(user_id: str, db=Depends(get_db)):
    user = await db.fetch_one("SELECT * FROM users WHERE id = $1", user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

# Background tasks
from fastapi import BackgroundTasks

@app.post("/notify")
async def send_notification(bg: BackgroundTasks):
    bg.add_task(send_email, "user@example.com")
    return {"status": "queued"}
```

## Anti-Patterns

| Bad | Good | Why |
|-----|------|-----|
| `requests.get()` in async | `aiohttp` or `httpx.AsyncClient` | Blocks the event loop |
| `time.sleep()` in async | `await asyncio.sleep()` | Blocks the event loop |
| `open()` for file I/O | `aiofiles.open()` | Blocks the event loop |
| Bare `await gather()` | `TaskGroup` or handle exceptions | gather swallows errors silently |
| Global `aiohttp.ClientSession()` | Session per request or lifespan | Session not closed = resource leak |
| `loop.run_in_executor` for everything | Only for legacy sync code | Overhead, prefer native async |

## Error Handling in Async

```python
async def safe_fetch(url: str) -> str | None:
    try:
        async with asyncio.timeout(10):
            return await fetch(url)
    except asyncio.TimeoutError:
        logger.warning(f"Timeout fetching {url}")
        return None
    except aiohttp.ClientError as e:
        logger.error(f"Client error for {url}: {e}")
        return None
```

## Testing Async Code

```python
import pytest

@pytest.mark.asyncio
async def test_fetch_user():
    user = await fetch_user("123")
    assert user.id == "123"

@pytest.mark.asyncio
async def test_concurrent_fetch():
    users = await fetch_all_users(["1", "2", "3"])
    assert len(users) == 3
```

## Related Skills

- **cc-python-patterns** — sync patterns and general Python idioms
- **cc-performance** — when to choose async vs threading vs multiprocessing
- **cc-python-testing** — pytest-asyncio patterns

## E2E Example: Parallel API Calls

```python
# BEFORE (sequential — slow)
async def get_user_data(user_id: str):
    profile = await fetch_profile(user_id)      # 200ms
    orders = await fetch_orders(user_id)         # 300ms
    recommendations = await fetch_recs(user_id)  # 250ms
    return {**profile, "orders": orders, "recs": recommendations}
# Total: 750ms

# AFTER (parallel — fast)
async def get_user_data(user_id: str):
    async with asyncio.TaskGroup() as tg:
        t1 = tg.create_task(fetch_profile(user_id))
        t2 = tg.create_task(fetch_orders(user_id))
        t3 = tg.create_task(fetch_recs(user_id))
    return {**t1.result(), "orders": t2.result(), "recs": t3.result()}
# Total: 300ms (max of the three)
```

## Quality Metrics

| Metric | Target | Check |
|--------|--------|-------|
| No sync I/O in async | 0 violations | `grep "requests\.\|time.sleep" in async functions` |
| TaskGroup for parallel | Used for 2+ concurrent calls | Code review |
| Timeout on all I/O | Every external call has timeout | `grep "timeout"` |
| Graceful cancellation | TaskGroup handles exceptions | Test with failing subtask |
