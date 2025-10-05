"""Comprehensive unit tests for NeonClient - the main SDK entry point."""

from unittest.mock import Mock, patch

import httpx
import pytest

from neon_crm.client import NeonClient
from neon_crm.exceptions import (
    NeonAuthenticationError,
    NeonBadRequestError,
    NeonConnectionError,
    NeonForbiddenError,
    NeonNotFoundError,
    NeonRateLimitError,
    NeonServerError,
    NeonTimeoutError,
    NeonUnprocessableEntityError,
)


class TestNeonClientInitialization:
    """Test NeonClient initialization and configuration."""

    def test_initialization_with_all_params(self):
        """Test client initialization with all parameters."""
        client = NeonClient(
            org_id="test_org",
            api_key="test_key",
            base_url="https://custom.api.com",
            timeout=30,
            enable_caching=True,
        )

        assert client.org_id == "test_org"
        assert client.api_key == "test_key"
        assert client.base_url == "https://custom.api.com"
        assert client.timeout == 30
        assert client._cache is not None

    def test_initialization_minimal_params(self):
        """Test client initialization with minimal parameters."""
        client = NeonClient(org_id="test_org", api_key="test_key")

        assert client.org_id == "test_org"
        assert client.api_key == "test_key"
        assert client.base_url == "https://api.neoncrm.com/v2/"
        assert client.timeout == 30

    def test_initialization_from_config(self):
        """Test client initialization from config file."""
        with patch("neon_crm.client.ConfigLoader") as mock_config_loader:
            mock_loader = Mock()
            mock_loader.get_config.return_value = {
                "org_id": "config_org",
                "api_key": "config_key",
                "base_url": "https://config.api.com",
                "timeout": 45,
                "active_profile": "default",
                "environment": "production",
                "api_version": "v2",
                "max_retries": 3,
            }
            mock_config_loader.return_value = mock_loader

            client = NeonClient()

            assert client.org_id == "config_org"
            assert client.api_key == "config_key"
            assert client.base_url == "https://config.api.com"
            assert client.timeout == 45

    def test_resource_initialization(self):
        """Test that all resource managers are initialized."""
        client = NeonClient(org_id="test", api_key="test")

        # Check that all major resources are available
        assert hasattr(client, "accounts")
        assert hasattr(client, "donations")
        assert hasattr(client, "events")
        assert hasattr(client, "memberships")
        assert hasattr(client, "activities")
        assert hasattr(client, "custom_fields")
        assert hasattr(client, "custom_objects")
        assert hasattr(client, "addresses")
        assert hasattr(client, "webhooks")
        assert hasattr(client, "online_store")

        # Verify they're the correct type
        from neon_crm.resources import AccountsResource, DonationsResource

        assert isinstance(client.accounts, AccountsResource)
        assert isinstance(client.donations, DonationsResource)

    def test_caching_enabled(self):
        """Test client with caching enabled."""
        client = NeonClient(org_id="test", api_key="test", enable_caching=True)
        assert client._cache is not None

    def test_caching_disabled(self):
        """Test client with caching disabled."""
        client = NeonClient(org_id="test", api_key="test", enable_caching=False)
        assert client._cache is None


class TestNeonClientCaching:
    """Test NeonClient caching functionality."""

    def test_cache_enabled_initialization(self):
        """Test cache initialization when enabled."""
        client = NeonClient(org_id="test", api_key="test", enable_caching=True)
        assert client._cache is not None

    def test_cache_disabled_initialization(self):
        """Test cache initialization when disabled."""
        client = NeonClient(org_id="test", api_key="test", enable_caching=False)
        assert client._cache is None

    def test_clear_cache_when_enabled(self):
        """Test clearing cache when caching is enabled."""
        client = NeonClient(org_id="test", api_key="test", enable_caching=True)

        # Mock the cache
        client._cache = Mock()

        client.clear_cache()

        client._cache.clear_all.assert_called_once()

    def test_clear_cache_when_disabled(self):
        """Test clearing cache when caching is disabled."""
        client = NeonClient(org_id="test", api_key="test", enable_caching=False)

        # Should not raise error
        client.clear_cache()


class TestNeonClientContextManager:
    """Test NeonClient as context manager."""

    def test_context_manager_usage(self):
        """Test using client as context manager."""
        with NeonClient(org_id="test", api_key="test") as client:
            assert isinstance(client, NeonClient)

    def test_context_manager_closes_client(self):
        """Test that context manager properly closes the client."""
        client = NeonClient(org_id="test", api_key="test")

        # Mock the close method
        with patch.object(client, "close") as mock_close:
            with client:
                pass

            mock_close.assert_called_once()

    def test_manual_close(self):
        """Test manually closing the client."""
        client = NeonClient(org_id="test", api_key="test")

        # Mock the httpx client
        client._client = Mock()

        client.close()

        client._client.close.assert_called_once()


