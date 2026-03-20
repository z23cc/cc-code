---
name: error-handling
description: "Python error handling patterns — exception hierarchies, retry logic, graceful degradation, context propagation. Use when designing error strategies."
---

# Error Handling Patterns

## Custom Exception Hierarchy

```python
class AppError(Exception):
    """Base with structured context for logging."""
    def __init__(self, message: str, *, code: str = "UNKNOWN", **context):
        super().__init__(message)
        self.code = code
        self.context = context

class ValidationError(AppError):
    """Input validation failures."""
    def __init__(self, field: str, message: str):
        super().__init__(message, code="VALIDATION_ERROR", field=field)

class NotFoundError(AppError):
    def __init__(self, resource: str, id: str | int):
        super().__init__(f"{resource} not found: {id}", code="NOT_FOUND", resource=resource, id=id)

class ExternalServiceError(AppError):
    def __init__(self, service: str, message: str, *, status_code: int | None = None):
        super().__init__(message, code="EXTERNAL_ERROR", service=service, status_code=status_code)

# Usage
raise NotFoundError("User", user_id)
# Catches: except NotFoundError as e: logger.error("not_found", **e.context)
```

## Exception Context (Python 3.11+)

```python
# Add notes to exceptions
try:
    process_order(order)
except ValueError as e:
    e.add_note(f"While processing order {order.id}")
    e.add_note(f"Customer: {order.customer_id}")
    raise  # Notes appear in traceback

# Exception groups (multiple errors at once)
errors = []
for item in items:
    try:
        validate(item)
    except ValidationError as e:
        errors.append(e)
if errors:
    raise ExceptionGroup("Validation failed", errors)
```

## Retry with Backoff

```python
import asyncio
import random
from functools import wraps

def retry(max_attempts: int = 3, backoff_base: float = 1.0, exceptions: tuple = (Exception,)):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    if attempt == max_attempts - 1:
                        raise
                    delay = backoff_base * (2 ** attempt) + random.uniform(0, 1)
                    logger.warning(
                        "retry",
                        func=func.__name__,
                        attempt=attempt + 1,
                        delay=f"{delay:.1f}s",
                        error=str(e),
                    )
                    await asyncio.sleep(delay)
        return wrapper
    return decorator

@retry(max_attempts=3, exceptions=(ExternalServiceError, ConnectionError))
async def call_payment_api(order_id: str) -> dict:
    ...
```

## Circuit Breaker (Simple)

```python
import time

class CircuitBreaker:
    def __init__(self, failure_threshold: int = 5, recovery_timeout: float = 60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failures = 0
        self.last_failure_time = 0.0
        self.state = "closed"  # closed | open | half-open

    def __call__(self, func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            if self.state == "open":
                if time.monotonic() - self.last_failure_time > self.recovery_timeout:
                    self.state = "half-open"
                else:
                    raise ExternalServiceError("payment", "Circuit breaker open")

            try:
                result = await func(*args, **kwargs)
                self.failures = 0
                self.state = "closed"
                return result
            except Exception:
                self.failures += 1
                self.last_failure_time = time.monotonic()
                if self.failures >= self.failure_threshold:
                    self.state = "open"
                raise
        return wrapper

payment_breaker = CircuitBreaker(failure_threshold=5, recovery_timeout=60)

@payment_breaker
async def process_payment(amount: float) -> dict:
    ...
```

## Graceful Degradation

```python
async def get_user_profile(user_id: str) -> UserProfile:
    user = await get_user(user_id)  # Required — let exception propagate

    # Optional enrichments — degrade gracefully
    try:
        avatar = await fetch_avatar(user_id)
    except ExternalServiceError:
        avatar = DEFAULT_AVATAR

    try:
        preferences = await fetch_preferences(user_id)
    except ExternalServiceError:
        preferences = DEFAULT_PREFERENCES

    return UserProfile(user=user, avatar=avatar, preferences=preferences)
```

## Anti-Patterns

| Bad | Good | Why |
|-----|------|-----|
| `except: pass` | `except SpecificError as e: log(e)` | Silent failures hide bugs |
| `except Exception: return None` | Let it propagate or handle specifically | Callers can't distinguish error from empty |
| Retry everything | Retry only transient errors (network, timeout) | Retrying validation errors wastes time |
| Log + raise + catch again | Log at ONE level, raise or handle | Duplicate logs obscure root cause |
| String error codes | Enum or exception class | Type safety, IDE autocomplete |

## When to Catch vs. Propagate

| Scenario | Action |
|----------|--------|
| Can fully recover | Catch and handle |
| Need to add context | Catch, add note, re-raise |
| Need to translate | Catch, wrap in domain error, raise |
| Logging boundary (middleware) | Catch, log, return error response |
| Don't know what to do | Let it propagate |

## Related Skills

- **logging** — structured error logging with context
- **fastapi** — FastAPI error handlers and responses
- **async-patterns** — async error handling, TaskGroup cancellation
- **debugging** — when errors are unexpected, switch to systematic debugging
- **task-queues** — Celery retry strategies and error handling
