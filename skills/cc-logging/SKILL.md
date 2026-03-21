---
name: cc-logging
description: "Python logging, structured output, and error handling patterns. Use when adding observability, debugging production issues, or setting up monitoring."
---

# Logging & Observability

## stdlib logging Setup

```python
import logging

# Module-level logger (best practice)
logger = logging.getLogger(__name__)

# Configuration (once, at app startup)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
```

## Structured Logging (Production)

```python
import structlog

structlog.configure(
    processors=[
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.JSONRenderer(),  # JSON for production
    ],
    logger_factory=structlog.stdlib.LoggerFactory(),
)

logger = structlog.get_logger()

# Usage — key-value context
logger.info("user.login", user_id="123", ip="1.2.3.4")
logger.error("payment.failed", order_id="456", reason="insufficient_funds")

# Bound logger (carry context across calls)
log = logger.bind(request_id="abc-123", user_id="456")
log.info("processing.start")
log.info("processing.complete", duration_ms=42)
```

## Log Levels — When to Use

| Level | When | Example |
|-------|------|---------|
| `DEBUG` | Development-only detail | Variable values, query params |
| `INFO` | Normal operations | User login, request served, job completed |
| `WARNING` | Unexpected but handled | Retry attempt, deprecated API call, slow query |
| `ERROR` | Failure requiring attention | Unhandled exception, external service down |
| `CRITICAL` | System is broken | Database unreachable, out of memory |

## Error Handling Patterns

### Structured Exception Hierarchy

```python
class AppError(Exception):
    """Base application error with structured logging support."""
    def __init__(self, message: str, **context):
        super().__init__(message)
        self.context = context

class ValidationError(AppError): ...
class NotFoundError(AppError): ...
class ExternalServiceError(AppError): ...

# Usage
try:
    result = await fetch_order(order_id)
except ExternalServiceError as e:
    logger.error("order.fetch_failed", order_id=order_id, **e.context)
    raise
```

### Middleware Error Logging (FastAPI)

```python
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        logger.info("request.start", method=request.method, path=request.url.path)
        try:
            response = await call_next(request)
            logger.info("request.end", status=response.status_code)
            return response
        except Exception as e:
            logger.exception("request.error", error=str(e))
            raise
```

## What NOT to Log

- Passwords, tokens, API keys
- Full credit card numbers
- Personal health information
- Session tokens or JWTs
- Raw request bodies with PII

```python
# Bad
logger.info("Login", password=password)

# Good
logger.info("Login", user_id=user.id, ip=request.client.host)
```

## Health Check Pattern

```python
@app.get("/health")
async def health():
    checks = {}
    try:
        await db.execute(text("SELECT 1"))
        checks["db"] = "ok"
    except Exception:
        checks["db"] = "fail"

    try:
        await redis.ping()
        checks["cache"] = "ok"
    except Exception:
        checks["cache"] = "fail"

    status = "ok" if all(v == "ok" for v in checks.values()) else "degraded"
    code = 200 if status == "ok" else 503
    return JSONResponse({"status": status, **checks}, status_code=code)
```

## Related Skills

- **cc-deploy** — health checks and production logging config
- **cc-debugging** — using logs for root cause investigation
- **cc-security-review** — what not to log, PII protection
