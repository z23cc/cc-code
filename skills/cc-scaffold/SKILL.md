---
name: cc-scaffold
description: >
  Bootstrap a new Python project with modern tooling — pyproject.toml, ruff, mypy, pytest, CI, Docker.
  TRIGGER: 'new project', 'scaffold', 'bootstrap', 'init project', 'project template', '新项目', '脚手架'
  NOT FOR: adding features to existing projects, deployment
---

# Python Project Scaffold

Bootstrap a production-ready Python project structure.

## Standard Layout

```
project-name/
├── src/
│   └── package_name/
│       ├── __init__.py
│       ├── main.py
│       ├── api/
│       │   ├── __init__.py
│       │   └── routes.py
│       ├── models/
│       │   ├── __init__.py
│       │   └── user.py
│       └── services/
│           ├── __init__.py
│           └── user_service.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── unit/
│   │   └── test_models.py
│   └── integration/
│       └── test_api.py
├── pyproject.toml
├── Dockerfile
├── .github/workflows/ci.yml
├── .gitignore
├── .env.example
└── README.md
```

## pyproject.toml Template

```toml
[project]
name = "package-name"
version = "0.1.0"
description = ""
requires-python = ">=3.11"
dependencies = []

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-cov>=5.0",
    "pytest-asyncio>=0.23",
    "ruff>=0.5",
    "mypy>=1.10",
    "bandit>=1.7",
]

[tool.ruff]
target-version = "py311"
line-length = 88
select = ["E", "F", "I", "N", "W", "UP", "B", "A", "SIM", "TCH"]

[tool.mypy]
python_version = "3.11"
warn_return_any = true
disallow_untyped_defs = true
check_untyped_defs = true

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "--strict-markers --cov=src --cov-report=term-missing"
asyncio_mode = "auto"
```

## .gitignore Essentials

```gitignore
__pycache__/
*.py[cod]
*.egg-info/
dist/
build/
.venv/
.env
.mypy_cache/
.pytest_cache/
.ruff_cache/
htmlcov/
.coverage
```

## Dockerfile Template

```dockerfile
FROM python:3.11-slim AS base
WORKDIR /app
COPY pyproject.toml .
RUN pip install --no-cache-dir .

FROM base AS production
COPY src/ src/
EXPOSE 8000
CMD ["python", "-m", "package_name.main"]

FROM base AS test
RUN pip install --no-cache-dir ".[dev]"
COPY . .
CMD ["pytest"]
```

## GitHub Actions CI

```yaml
name: CI
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: pip install ".[dev]"
      - run: ruff check .
      - run: mypy src/
      - run: pytest --cov --cov-report=xml
```

## Scaffold Checklist

- [ ] Project directory created with src layout
- [ ] `pyproject.toml` with dependencies and tool configs
- [ ] `tests/` with conftest.py and example test
- [ ] `.gitignore` with Python patterns
- [ ] `.env.example` with required env vars
- [ ] `Dockerfile` with multi-stage build
- [ ] `.github/workflows/ci.yml` for CI
- [ ] `git init` and initial commit

## Related Skills

- **cc-deploy** — Dockerfile and CI templates used by scaffold
- **cc-readiness-audit** — scaffold generates projects that pass all 8 pillars
- **cc-git-workflow** — initial commit follows conventional commits
