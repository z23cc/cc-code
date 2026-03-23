---
name: cc-scout-observability
description: >
  Scan logging, tracing, metrics, health endpoints, and error tracking setup.
  Reports observability coverage percentage.
  TRIGGER: 'check observability', 'logging setup', 'monitoring config', 'tracing', 'metrics',
  '监控配置', '日志怎么设置的', '可观测性'.
  NOT FOR: adding logging to code — use cc-python-logging instead.
---

# Observability Scout — Logging/Tracing/Metrics Audit

## Scan Checklist

### 1. Logging

```bash
# Python
grep -rn "import logging\|from logging\|loguru\|structlog" src/ 2>/dev/null | head -5
grep -rn "getLogger\|logger\." src/ 2>/dev/null | wc -l

# JS/TS
grep "winston\|pino\|bunyan\|morgan" package.json 2>/dev/null

# Structured logging?
grep -rn "json.*log\|structured.*log\|logger.*info.*{" src/ 2>/dev/null | head -3
```

### 2. Distributed Tracing

```bash
grep "opentelemetry\|jaeger\|zipkin\|datadog.*trace" pyproject.toml package.json 2>/dev/null
grep -rn "trace_id\|span_id\|@trace\|tracer" src/ 2>/dev/null | head -3
```

### 3. Metrics

```bash
grep "prometheus\|prom-client\|statsd\|datadog" pyproject.toml package.json 2>/dev/null
grep -rn "counter\|histogram\|gauge\|@metrics" src/ 2>/dev/null | head -3
```

### 4. Error Tracking

```bash
grep "sentry\|bugsnag\|rollbar\|airbrake" pyproject.toml package.json 2>/dev/null
grep -rn "sentry_sdk\|capture_exception\|capture_message" src/ 2>/dev/null | head -3
```

### 5. Health Endpoints

```bash
grep -rn "health\|healthz\|ready\|readiness\|liveness" src/ 2>/dev/null | head -5
```

## Output Format

```markdown
## Observability Audit

| Pillar | Status | Tool | Details |
|--------|--------|------|---------|
| Logging | OK/BASIC/MISSING | [library] | [structured? level config?] |
| Tracing | OK/MISSING | [library] | [trace ID propagation?] |
| Metrics | OK/MISSING | [library] | [custom metrics defined?] |
| Error tracking | OK/MISSING | [service] | [configured?] |
| Health endpoint | OK/MISSING | [path] | [/health, /ready?] |
| Alerting | OK/MISSING | [tool] | [configured?] |

### Coverage: X/6 pillars

### Recommendations
1. [Most critical gap]
```

## Related Skills

- **cc-logging** — Python logging patterns
- **cc-scout-build** — CI/CD that checks observability
- **cc-incident** — observability enables incident response
