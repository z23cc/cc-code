---
description: "Git workflow rules — enforced for all commits"
alwaysApply: true
---

# Git Rules

- Use conventional commits: `<type>(<scope>): <description>`
- Types: feat, fix, refactor, test, docs, perf, ci, chore
- Run lint + type check + tests before committing
- Don't commit .env, credentials, or secrets
- Don't commit debug print statements
- One logical change per commit
- Branch naming: `feature/`, `fix/`, `refactor/`, `test/`
