---
description: >
  Distributed task queues with Celery — background jobs, periodic tasks,
  workflows, error handling, monitoring.
  TRIGGER: 'background job', 'celery', 'async task', 'periodic task', 'task queue', 'message queue'.
  NOT FOR: project task tracking — use cc-task-tracking instead.
  FLOWS INTO: cc-performance. DEPENDS ON: cc-async-patterns.
---

Activate the cc-task-queues skill.

## Covers

- Celery setup (broker, backend, config)
- Task patterns (basic, with progress, periodic)
- Workflows via Canvas (chain, group, chord)
- Error handling (retry with exponential backoff + jitter)
- Monitoring (Flower, worker inspection)
- Production checklist (acks_late, idempotency, dead letter queue, time limits)

## When to Use

- **Yes**: Email sending, file processing, report generation, webhooks, data sync, scheduled cleanup
- **No**: Simple async I/O (use asyncio), sub-second latency (use in-memory), minimal infra (use RQ/Huey)
