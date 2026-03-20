---
name: python-patterns
description: "Pythonic idioms, PEP 8, type hints, and best practices for robust Python applications."
---

# Python Development Patterns

## Core Principles

1. **Readability counts** — code should be obvious
2. **Explicit > implicit** — no magic
3. **EAFP** — ask forgiveness, not permission (try/except over if/check)

## Type Hints (Python 3.9+)

```python
# Use built-in types
def process(items: list[str]) -> dict[str, int]:
    return {item: len(item) for item in items}

# Optional and Union
def find_user(user_id: str) -> User | None:
    return db.find(user_id)

# Protocol for duck typing
from typing import Protocol

class Renderable(Protocol):
    def render(self) -> str: ...
```

## Error Handling

```python
# Specific exceptions with chaining
try:
    config = load_config(path)
except FileNotFoundError as e:
    raise ConfigError(f"Config not found: {path}") from e

# Custom hierarchy
class AppError(Exception): ...
class ValidationError(AppError): ...
class NotFoundError(AppError): ...
```

## Context Managers

```python
# Always use with for resources
with open(path) as f:
    data = f.read()

# Custom context manager
from contextlib import contextmanager

@contextmanager
def timer(name: str):
    start = time.perf_counter()
    yield
    print(f"{name}: {time.perf_counter() - start:.4f}s")
```

## Data Classes

```python
from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class User:
    id: str
    name: str
    email: str
    created_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        if "@" not in self.email:
            raise ValueError(f"Invalid email: {self.email}")
```

## Concurrency

- **Threading** — I/O-bound (concurrent.futures.ThreadPoolExecutor)
- **Multiprocessing** — CPU-bound (concurrent.futures.ProcessPoolExecutor)
- **Async/await** — concurrent I/O (asyncio + aiohttp), see `async-patterns` skill

### Thread Safety

```python
import threading

# Shared mutable state needs a lock
lock = threading.Lock()
counter = 0

def increment():
    global counter
    with lock:  # Always use context manager
        counter += 1

# Thread-safe collections
from queue import Queue
q = Queue()  # Thread-safe FIFO
q.put(item)
item = q.get()
```

**Rules:**
- Protect shared mutable state with `threading.Lock()`
- Use `queue.Queue` for thread-safe producer/consumer
- Use `threading.local()` for thread-local storage
- Prefer `concurrent.futures` over raw `threading` module
- Never mix `asyncio` and blocking calls without `run_in_executor`

## Anti-Patterns to Avoid

| Bad | Good |
|-----|------|
| `def f(x=[])` | `def f(x=None)` then `x = x or []` |
| `type(obj) == list` | `isinstance(obj, list)` |
| `value == None` | `value is None` |
| `from module import *` | Explicit imports |
| `except: pass` | `except SpecificError as e:` |
| String concat in loops | `"".join(...)` |
| `os.path` manipulation | `pathlib.Path` |

## Project Layout

```
src/mypackage/
    __init__.py
    main.py
    api/routes.py
    models/user.py
    utils/helpers.py
tests/
    conftest.py
    test_api.py
    test_models.py
pyproject.toml
```

## Tooling

```bash
black .                    # Format
isort .                    # Sort imports
ruff check .               # Lint
mypy .                     # Type check
pytest --cov=mypackage     # Test + coverage
bandit -r .                # Security
```

## Related Skills

- **async-patterns** — async/await patterns for concurrent I/O
- **clean-architecture** — system-level structure using these patterns
- **python-testing** — testing patterns complement coding patterns
- **error-handling** — exception design and retry strategies
