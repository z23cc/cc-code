---
description: "Bootstrap new Python project. TRIGGER: 'new project', 'create project', 'start a project', 'init', '新建项目', '创建项目'. Generates structure, pyproject.toml, Docker, CI."
---

Use the scaffold skill to create a new Python project.

Ask the user for:
1. Project name
2. Framework preference (FastAPI / Flask / Django / CLI / Library)
3. Database (PostgreSQL / SQLite / None)

Then create:
- `src/` layout with package structure
- `pyproject.toml` with ruff, mypy, pytest configs
- `tests/conftest.py` with example fixtures
- `Dockerfile` with multi-stage build
- `.github/workflows/ci.yml`
- `.gitignore`, `.env.example`
- Initial git commit
