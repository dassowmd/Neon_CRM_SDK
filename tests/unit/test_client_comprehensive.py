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


class TestNeonClientHTTPMethods:
    """Test HTTP convenience methods (get, post, put, patch, delete)."""

    @patch("httpx.Client.request")
    def test_get_method(self, mock_request):
        """Test GET convenience method."""
        client = NeonClient(org_id="test", api_key="test")

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": "test"}
        mock_request.return_value = mock_response

        result = client.get("/accounts")

        assert result == {"data": "test"}
        assert mock_request.called

    @patch("httpx.Client.request")
    def test_post_method(self, mock_request):
        """Test POST convenience method."""
        client = NeonClient(org_id="test", api_key="test")

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": 123}
        mock_request.return_value = mock_response

        data = {"name": "Test"}
        result = client.post("/accounts", json_data=data)

        assert result == {"id": 123}
        assert mock_request.called

    @patch("httpx.Client.request")
    def test_put_method(self, mock_request):
        """Test PUT convenience method."""
        client = NeonClient(org_id="test", api_key="test")

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"updated": True}
        mock_request.return_value = mock_response

        result = client.put("/accounts/123")

        assert result == {"updated": True}
        assert mock_request.called

    @patch("httpx.Client.request")
    def test_patch_method(self, mock_request):
        """Test PATCH convenience method."""
        client = NeonClient(org_id="test", api_key="test")

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"patched": True}
        mock_request.return_value = mock_response

        result = client.patch("/accounts/123")

        assert result == {"patched": True}
        assert mock_request.called

    @patch("httpx.Client.request")
    def test_delete_method(self, mock_request):
        """Test DELETE convenience method."""
        client = NeonClient(org_id="test", api_key="test")

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {}
        mock_request.return_value = mock_response

        result = client.delete("/accounts/123")

        assert result == {}
        assert mock_request.called


class TestNeonClientCaching:
    """Test caching functionality."""

    def test_caching_enabled(self):
        """Test client with caching enabled."""
        client = NeonClient(org_id="test", api_key="test", enable_caching=True)
        assert client._cache is not None

    def test_caching_disabled(self):
        """Test client with caching disabled."""
        client = NeonClient(org_id="test", api_key="test", enable_caching=False)
        assert client._cache is None

    def test_clear_cache(self):
        """Test clearing cache."""
        client = NeonClient(org_id="test", api_key="test", enable_caching=True)
        client.clear_cache()
        # Should not raise an error

    def test_clear_cache_when_disabled(self):
        """Test clearing cache when caching is disabled."""
        client = NeonClient(org_id="test", api_key="test", enable_caching=False)
        client.clear_cache()
        # Should not raise an error

    def test_get_cache_stats(self):
        """Test getting cache statistics."""
        client = NeonClient(org_id="test", api_key="test", enable_caching=True)
        stats = client.get_cache_stats()
        assert isinstance(stats, dict)

    def test_get_cache_stats_when_disabled(self):
        """Test getting cache stats when caching is disabled."""
        client = NeonClient(org_id="test", api_key="test", enable_caching=False)
        stats = client.get_cache_stats()
        assert isinstance(stats, dict)

    def test_clear_field_cache(self):
        """Test clearing field cache."""
        client = NeonClient(org_id="test", api_key="test", enable_caching=True)
        client.clear_field_cache("accounts")
        # Should not raise an error

    def test_clear_field_cache_all_resources(self):
        """Test clearing field cache for all resources."""
        client = NeonClient(org_id="test", api_key="test", enable_caching=True)
        client.clear_field_cache()
        # Should not raise an error

    def test_refresh_field_cache(self):
        """Test refreshing field cache."""
        client = NeonClient(org_id="test", api_key="test", enable_caching=True)
        # This will make API calls, so we just test it doesn't crash
        # In real usage this would fetch fresh data
        # For unit test we just verify method exists and is callable
        assert callable(client.refresh_field_cache)

    def test_get_field_cache_status(self):
        """Test getting field cache status."""
        client = NeonClient(org_id="test", api_key="test", enable_caching=True)
        status = client.get_field_cache_status()
        assert isinstance(status, dict)


class TestNeonClientContextManager:
    """Test context manager functionality."""

    @patch("httpx.Client.close")
    def test_context_manager(self, mock_close):
        """Test using client as context manager."""
        with NeonClient(org_id="test", api_key="test") as client:
            assert client is not None
            assert client.org_id == "test"

        # Client should be closed after exiting context
        mock_close.assert_called_once()

    @patch("httpx.Client.close")
    def test_context_manager_with_exception(self, mock_close):
        """Test context manager properly closes on exception."""
        try:
            with NeonClient(org_id="test", api_key="test") as client:
                raise ValueError("Test error")
        except ValueError:
            pass

        # Client should still be closed
        mock_close.assert_called_once()

    def test_close_method(self):
        """Test explicit close method."""
        client = NeonClient(org_id="test", api_key="test")
        client.close()
        # Should not raise an error


