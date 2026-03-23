---
name: cc-python-testing
description: >
  Python testing with pytest — TDD, fixtures, parametrization, mocking, async testing, and coverage.
  TRIGGER: 'pytest', 'test', 'TDD', 'coverage', 'mock', 'fixture', '测试', '写测试'
  NOT FOR: error handling patterns, debugging, deployment
---

# Python Testing Patterns

## TDD Cycle

1. **RED**: Write failing test
2. **GREEN**: Minimal code to pass
3. **REFACTOR**: Improve while staying green

Target: 80%+ coverage. Critical paths: 100%.

## pytest Basics

```python
def test_addition():
    assert add(2, 3) == 5

def test_raises_on_invalid():
    with pytest.raises(ValueError, match="invalid input"):
        validate("")
```

## Fixtures

```python
@pytest.fixture
def db():
    db = Database(":memory:")
    db.create_tables()
    yield db
    db.close()

@pytest.fixture
def client(db):
    app = create_app(testing=True, db=db)
    return app.test_client()

# Shared fixtures go in conftest.py
```

## Parametrization

```python
@pytest.mark.parametrize("input,expected", [
    ("valid@email.com", True),
    ("invalid", False),
    ("@no-domain", False),
], ids=["valid", "missing-at", "no-local"])
def test_email_validation(input, expected):
    assert is_valid_email(input) is expected
```

## Mocking

```python
from unittest.mock import patch, Mock

@patch("mypackage.external_api_call")
def test_with_mock(api_mock):
    api_mock.return_value = {"status": "ok"}
    result = my_function()
    api_mock.assert_called_once()
    assert result["status"] == "ok"

# Mock exceptions
@patch("mypackage.api_call")
def test_error_handling(api_mock):
    api_mock.side_effect = ConnectionError("timeout")
    with pytest.raises(ConnectionError):
        api_call()
```

## Async Testing

```python
@pytest.mark.asyncio
async def test_async_fetch():
    result = await fetch_data("endpoint")
    assert result is not None

@pytest.mark.asyncio
@patch("mypackage.async_api")
async def test_async_mock(api_mock):
    api_mock.return_value = {"data": []}
    result = await process()
    api_mock.assert_awaited_once()
```

## Test Organization

```
tests/
    conftest.py              # Shared fixtures
    unit/
        test_models.py
        test_utils.py
    integration/
        test_api.py
        test_database.py
```

## Running Tests

```bash
pytest                                      # All
pytest tests/test_file.py::test_name -v    # One test
pytest --cov=mypackage --cov-report=html   # Coverage
pytest -x                                   # Stop first fail
pytest --lf                                 # Last failed
pytest -k "test_user"                       # Pattern
pytest -m "not slow"                        # Skip slow
```

## Test Pyramid — Layered Strategy

| Layer | Quantity | Speed | What to Test |
|-------|----------|-------|-------------|
| **Unit** | Many (70%) | Fast | Pure functions, business logic, models |
| **Integration** | Some (20%) | Medium | DB queries, API endpoints, service interactions |
| **E2E** | Few (10%) | Slow | Critical user flows end-to-end |

### Edge Case Matrix

For each function, consider:

| Category | Cases |
|----------|-------|
| **Boundaries** | Empty input, max length, zero, negative, off-by-one |
| **Null/None** | None arguments, missing keys, empty collections |
| **Concurrency** | Parallel calls, race conditions, deadlocks |
| **Error paths** | Network timeout, DB down, invalid format, permission denied |
| **Security** | SQL injection strings, XSS payloads, path traversal (`../`) |

### Performance Tests

```python
@pytest.mark.slow
def test_bulk_insert_performance():
    start = time.perf_counter()
    bulk_insert(generate_records(10_000))
    elapsed = time.perf_counter() - start
    assert elapsed < 5.0, f"Bulk insert too slow: {elapsed:.1f}s"
```

## DO / DON'T

**DO:** Test behavior not implementation, use fixtures, mock external deps, test edge cases, follow the pyramid
**DON'T:** Test third-party code, share state between tests, use complex conditionals in tests, catch exceptions (use `pytest.raises`)

## Related Skills

- **cc-tdd** — TDD workflow that drives test writing
- **cc-python-patterns** — coding patterns being tested
- **cc-refinement** — coverage thresholds checked during refinement
- **cc-async-patterns** — pytest-asyncio patterns for async code

## E2E Example: Testing a User Service

```python
# fixtures (conftest.py)
@pytest.fixture
def fake_repo():
    return FakeUserRepo()

@pytest.fixture
def service(fake_repo):
    return UserService(repo=fake_repo)

# test_user_service.py
class TestCreateUser:
    def test_creates_with_valid_email(self, service):
        user = service.create("test@example.com", "password123")
        assert user.email == "test@example.com"
        assert user.id is not None

    def test_rejects_duplicate_email(self, service):
        service.create("test@example.com", "pw")
        with pytest.raises(UserAlreadyExists):
            service.create("test@example.com", "pw2")

    @pytest.mark.parametrize("email", ["", "no-at", "@no-local", "no-domain@"])
    def test_rejects_invalid_email(self, service, email):
        with pytest.raises(ValidationError):
            service.create(email, "password123")

# Run: pytest tests/test_user_service.py -v --cov=src/services --cov-fail-under=80
```

## Quality Metrics

| Metric | Target | Command |
|--------|--------|---------|
| Coverage | ≥ 80% | `pytest --cov --cov-fail-under=80` |
| Tests per function | ≥ 2 | happy + error path |
| Test speed | < 5s each | `pytest --durations=5` |
| No mocking internals | 0 mock.patch on private methods | Code review |
