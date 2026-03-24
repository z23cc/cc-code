---
name: cc-task-queues
description: >
  Distributed task queues with Celery — background jobs, periodic tasks,
  workflows, error handling, monitoring. Use when adding background processing
  to Python services.
  TRIGGER: 'background job', 'celery', 'async task', 'periodic task', 'task queue',
  '后台任务', '定时任务', '异步队列', '消息队列'.
  NOT FOR: project task tracking — use cc-task-tracking instead.
  FLOWS INTO: cc-performance.
  DEPENDS ON: cc-async-patterns.
---

# Task Queues — Celery Patterns

## When to Use

- **Yes**: Email sending, file processing, report generation, webhooks, data sync, scheduled cleanup
- **No**: Simple async I/O (use `asyncio`), sub-second latency (use in-memory), minimal infra (use RQ/Huey)

## Quick Setup

```python
# celery_app.py
from celery import Celery

app = Celery("myapp", broker="redis://localhost:6379/0", backend="redis://localhost:6379/1")
app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    task_track_started=True,
    task_acks_late=True,              # Re-deliver if worker crashes
    worker_prefetch_multiplier=1,     # Fair scheduling
)
```

## Task Patterns

### Basic Task

```python
@app.task(bind=True, max_retries=3, default_retry_delay=60)
def send_email(self, to: str, subject: str, body: str):
    try:
        smtp_send(to, subject, body)
    except ConnectionError as e:
        self.retry(exc=e)
```

### Task with Progress

```python
@app.task(bind=True)
def process_csv(self, file_path: str):
    rows = read_csv(file_path)
    for i, row in enumerate(rows):
        process_row(row)
        self.update_state(state="PROGRESS", meta={"current": i + 1, "total": len(rows)})
    return {"processed": len(rows)}
```

### Periodic Tasks

```python
from celery.schedules import crontab

app.conf.beat_schedule = {
    "cleanup-expired-sessions": {
        "task": "tasks.cleanup_sessions",
        "schedule": crontab(hour=3, minute=0),  # Daily at 3 AM
    },
    "sync-external-data": {
        "task": "tasks.sync_data",
        "schedule": 300.0,  # Every 5 minutes
    },
}
```

## Workflows (Canvas)

```python
from celery import chain, group, chord

# Sequential pipeline
pipeline = chain(
    extract_data.s(source_id),
    transform_data.s(),
    load_data.s(destination_id),
)
pipeline.apply_async()

# Parallel fan-out
parallel = group(
    process_chunk.s(chunk) for chunk in chunks
)
parallel.apply_async()

# Fan-out then aggregate
aggregation = chord(
    (process_page.s(url) for url in urls),
    aggregate_results.s()
)
aggregation.apply_async()
```

## Error Handling

```python
@app.task(
    bind=True,
    max_retries=5,
    autoretry_for=(ConnectionError, TimeoutError),
    retry_backoff=True,         # Exponential backoff
    retry_backoff_max=600,      # Max 10 minutes
    retry_jitter=True,          # Random jitter
)
def unreliable_api_call(self, endpoint: str):
    return requests.get(endpoint, timeout=30).json()
```

## Monitoring

```bash
# Real-time monitoring
celery -A myapp flower          # Web UI at localhost:5555

# Worker status
celery -A myapp inspect active
celery -A myapp inspect reserved
celery -A myapp inspect stats
```

## Production Checklist

- [ ] `task_acks_late=True` (re-deliver on crash)
- [ ] `worker_prefetch_multiplier=1` (fair scheduling)
- [ ] All tasks are idempotent (safe to retry)
- [ ] Retry with exponential backoff + jitter
- [ ] Result backend configured (if results needed)
- [ ] Flower or Prometheus monitoring
- [ ] Dead letter queue for permanent failures
- [ ] Task time limits set (`task_soft_time_limit`, `task_time_limit`)
- [ ] Separate queues for priority levels

## Related Skills

- **cc-async-patterns** — when to use asyncio vs Celery
- **cc-deploy** — Docker setup for workers + beat + flower
- **cc-error-handling** — retry strategies and circuit breakers
- **cc-performance** — profiling slow tasks, optimizing throughput
- **cc-logging** — structured logging in distributed workers
