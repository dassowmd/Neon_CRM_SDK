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
        assert client.base_url == "https://api.neoncrm.com/v2"
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


class TestNeonClientHTTPMethods:
    """Test NeonClient HTTP methods."""

    def setup_method(self):
        """Set up test fixtures."""
        self.client = NeonClient(org_id="test", api_key="test")

    @patch("httpx.Client.request")
    def test_get_request_success(self, mock_request):
        """Test successful GET request."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": "test"}
        mock_request.return_value = mock_response

        result = self.client.get("/test")

        assert result == {"data": "test"}
        mock_request.assert_called_once_with(
            "GET", "https://api.neoncrm.com/v2/test", params=None, json=None, timeout=30
        )

    @patch("httpx.Client.request")
    def test_post_request_success(self, mock_request):
        """Test successful POST request."""
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"id": 123}
        mock_request.return_value = mock_response

        data = {"name": "test"}
        result = self.client.post("/test", json_data=data)

        assert result == {"id": 123}
        mock_request.assert_called_once_with(
            "POST",
            "https://api.neoncrm.com/v2/test",
            params=None,
            json=data,
            timeout=30,
        )

    @patch("httpx.Client.request")
    def test_put_request_success(self, mock_request):
        """Test successful PUT request."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"updated": True}
        mock_request.return_value = mock_response

        data = {"name": "updated"}
        result = self.client.put("/test/123", json_data=data)

        assert result == {"updated": True}

    @patch("httpx.Client.request")
    def test_patch_request_success(self, mock_request):
        """Test successful PATCH request."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"patched": True}
        mock_request.return_value = mock_response

        data = {"field": "value"}
        result = self.client.patch("/test/123", json_data=data)

        assert result == {"patched": True}

    @patch("httpx.Client.request")
    def test_delete_request_success(self, mock_request):
        """Test successful DELETE request."""
        mock_response = Mock()
        mock_response.status_code = 204
        mock_response.json.return_value = {}
        mock_request.return_value = mock_response

        result = self.client.delete("/test/123")

        assert result == {}

    @patch("httpx.Client.request")
    def test_request_with_params(self, mock_request):
        """Test request with query parameters."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": "test"}
        mock_request.return_value = mock_response

        params = {"page": 1, "size": 10}
        self.client.get("/test", params=params)

        mock_request.assert_called_once_with(
            "GET",
            "https://api.neoncrm.com/v2/test",
            params=params,
            json=None,
            timeout=30,
        )