class TestNeonClientIntegration:
    """Integration-style tests for NeonClient."""

    def test_real_resource_interaction(self):
        """Test that client properly interacts with resource classes."""
        client = NeonClient(org_id="test", api_key="test")

        # Test that resources can access client methods
        assert client.accounts._client == client
        assert client.donations._client == client

    def test_resource_endpoint_configuration(self):
        """Test that resources have correct endpoints."""
        client = NeonClient(org_id="test", api_key="test")

        assert client.accounts._endpoint == "/accounts"
        assert client.donations._endpoint == "/donations"
        assert client.events._endpoint == "/events"
        assert client.custom_fields._endpoint == "/customFields"

    @patch("httpx.Client.request")
    def test_end_to_end_list_request(self, mock_request):
        """Test end-to-end list request through resource."""
        client = NeonClient(org_id="test", api_key="test")

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "accounts": [
                {"accountId": 123, "firstName": "John", "userType": "INDIVIDUAL"}
            ],
            "pagination": {"currentPage": 0, "totalPages": 1},
        }
        mock_request.return_value = mock_response

        # This should work end-to-end
        from neon_crm.governance import create_user_permissions, Role, PermissionContext

        client.user_permissions = create_user_permissions(
            user_id="test_user", role=Role.ADMIN
        )

        with PermissionContext(client.user_permissions):
            accounts = list(client.accounts.list(user_type="INDIVIDUAL", limit=1))

        assert len(accounts) == 1
        assert accounts[0]["accountId"] == 123


class TestNeonClientReconnection:
    """Test NeonClient reconnection and retry logic for closed connections."""

    @patch("httpx.Client")
    def test_recreate_client_if_closed(self, mock_client_class):
        """Test that client is recreated if it has been closed."""
        # Setup mock client
        mock_client_instance = Mock()
        mock_client_instance.is_closed = True
        mock_client_class.return_value = mock_client_instance

        client = NeonClient(org_id="test", api_key="test")

        # Replace with our mock
        client._client = mock_client_instance

        # Call the recreate method
        client._recreate_client_if_needed()

        # Should have created a new client instance
        assert mock_client_class.call_count >= 2  # Once in __init__, once in recreate

    @patch("httpx.Client")
    def test_no_recreate_if_client_open(self, mock_client_class):
        """Test that client is not recreated if it's still open."""
        # Setup mock client
        mock_client_instance = Mock()
        mock_client_instance.is_closed = False
        mock_client_class.return_value = mock_client_instance

        client = NeonClient(org_id="test", api_key="test")

        # Replace with our mock
        client._client = mock_client_instance
        initial_call_count = mock_client_class.call_count

        # Call the recreate method
        client._recreate_client_if_needed()

        # Should not have created a new client instance
        assert mock_client_class.call_count == initial_call_count

    @patch("time.sleep")  # Mock sleep to speed up tests
    @patch("httpx.Client")
    def test_request_with_client_closed_error(self, mock_client_class, mock_sleep):
        """Test handling of RuntimeError when client is closed during request."""
        # Setup first client instance that will fail
        mock_client_1 = Mock()
        mock_client_1.is_closed = False
        mock_client_1.request.side_effect = RuntimeError("client has been closed")
        mock_client_1.close.return_value = None

        # Setup second client instance that will succeed
        mock_client_2 = Mock()
        mock_client_2.is_closed = False
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"test": "success"}
        mock_client_2.request.return_value = mock_response

        # Configure mock to return different instances
        mock_client_class.side_effect = [mock_client_1, mock_client_2]

        client = NeonClient(org_id="test", api_key="test")

        result = client.request("GET", "/test")

        assert result == {"test": "success"}
        assert mock_client_class.call_count == 2  # Original + recreated
        assert mock_client_1.close.called

    @patch("time.sleep")  # Mock sleep to speed up tests
    @patch("httpx.Client")
    def test_request_with_client_closed_error_max_retries(
        self, mock_client_class, mock_sleep
    ):
        """Test that client closed errors respect max_retries limit."""
        # Setup client instance that always fails
        mock_client = Mock()
        mock_client.is_closed = False
        mock_client.request.side_effect = RuntimeError("client has been closed")
        mock_client.close.return_value = None

        # All client creations return the same failing instance
        mock_client_class.return_value = mock_client

        client = NeonClient(org_id="test", api_key="test", max_retries=1)

        with pytest.raises(NeonConnectionError) as exc_info:
            client.request("GET", "/test")

        assert "HTTP client was closed during request" in str(exc_info.value)
        assert exc_info.value.original_error is not None

        # Should have tried max_retries + 1 times = 2 attempts
        assert mock_client.request.call_count == 2

    @patch("httpx.Client.request")
    def test_request_with_other_runtime_error(self, mock_request):
        """Test that non-client-closed RuntimeErrors are not caught."""
        client = NeonClient(org_id="test", api_key="test")

        # Mock the request to raise a different RuntimeError
        mock_request.side_effect = RuntimeError("some other error")

        with pytest.raises(RuntimeError) as exc_info:
            client.request("GET", "/test")

        assert "some other error" in str(exc_info.value)
        assert mock_request.call_count == 1  # Should not retry
