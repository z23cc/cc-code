---
description: "Conventional commit with pre-commit verification. TRIGGER: 'commit', 'save changes', '提交', '保存'. Auto-detects project language for lint+test."
---

Follow the cc-git-workflow skill's conventional commits format to create a commit.

1. Run `git status` and `git diff --staged` to understand changes
2. Run `git log --oneline -5` to match existing commit style
3. Determine the correct type (feat/fix/refactor/test/docs/perf/ci/chore)
4. Draft a concise commit message: `<type>(<scope>): <description>`
5. Auto-detect language and run verification:
   - Python (`pyproject.toml`): `ruff check . && python -m py_compile`
   - JS/TS (`package.json`): `npm run lint`
   - Go (`go.mod`): `go vet ./...`
   - Rust (`Cargo.toml`): `cargo check`
   - If test files changed: run tests too
6. Stage relevant files (not `.env` or secrets)
7. Create the commit