class TestNeonClientGovernance:
    """Test governance and permissions functionality."""

    def test_governance_enabled_by_default(self):
        """Test that governance is enabled by default."""
        client = NeonClient(org_id="test", api_key="test")
        assert client.governance_enabled is True

    def test_governance_can_be_disabled(self):
        """Test that governance can be disabled."""
        client = NeonClient(org_id="test", api_key="test", enable_governance=False)
        assert client.governance_enabled is False

    def test_set_user_permissions(self):
        """Test setting user permissions."""
        from neon_crm.governance import create_user_permissions, Role

        client = NeonClient(org_id="test", api_key="test")
        permissions = create_user_permissions(user_id="user123", role=Role.ADMIN)

        client.set_user_permissions(permissions)
        assert client.user_permissions == permissions


class TestNeonClientErrorFormatting:
    """Test error message formatting."""

    def test_format_error_with_string_response(self):
        """Test error formatting with string response."""
        client = NeonClient(org_id="test", api_key="test")
        message = client._format_error_message(404, "Not found")
        assert "Not found" in message

    def test_format_error_with_dict_response(self):
        """Test error formatting with dictionary response."""
        client = NeonClient(org_id="test", api_key="test")
        response_data = {"error": "Invalid request", "details": "Missing field"}
        message = client._format_error_message(400, response_data)
        assert "Invalid request" in message or "400" in message

    def test_format_error_with_message_key(self):
        """Test error formatting extracts 'message' from response."""
        client = NeonClient(org_id="test", api_key="test")
        response_data = {"message": "Custom error message"}
        message = client._format_error_message(500, response_data)
        assert "Custom error message" in message or "500" in message


class TestNeonClientRetryLogic:
    """Test retry and backoff logic."""

    def test_calculate_retry_delay_exponential_backoff(self):
        """Test exponential backoff calculation."""
        client = NeonClient(org_id="test", api_key="test")

        # First retry
        delay1 = client._calculate_retry_delay(0, None)
        # Second retry should be longer
        delay2 = client._calculate_retry_delay(1, None)
        # Third retry should be even longer
        delay3 = client._calculate_retry_delay(2, None)

        assert delay1 >= 0
        assert delay2 >= delay1
        assert delay3 >= delay2

    def test_calculate_retry_delay_with_retry_after(self):
        """Test using Retry-After header value."""
        client = NeonClient(org_id="test", api_key="test")

        # Should use retry_after when provided (plus jitter)
        delay = client._calculate_retry_delay(0, 10)
        assert delay >= 10.1  # Should be retry_after + jitter
        assert delay <= 11.0  # jitter is between 0.1 and 1.0

    def test_calculate_retry_delay_max_value(self):
        """Test that retry delay doesn't exceed maximum."""
        client = NeonClient(org_id="test", api_key="test")

        # Very high attempt number should still cap at max
        delay = client._calculate_retry_delay(100, None)
        assert delay <= 60  # Assuming max is 60 seconds


class TestNeonClientInitializationErrors:
    """Test error handling during client initialization."""

    def test_log_level_configuration(self):
        """Test that log_level is properly configured."""
        client = NeonClient(org_id="test", api_key="test", log_level="DEBUG")
        # Logger should be configured with DEBUG level
        assert client._logger is not None


class TestNeonClientGovernanceConfiguration:
    """Test governance and permissions configuration."""

    def test_governance_with_default_role(self):
        """Test client initialization with default_role."""
        from neon_crm.governance import Role

        client = NeonClient(org_id="test", api_key="test", default_role=Role.VIEWER)

        assert client.user_permissions is not None
        assert client.user_permissions.role == "viewer"

    def test_governance_with_permission_overrides(self):
        """Test client initialization with permission_overrides."""
        from neon_crm.governance import Permission, ResourceType

        permission_overrides = {ResourceType.ACCOUNTS: {Permission.ADMIN}}

        client = NeonClient(
            org_id="test",
            api_key="test",
            default_role="viewer",
            permission_overrides=permission_overrides,
        )

        assert client.user_permissions is not None

    def test_governance_with_explicit_user_permissions(self):
        """Test client initialization with explicit user_permissions."""
        from neon_crm.governance import create_user_permissions, Role

        permissions = create_user_permissions("test_user", Role.ADMIN)

        client = NeonClient(org_id="test", api_key="test", user_permissions=permissions)

        assert client.user_permissions == permissions

    def test_governance_disabled_no_permissions(self):
        """Test client without governance has no permissions."""
        client = NeonClient(org_id="test", api_key="test", enable_governance=False)

        assert client.user_permissions is None

    def test_create_permissions_from_config_with_invalid_role(self):
        """Test permission creation with invalid role defaults to viewer."""
        client = NeonClient(
            org_id="test", api_key="test", default_role="invalid_role_name"
        )

        # Should default to viewer role
        assert client.user_permissions is not None
        assert client.user_permissions.role == "viewer"

    def test_create_permissions_with_invalid_resource_type(self):
        """Test permission override with invalid resource type is skipped."""
        permission_overrides = {"invalid_resource": {"read"}}

        client = NeonClient(
            org_id="test",
            api_key="test",
            default_role="viewer",
            permission_overrides=permission_overrides,
        )

        # Should create permissions but skip invalid resource
        assert client.user_permissions is not None

    def test_create_permissions_with_invalid_permission(self):
        """Test permission override with invalid permission is skipped."""
        from neon_crm.governance import ResourceType

        permission_overrides = {ResourceType.ACCOUNTS: {"invalid_permission"}}

        client = NeonClient(
            org_id="test",
            api_key="test",
            default_role="viewer",
            permission_overrides=permission_overrides,
        )

        # Should create permissions but skip invalid permission
        assert client.user_permissions is not None


