---
agent: "architect"
description: "Bootstrap new Python project. TRIGGER: 'new project', 'create project', 'start a project', 'init', '新建项目', '创建项目'. Generates structure, pyproject.toml, Docker, CI."
---

Activate the cc-scaffold skill. Steps:

1. Ask the user for:
   - Project name
   - Framework (FastAPI / Flask / Django / CLI / Library)
   - Database (PostgreSQL / SQLite / None)
2. Create `src/<package>/` with `__init__.py`, `main.py`
3. Create `pyproject.toml` with ruff, mypy, pytest configs
4. Create `tests/conftest.py` with example fixture
5. Create `.gitignore` with Python patterns
6. Create `.env.example` with required env vars
7. Create `Dockerfile` with multi-stage build (if framework chosen)
8. Create `.github/workflows/ci.yml`
9. Run `git init` and create initial commit
10. Run `/audit` to verify all 8 pillars pass