class TestNeonClientErrorHandling:
    """Test NeonClient error handling."""

    def setup_method(self):
        """Set up test fixtures."""
        self.client = NeonClient(org_id="test", api_key="test")

    @patch("httpx.Client.request")
    def test_400_bad_request_error(self, mock_request):
        """Test 400 Bad Request error handling."""
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.json.return_value = {"error": "Bad request"}
        mock_request.return_value = mock_response

        with pytest.raises(NeonBadRequestError):
            self.client.get("/test")

    @patch("httpx.Client.request")
    def test_401_authentication_error(self, mock_request):
        """Test 401 Authentication error handling."""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.json.return_value = {"error": "Unauthorized"}
        mock_request.return_value = mock_response

        with pytest.raises(NeonAuthenticationError):
            self.client.get("/test")

    @patch("httpx.Client.request")
    def test_403_forbidden_error(self, mock_request):
        """Test 403 Forbidden error handling."""
        mock_response = Mock()
        mock_response.status_code = 403
        mock_response.json.return_value = {"error": "Forbidden"}
        mock_request.return_value = mock_response

        with pytest.raises(NeonForbiddenError):
            self.client.get("/test")

    @patch("httpx.Client.request")
    def test_404_not_found_error(self, mock_request):
        """Test 404 Not Found error handling."""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.json.return_value = {"error": "Not found"}
        mock_request.return_value = mock_response

        with pytest.raises(NeonNotFoundError):
            self.client.get("/test")

    @patch("httpx.Client.request")
    def test_422_unprocessable_entity_error(self, mock_request):
        """Test 422 Unprocessable Entity error handling."""
        mock_response = Mock()
        mock_response.status_code = 422
        mock_response.json.return_value = {"error": "Validation failed"}
        mock_request.return_value = mock_response

        with pytest.raises(NeonUnprocessableEntityError):
            self.client.get("/test")

    @patch("httpx.Client.request")
    def test_429_rate_limit_error(self, mock_request):
        """Test 429 Rate Limit error handling."""
        mock_response = Mock()
        mock_response.status_code = 429
        mock_response.headers = {"Retry-After": "60"}
        mock_response.json.return_value = {"error": "Rate limit exceeded"}
        mock_request.return_value = mock_response

        with pytest.raises(NeonRateLimitError) as exc_info:
            self.client.get("/test")

        assert exc_info.value.retry_after == 60

    @patch("httpx.Client.request")
    def test_500_server_error(self, mock_request):
        """Test 500 Server Error handling."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.json.return_value = {"error": "Internal server error"}
        mock_request.return_value = mock_response

        with pytest.raises(NeonServerError):
            self.client.get("/test")

    @patch("httpx.Client.request")
    def test_connection_error(self, mock_request):
        """Test connection error handling."""
        mock_request.side_effect = httpx.ConnectError("Connection failed")

        with pytest.raises(NeonConnectionError):
            self.client.get("/test")

    @patch("httpx.Client.request")
    def test_timeout_error(self, mock_request):
        """Test timeout error handling."""
        mock_request.side_effect = httpx.TimeoutException("Request timed out")

        with pytest.raises(NeonTimeoutError):
            self.client.get("/test")


class TestNeonClientRetryLogic:
    """Test NeonClient retry logic for server errors."""

    def setup_method(self):
        """Set up test fixtures."""
        self.client = NeonClient(org_id="test", api_key="test")

    @patch("httpx.Client.request")
    @patch("time.sleep")
    def test_retry_on_502_bad_gateway(self, mock_sleep, mock_request):
        """Test retry logic for 502 Bad Gateway."""
        # First call fails with 502, second succeeds
        mock_responses = [
            Mock(status_code=502, json=lambda: {"error": "Bad Gateway"}),
            Mock(status_code=200, json=lambda: {"data": "success"}),
        ]
        mock_request.side_effect = mock_responses

        result = self.client.get("/test")

        assert result == {"data": "success"}
        assert mock_request.call_count == 2
        mock_sleep.assert_called_once()

    @patch("httpx.Client.request")
    @patch("time.sleep")
    def test_retry_on_503_service_unavailable(self, mock_sleep, mock_request):
        """Test retry logic for 503 Service Unavailable."""
        mock_responses = [
            Mock(status_code=503, json=lambda: {"error": "Service Unavailable"}),
            Mock(status_code=200, json=lambda: {"data": "success"}),
        ]
        mock_request.side_effect = mock_responses

        result = self.client.get("/test")

        assert result == {"data": "success"}
        assert mock_request.call_count == 2

    @patch("httpx.Client.request")
    @patch("time.sleep")
    def test_retry_on_504_gateway_timeout(self, mock_sleep, mock_request):
        """Test retry logic for 504 Gateway Timeout."""
        mock_responses = [
            Mock(status_code=504, json=lambda: {"error": "Gateway Timeout"}),
            Mock(status_code=200, json=lambda: {"data": "success"}),
        ]
        mock_request.side_effect = mock_responses

        result = self.client.get("/test")

        assert result == {"data": "success"}
        assert mock_request.call_count == 2

    @patch("httpx.Client.request")
    @patch("time.sleep")
    def test_retry_exhausted(self, mock_sleep, mock_request):
        """Test when all retries are exhausted."""
        # All calls fail with 502
        mock_request.return_value = Mock(
            status_code=502, json=lambda: {"error": "Bad Gateway"}
        )

        with pytest.raises(NeonServerError):
            self.client.get("/test")

        # Should try 3 times (initial + 2 retries)
        assert mock_request.call_count == 3
        assert mock_sleep.call_count == 2

    @patch("httpx.Client.request")
    def test_no_retry_on_client_errors(self, mock_request):
        """Test that client errors (4xx) are not retried."""
        mock_request.return_value = Mock(
            status_code=400, json=lambda: {"error": "Bad Request"}
        )

        with pytest.raises(NeonBadRequestError):
            self.client.get("/test")

        # Should only try once
        assert mock_request.call_count == 1


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


class TestNeonClientHeaders:
    """Test NeonClient request headers."""

    def setup_method(self):
        """Set up test fixtures."""
        self.client = NeonClient(org_id="test_org", api_key="test_key")

    def test_default_headers(self):
        """Test that default headers are set correctly."""
        headers = self.client._get_default_headers()

        assert "Authorization" in headers
        assert "Content-Type" in headers
        assert "User-Agent" in headers
        assert "NEON-ORG-ID" in headers

        assert headers["Content-Type"] == "application/json"
        assert headers["NEON-ORG-ID"] == "test_org"
        assert "neon-crm-sdk" in headers["User-Agent"]

    def test_authorization_header(self):
        """Test that authorization header is properly encoded."""
        headers = self.client._get_default_headers()
        auth_header = headers["Authorization"]

        assert auth_header.startswith("Basic ")

        # Decode and verify
        import base64

        encoded_creds = auth_header.split(" ")[1]
        decoded_creds = base64.b64decode(encoded_creds).decode()
        assert decoded_creds == "test_org:test_key"

    @patch("httpx.Client.request")
    def test_headers_sent_in_request(self, mock_request):
        """Test that headers are included in requests."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": "test"}
        mock_request.return_value = mock_response

        self.client.get("/test")

        # Verify the request was made with proper headers
        call_args = mock_request.call_args
        assert "headers" in call_args.kwargs

        headers = call_args.kwargs["headers"]
        assert "Authorization" in headers
        assert "NEON-ORG-ID" in headers


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
            "accounts": [{"accountId": 123, "firstName": "John"}],
            "pagination": {"currentPage": 0, "totalPages": 1},
        }
        mock_request.return_value = mock_response

        # This should work end-to-end
        accounts = list(client.accounts.list(limit=1))

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
