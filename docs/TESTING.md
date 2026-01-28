# Testing Guidelines

This document describes the testing conventions and best practices for the tonie-api project.

## Test File Naming

- Test files: `test_<module>.py` (e.g., `test_api.py`, `test_session.py`)
- Test classes: `Test<Feature>` (e.g., `TestTonieAPIInitialization`)
- Test functions: `test_<what>_<scenario>` (e.g., `test_upload_to_s3_empty_file`)

## Coverage Requirements

- **New features**: >= 90% coverage
- **Bug fixes**: Must include a regression test
- **Overall goal**: Maintain >= 85% coverage

Run coverage report:

```bash
poetry run pytest --cov=tonie_api --cov-report=term-missing
```

## Test Markers

Use pytest markers to categorize tests:

```python
import pytest

@pytest.mark.unit
def test_model_validation():
    """Fast unit test without external dependencies."""
    ...

@pytest.mark.integration
def test_api_connectivity():
    """Test that requires network access."""
    ...

@pytest.mark.slow
def test_large_file_upload():
    """Test that takes significant time."""
    ...
```

Run specific categories:

```bash
poetry run pytest -m unit           # Only unit tests
poetry run pytest -m "not slow"     # Skip slow tests
```

## Mocking Guidelines

### Session Mocking

Always mock `TonieCloudSession` when testing `TonieAPI`:

```python
from unittest.mock import MagicMock
from tonie_api.session import TonieCloudSession

@pytest.fixture
def mock_session():
    """Create a mock session that doesn't require authentication."""
    session = MagicMock(spec=TonieCloudSession)
    session.headers = {"Authorization": "Bearer test-token"}
    return session

@pytest.fixture
def api(mock_session):
    """Create a TonieAPI instance with a mock session."""
    return TonieAPI(session=mock_session)
```

### HTTP Request Mocking

Use the `responses` library for HTTP mocking:

```python
import responses

@responses.activate
def test_token_acquisition():
    responses.add(
        responses.POST,
        TonieCloudSession.TOKEN_URL,
        json={"access_token": "test-token"},
        status=200,
    )
    # Test code here
```

### CLI Testing

Use Click's `CliRunner`:

```python
from click.testing import CliRunner
from tonie_api.cli.main import cli

@pytest.fixture
def runner():
    return CliRunner()

def test_command(runner):
    result = runner.invoke(cli, ["command", "--option"])
    assert result.exit_code == 0
```

## Environment Variable Rules

**CRITICAL**: Never use generic environment variable names in tests!

### Forbidden

```python
# DON'T use system env vars that might conflict
os.environ.get("USERNAME")   # Conflicts with macOS/Windows
os.environ.get("PASSWORD")
```

### Required

```python
# DO use TONIE_ prefixed variables
os.environ.get("TONIE_USERNAME")
os.environ.get("TONIE_PASSWORD")
```

### Test Isolation

Always use `patch.dict` to isolate environment:

```python
from unittest.mock import patch

def test_with_env_vars():
    with patch.dict("os.environ", {
        "TONIE_USERNAME": "test@example.com",
        "TONIE_PASSWORD": "secret"
    }, clear=True):
        # Test code here
        ...
```

## Test Data Fixtures

Use fixtures for common test data:

```python
@pytest.fixture
def sample_tonie():
    return {
        "id": "tonie-123",
        "householdId": "hh-123",
        "name": "Test Tonie",
        # ... other fields
    }

@pytest.fixture
def sample_upload_request():
    return {
        "request": {
            "url": "https://s3.amazonaws.com/bucket",
            "fields": {"key": "uploads/file.mp3", ...}
        },
        "fileId": "file-123"
    }
```

## Temporary Files

Use pytest's `tmp_path` fixture for file operations:

```python
def test_upload_file(tmp_path):
    test_file = tmp_path / "test.mp3"
    test_file.write_bytes(b"fake audio content")

    # Test upload with test_file
```

## Error Testing

Test both success and error paths:

```python
def test_success_case(api, mock_session):
    mock_session.request.return_value = MagicMock(ok=True, json=lambda: {...})
    result = api.some_method()
    assert result.id == "expected"

def test_error_case(api, mock_session):
    mock_response = MagicMock(ok=False, status_code=404)
    mock_session.request.return_value = mock_response

    with pytest.raises(NotFoundError):
        api.some_method()
```

## Running Tests

```bash
# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=tonie_api --cov-report=term-missing

# Run specific file
poetry run pytest tests/test_api.py

# Run specific test
poetry run pytest tests/test_api.py::TestTonieAPIInitialization::test_init_with_credentials

# Run with verbose output
poetry run pytest -v

# Stop on first failure
poetry run pytest -x
```
