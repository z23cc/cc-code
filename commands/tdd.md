---
description: "Start TDD workflow. Write failing tests first, then implement."
---

Activate the TDD skill for the current task.

Follow the Red-Green-Refactor cycle strictly:
1. Write a failing test for the desired behavior
2. Run it to verify it fails correctly
3. Write minimal code to make it pass
4. Run tests to verify they pass
5. Refactor while keeping tests green
6. Repeat

Target 80%+ coverage. Use `pytest --cov` to measure.
