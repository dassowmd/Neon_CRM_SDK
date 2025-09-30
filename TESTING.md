# Testing Guide

This document explains the testing structure and how to run different types of tests for the Neon CRM SDK.

## Test Categories

### 1. Unit Tests
- **Location**: `tests/unit/`
- **Purpose**: Test individual components with mocks
- **Safety**: Safe to run anywhere - uses no real API calls
- **Marker**: `@pytest.mark.unit`

### 2. Read-Only Regression Tests
- **Location**: `tests/regression/test_readonly.py`
- **Purpose**: Test against real API with read-only operations
- **Safety**: Safe for production - only performs GET requests
- **Marker**: `@pytest.mark.regression @pytest.mark.readonly`

### 3. Write Operation Regression Tests
- **Location**: `tests/regression/test_writeops.py`
- **Purpose**: Test create/update/delete operations against real API
- **Safety**: ⚠️ **MODIFIES DATABASE** - only use with trial/test environments
- **Marker**: `@pytest.mark.regression @pytest.mark.writeops`

## Running Tests

### Quick Start with Test Runner

```bash
# Run unit tests (safe, no API calls)
python run_tests.py unit

# Run read-only regression tests (safe for production)
python run_tests.py readonly

# Run write operation tests (MODIFIES DATABASE)
python run_tests.py writeops

# Run all regression tests
python run_tests.py regression

# Run all tests
python run_tests.py all
```

### Direct pytest Commands

```bash
# Unit tests only
pytest -m "unit" tests/unit/

# Read-only regression tests only
pytest -m "regression and readonly" tests/regression/test_readonly.py

# Write operation tests only
pytest -m "regression and writeops" tests/regression/test_writeops.py

# All regression tests
pytest -m "regression" tests/regression/

# All tests except write operations
pytest -m "not writeops"

# All tests except slow ones
pytest -m "not slow"
```

## Environment Setup

### For Unit Tests
No environment variables required.

### For Read-Only Regression Tests
```bash
export NEON_ORG_ID="your_org_id"
export NEON_API_KEY="your_api_key"
export NEON_ENVIRONMENT="production"  # or "trial"
```

### For Write Operation Tests
```bash
export NEON_ORG_ID="your_org_id"
export NEON_API_KEY="your_api_key"
export NEON_ENVIRONMENT="trial"  # NEVER use "production"
export NEON_ALLOW_WRITE_TESTS="true"  # Required safety flag
```

**IMPORTANT**: Write operation tests will refuse to run if:
- `NEON_ENVIRONMENT=production`
- `NEON_ALLOW_WRITE_TESTS` is not set to "true"

## Test Structure

```
tests/
├── conftest.py              # Common fixtures and configuration
├── __init__.py
├── unit/                    # Unit tests with mocks
│   ├── __init__.py
│   ├── test_client.py
│   ├── test_resources.py
│   └── ...
└── regression/              # Regression tests with real API
    ├── __init__.py
    ├── test_readonly.py     # Safe read-only operations
    └── test_writeops.py     # Database-modifying operations
```

## Safety Features

### Read-Only Tests
- Only perform GET requests and searches
- Safe to run against production data
- Will not modify any records
- Use `@pytest.mark.readonly` marker

### Write Operation Tests
- Multiple safety checks prevent accidental production usage
- Automatic cleanup of created test data
- Rate limiting to avoid overwhelming the API
- Use `@pytest.mark.writeops` marker
- Some dangerous tests require additional confirmation via `NEON_CONFIRM_DANGEROUS_TESTS=true`

### Test Data Management
- Write tests create unique test data using timestamps
- All created records are automatically cleaned up
- Cleanup continues even if tests fail
- Test data is clearly identifiable (e.g., "Test Company 1634567890")

## Continuous Integration

For CI/CD pipelines, recommended approach:

```bash
# Always run unit tests
pytest -m "unit"

# Run read-only regression tests if credentials available
if [[ -n "$NEON_ORG_ID" && -n "$NEON_API_KEY" ]]; then
    pytest -m "regression and readonly"
fi

# Only run write tests in dedicated test environments
if [[ "$CI_ENVIRONMENT" == "test" && "$NEON_ALLOW_WRITE_TESTS" == "true" ]]; then
    pytest -m "regression and writeops"
fi
```

## Adding New Tests

### Unit Test
```python
@pytest.mark.unit
def test_something(mock_client):
    # Use mocks, no real API calls
    pass
```

### Read-Only Regression Test
```python
@pytest.mark.regression
@pytest.mark.readonly
def test_readonly_operation(regression_client):
    # Only GET/search operations
    result = regression_client.accounts.list(page_size=1)
    assert result
```

### Write Operation Test
```python
@pytest.mark.regression
@pytest.mark.writeops
def test_write_operation(write_regression_client):
    # Create test data
    result = write_regression_client.accounts.create(test_data)
    account_id = result["accountId"]

    try:
        # Test the operation
        assert account_id
    finally:
        # Always clean up
        write_regression_client.accounts.delete(account_id)
```

## Troubleshooting

### Common Issues

1. **Missing environment variables**: Ensure all required env vars are set
2. **Production safety**: Write tests won't run against production
3. **API rate limits**: Tests include delays to avoid rate limiting
4. **Cleanup failures**: Manual cleanup may be needed if tests are interrupted

### Debug Mode
```bash
# Run with verbose output
pytest -v -s

# Run specific test
pytest -v tests/regression/test_readonly.py::TestReadOnlyOperations::test_list_accounts_basic

# Stop on first failure
pytest -x
```
