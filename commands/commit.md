---
description: "Create a conventional commit. Analyzes staged changes, drafts a message following commit conventions, and commits."
---

Follow the git-workflow skill's conventional commits format to create a commit.

1. Run `git status` and `git diff --staged` to understand changes
2. Run `git log --oneline -5` to match existing commit style
3. Determine the correct type (feat/fix/refactor/test/docs/perf/ci/chore)
4. Draft a concise commit message: `<type>(<scope>): <description>`
5. Run verification before committing:
   - `ruff check .` (lint)
   - `python -m py_compile` on changed files (syntax)
   - `pytest` if test files changed
6. Stage relevant files (not `.env` or secrets)
7. Create the commit
