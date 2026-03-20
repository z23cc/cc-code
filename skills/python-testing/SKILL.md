---
name: python-testing
description: "Python testing with pytest — TDD methodology, fixtures, parametrization, mocking, async testing, and coverage."
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

## DO / DON'T

**DO:** Test behavior not implementation, use fixtures, mock external deps, test edge cases
**DON'T:** Test third-party code, share state between tests, use complex conditionals in tests, catch exceptions (use `pytest.raises`)
