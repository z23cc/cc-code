---
description: "Testing standards — enforced across all code changes"
alwaysApply: true
---

# Testing Rules

- Write tests BEFORE implementation (TDD: Red → Green → Refactor)
- Target 80%+ code coverage on new code
- Use pytest (not unittest)
- Test behavior, not implementation details
- One assertion concept per test
- Use descriptive test names: `test_login_with_invalid_password_returns_401`
- Use fixtures for setup, parametrize for multiple inputs
- Mock external dependencies only (DB, APIs, filesystem)
- Never mock the code under test
- Run `pytest` before every commit
