---
name: cc-deploy
description: >
  Docker, CI/CD, and deployment patterns for Python applications.
  TRIGGER: 'deploy', 'docker', 'CI/CD', 'production', 'container', 'Dockerfile', '部署', 'Docker'
  NOT FOR: local development setup, testing, scaffolding
  FLOWS INTO: cc-ship.
  DEPENDS ON: cc-verification.
---

# Python Deployment Patterns

## Dockerfile Best Practices

```dockerfile
# Multi-stage build — small final image
FROM python:3.11-slim AS builder
WORKDIR /app
COPY pyproject.toml .
RUN pip install --no-cache-dir --prefix=/install .

FROM python:3.11-slim
WORKDIR /app
COPY --from=builder /install /usr/local
COPY src/ src/

# Non-root user
RUN useradd -r appuser && chown -R appuser /app
USER appuser

EXPOSE 8000
HEALTHCHECK --interval=30s CMD curl -f http://localhost:8000/health || exit 1
CMD ["python", "-m", "package_name.main"]
```

### Key Rules
- Use `python:3.11-slim` not `python:3.11` (saves ~800MB)
- Multi-stage builds — install deps in builder, copy to clean image
- Non-root user for security
- Always add `HEALTHCHECK`
- Pin dependency versions
- `.dockerignore` to exclude `.git/`, `__pycache__/`, `.venv/`

## Docker Compose (Local Dev)

```yaml
services:
  app:
    build: .
    ports: ["8000:8000"]
    volumes: ["./src:/app/src"]
    env_file: .env
    depends_on:
      db:
        condition: service_healthy

  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: app
      POSTGRES_PASSWORD: dev
    healthcheck:
      test: pg_isready -U postgres
      interval: 5s
    volumes: ["pgdata:/var/lib/postgresql/data"]

volumes:
  pgdata:
```

## GitHub Actions CI/CD

```yaml
name: CI/CD
on:
  push:
    branches: [main]
  pull_request:

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16-alpine
        env:
          POSTGRES_DB: test
          POSTGRES_PASSWORD: test
        options: >-
          --health-cmd pg_isready --health-interval 10s
          --health-timeout 5s --health-retries 5
        ports: ["5432:5432"]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.11" }
      - run: pip install ".[dev]"
      - run: ruff check .
      - run: mypy src/
      - run: pytest --cov --cov-report=xml
      - uses: codecov/codecov-action@v4

  deploy:
    needs: test
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: docker build -t app .
      # Add your deployment target here
```

## Health Check Endpoint

```python
# FastAPI
@app.get("/health")
async def health():
    return {"status": "ok", "version": __version__}

# With dependency checks
@app.get("/health")
async def health(db: AsyncSession = Depends(get_db)):
    try:
        await db.execute(text("SELECT 1"))
        return {"status": "ok", "db": "connected"}
    except Exception:
        return JSONResponse(status_code=503, content={"status": "degraded", "db": "disconnected"})
```

## Environment Management

```python
# Use pydantic-settings for typed config
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str
    secret_key: str
    debug: bool = False

    model_config = {"env_file": ".env"}

settings = Settings()
```


## On Completion

When done:
```bash
cc-flow skill ctx save cc-deploy --data '{"deployed": true, "url": "..."}'
cc-flow skill next
```

## Related Skills

- **cc-security-review** — security checklist before deployment
- **cc-verification** — verify build/tests before deploying
- **cc-scaffold** — initial project setup with Docker and CI

## Deployment Checklist

- [ ] `DEBUG=False` in production
- [ ] Secrets from environment variables (not code)
- [ ] HTTPS enforced
- [ ] Health check endpoint
- [ ] Structured logging (JSON format)
- [ ] Database migrations applied
- [ ] Docker image scanned for vulnerabilities
- [ ] Rate limiting configured
- [ ] CORS properly set
