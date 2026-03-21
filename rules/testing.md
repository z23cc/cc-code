---
description: "Testing standards — enforced across all code changes"
alwaysApply: true
---

# Testing Rules

- Write tests BEFORE implementation (TDD: Red → Green → Refactor)
- Target 80%+ code coverage on new code
- Test behavior, not implementation details
- One assertion concept per test
- Use descriptive test names: `test_login_with_invalid_password_returns_401`
- Use fixtures/helpers for setup
- Mock external dependencies only (DB, APIs, filesystem)
- Never mock the code under test
- Run tests before every commit