class TestNeonClientEnvironmentConfiguration:
    """Test environment-based configuration."""

    def test_trial_environment_base_url(self):
        """Test that trial environment uses correct base URL."""
        client = NeonClient(org_id="test", api_key="test", environment="trial")

        assert client.base_url == "https://trial.neoncrm.com/v2/"

    def test_production_environment_base_url(self):
        """Test that production environment uses correct base URL."""
        client = NeonClient(org_id="test", api_key="test", environment="production")

        assert client.base_url == "https://api.neoncrm.com/v2/"

    def test_custom_base_url_overrides_environment(self):
        """Test that custom base_url overrides environment default."""
        custom_url = "https://custom.api.com/v2/"
        client = NeonClient(
            org_id="test", api_key="test", environment="trial", base_url=custom_url
        )

        assert client.base_url == custom_url


class TestNeonClientErrorHandling:
    """Test HTTP error response handling."""

    @patch("httpx.Client.request")
    def test_400_bad_request_error(self, mock_request):
        """Test handling of 400 Bad Request errors."""
        from neon_crm.exceptions import NeonBadRequestError
        import pytest

        client = NeonClient(org_id="test", api_key="test")

        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.json.return_value = {"error": "Invalid request"}
        mock_response.text = "Invalid request"
        mock_request.return_value = mock_response

        with pytest.raises(NeonBadRequestError):
            client.get("/accounts/123")

    @patch("httpx.Client.request")
    def test_401_authentication_error(self, mock_request):
        """Test handling of 401 Authentication errors."""
        from neon_crm.exceptions import NeonAuthenticationError
        import pytest

        client = NeonClient(org_id="test", api_key="test")

        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.json.return_value = {"error": "Unauthorized"}
        mock_response.text = "Unauthorized"
        mock_request.return_value = mock_response

        with pytest.raises(NeonAuthenticationError):
            client.get("/accounts/123")

    @patch("httpx.Client.request")
    def test_403_forbidden_error(self, mock_request):
        """Test handling of 403 Forbidden errors."""
        from neon_crm.exceptions import NeonForbiddenError
        import pytest

        client = NeonClient(org_id="test", api_key="test")

        mock_response = Mock()
        mock_response.status_code = 403
        mock_response.json.return_value = {"error": "Forbidden"}
        mock_response.text = "Forbidden"
        mock_request.return_value = mock_response

        with pytest.raises(NeonForbiddenError):
            client.get("/accounts/123")

    @patch("httpx.Client.request")
    def test_404_not_found_error(self, mock_request):
        """Test handling of 404 Not Found errors."""
        from neon_crm.exceptions import NeonNotFoundError
        import pytest

        client = NeonClient(org_id="test", api_key="test")

        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.json.return_value = {"error": "Not found"}
        mock_response.text = "Not found"
        mock_request.return_value = mock_response

        with pytest.raises(NeonNotFoundError):
            client.get("/accounts/999999")

    @patch("httpx.Client.request")
    def test_429_rate_limit_error(self, mock_request):
        """Test handling of 429 Rate Limit errors."""
        from neon_crm.exceptions import NeonRateLimitError
        import pytest

        client = NeonClient(org_id="test", api_key="test")

        mock_response = Mock()
        mock_response.status_code = 429
        mock_response.headers = {"Retry-After": "60"}
        mock_response.json.return_value = {"error": "Rate limit exceeded"}
        mock_response.text = "Rate limit exceeded"
        mock_request.return_value = mock_response

        with pytest.raises(NeonRateLimitError) as exc_info:
            client.get("/accounts/123")

        assert exc_info.value.retry_after == 60

    @patch("httpx.Client.request")
    def test_500_server_error(self, mock_request):
        """Test handling of 500 Server errors."""
        from neon_crm.exceptions import NeonServerError
        import pytest

        client = NeonClient(org_id="test", api_key="test")

        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.json.return_value = {"error": "Internal server error"}
        mock_response.text = "Internal server error"
        mock_request.return_value = mock_response

        with pytest.raises(NeonServerError):
            client.get("/accounts/123")

    @patch("httpx.Client.request")
    def test_response_json_parse_error(self, mock_request):
        """Test handling when response JSON cannot be parsed."""
        from neon_crm.exceptions import NeonBadRequestError
        import pytest

        client = NeonClient(org_id="test", api_key="test")

        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_response.text = "Invalid response"
        mock_request.return_value = mock_response

        with pytest.raises(NeonBadRequestError):
            client.get("/accounts/123")
