"""Test configuration and fixtures for the Neon CRM SDK."""

from typing import Any, Dict
from unittest.mock import MagicMock

import pytest

from neon_crm import NeonClient


@pytest.fixture
def mock_client():
    """Create a mock Neon client for unit tests."""
    client = MagicMock(spec=NeonClient)
    client.org_id = "test_org"
    client.api_key = "test_key"
    client.environment = "trial"
    return client


@pytest.fixture
def sample_account_data() -> Dict[str, Any]:
    """Sample account data for testing."""
    return {
        "accountId": "12345",
        "firstName": "John",
        "lastName": "Doe",
        "email": "john.doe@example.com",
        "userType": "INDIVIDUAL",
        "dateCreated": "2024-01-15T10:30:00Z",
    }


@pytest.fixture
def sample_donation_data() -> Dict[str, Any]:
    """Sample donation data for testing."""
    return {
        "donationId": "67890",
        "amount": 100.00,
        "date": "2024-01-15",
        "campaign": {"id": 1, "name": "Annual Campaign"},
        "fund": {"id": 2, "name": "General Fund"},
    }


@pytest.fixture
def sample_event_data() -> Dict[str, Any]:
    """Sample event data for testing."""
    return {
        "eventId": "11111",
        "name": "Fundraising Gala",
        "startDate": "2024-06-15T19:00:00Z",
        "endDate": "2024-06-15T23:00:00Z",
        "status": "published",
    }


@pytest.fixture
def sample_pagination_response() -> Dict[str, Any]:
    """Sample paginated response for testing."""
    return {
        "pagination": {
            "currentPage": 1,
            "pageSize": 50,
            "totalPages": 3,
            "totalResults": 150,
            "sortColumn": "dateCreated",
            "sortDirection": "DESC",
        },
        "searchResults": [{"id": 1, "name": "Item 1"}, {"id": 2, "name": "Item 2"}],
    }


@pytest.fixture
def regression_client():
    """Create a real client for regression tests using standard config loading chain.

    Configuration priority: init params > profile config > env vars > defaults

    This fixture will create a client without explicit parameters, allowing it to
    use the full config chain including profiles.
    """
    try:
        # Let NeonClient use its standard config loading chain
        client = NeonClient()
        return client
    except ValueError as e:
        # If config loading fails, skip the test with a helpful message
        pytest.skip(
            f"Regression tests require configuration via config file or environment variables. "
            f"Error: {e}\n"
            f"Options:\n"
            f"1. Create ~/.neon/config.json with org_id, api_key, environment\n"
            f"2. Use profiles in ~/.neon/config.json and set NEON_PROFILE\n"
            f"3. Set NEON_ORG_ID and NEON_API_KEY environment variables\n"
            f"4. Optionally set NEON_ENVIRONMENT (defaults to 'production')"
        )


@pytest.fixture
def write_regression_client():
    """Create a real client for write regression tests with safety checks.

    This fixture explicitly sets environment to 'trial' for safety and provides
    additional validation for write operations.
    """
    try:
        # For write operations, we want to be extra cautious about environment
        client = NeonClient(environment="trial")

        # Additional safety check - ensure we're not accidentally using production
        if client.environment == "production":
            pytest.skip(
                "Write operations are not allowed in production environment. "
                "Please set NEON_ENVIRONMENT=trial or configure your config file with 'environment': 'trial'"
            )

        return client
    except ValueError as e:
        pytest.skip(
            f"Write regression tests require configuration. Error: {e}\n"
            f"For safety, write tests will use environment='trial'\n"
            f"Options:\n"
            f"1. Create ~/.neon/config.json with org_id, api_key, and environment: 'trial'\n"
            f"2. Set NEON_ORG_ID, NEON_API_KEY, and NEON_ENVIRONMENT=trial environment variables"
        )


@pytest.fixture
def mock_successful_response():
    """Mock a successful HTTP response."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"success": True}
    return mock_response


@pytest.fixture
def mock_paginated_response(sample_pagination_response):
    """Mock a paginated HTTP response."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = sample_pagination_response
    return mock_response


@pytest.fixture
def mock_error_response():
    """Mock an error HTTP response."""
    mock_response = MagicMock()
    mock_response.status_code = 400
    mock_response.json.return_value = {
        "error": "Bad Request",
        "message": "Invalid parameters",
    }
    return mock_response


# Markers for different test categories
pytest_plugins = []


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line("markers", "unit: Unit tests that use mocks")
    config.addinivalue_line("markers", "regression: Regression tests that use real API")
    config.addinivalue_line(
        "markers", "readonly: Read-only operations (safe for production)"
    )
    config.addinivalue_line("markers", "writeops: Write operations (modifies database)")
    config.addinivalue_line("markers", "slow: Slow running tests")


# Test data generators
class TestDataGenerator:
    """Generate test data for various scenarios."""

    @staticmethod
    def create_individual_account(
        first_name: str = "John",
        last_name: str = "Doe",
        email: str = "john.doe@example.com",
    ) -> Dict[str, Any]:
        """Create individual account test data."""
        return {
            "individualAccount": {
                "accountType": "INDIVIDUAL",
                "firstName": first_name,
                "lastName": last_name,
                "email": email,
            }
        }

    @staticmethod
    def create_company_account(
        name: str = "Test Company", email: str = "info@testcompany.com"
    ) -> Dict[str, Any]:
        """Create company account test data."""
        return {
            "companyAccount": {"accountType": "COMPANY", "name": name, "email": email}
        }

    @staticmethod
    def create_donation(
        amount: float = 100.00, date: str = "2024-01-15"
    ) -> Dict[str, Any]:
        """Create donation test data."""
        return {
            "amount": amount,
            "date": date,
            "campaign": {"id": 1},
            "fund": {"id": 1},
        }


@pytest.fixture
def test_data_generator():
    """Provide access to test data generator."""
    return TestDataGenerator()
