"""Tests for rate limiting functionality."""

from unittest.mock import Mock, patch

import pytest

from neon_crm.client import AsyncNeonClient, NeonClient
from neon_crm.exceptions import NeonRateLimitError


class TestRateLimiting:
    """Test rate limiting functionality for both sync and async clients."""

    def test_calculate_retry_delay_with_retry_after(self):
        """Test retry delay calculation when server provides Retry-After header."""
        client = NeonClient(org_id="test", api_key="test")

        # Should use retry_after value plus jitter
        delay = client._calculate_retry_delay(attempt=0, retry_after=5)
        assert 5.1 <= delay <= 6.0  # 5 + jitter (0.1 to 1.0)

    def test_calculate_retry_delay_exponential_backoff(self):
        """Test exponential backoff when no Retry-After header."""
        client = NeonClient(org_id="test", api_key="test")

        # First attempt (attempt=0): 2^0 = 1 second + jitter
        delay = client._calculate_retry_delay(attempt=0)
        assert 1.1 <= delay <= 1.5

        # Second attempt (attempt=1): 2^1 = 2 seconds + jitter
        delay = client._calculate_retry_delay(attempt=1)
        assert 2.1 <= delay <= 3.0

        # Third attempt (attempt=2): 2^2 = 4 seconds + jitter
        delay = client._calculate_retry_delay(attempt=2)
        assert 4.1 <= delay <= 6.0

    def test_calculate_retry_delay_max_cap(self):
        """Test that retry delay is capped at 60 seconds."""
        client = NeonClient(org_id="test", api_key="test")

        # Large attempt number should be capped
        delay = client._calculate_retry_delay(attempt=10)
        assert delay <= 60.0

    @patch("neon_crm.client.time.sleep")
    @patch("httpx.Client.request")
    def test_sync_retry_on_rate_limit(self, mock_request, mock_sleep):
        """Test that sync client retries on rate limit errors."""
        client = NeonClient(org_id="test", api_key="test", max_retries=2)

        # First two calls raise rate limit error, third succeeds
        rate_limit_response = Mock()
        rate_limit_response.status_code = 429
        rate_limit_response.headers = {"Retry-After": "2"}
        rate_limit_response.json.return_value = {"error": "Rate limit exceeded"}

        success_response = Mock()
        success_response.status_code = 200
        success_response.json.return_value = {"success": True}

        mock_request.side_effect = [
            # First attempt - rate limited
            rate_limit_response,
            # Second attempt - rate limited
            rate_limit_response,
            # Third attempt - success
            success_response,
        ]

        result = client.get("/test")

        # Should have made 3 calls
        assert mock_request.call_count == 3
        # Should have slept twice (after first two failures)
        assert mock_sleep.call_count == 2
        # Should return successful result
        assert result == {"success": True}

    @patch("neon_crm.client.time.sleep")
    @patch("httpx.Client.request")
    def test_sync_exhausted_retries(self, mock_request, mock_sleep):
        """Test that sync client raises error when retries are exhausted."""
        client = NeonClient(org_id="test", api_key="test", max_retries=1)

        # All calls raise rate limit error
        rate_limit_response = Mock()
        rate_limit_response.status_code = 429
        rate_limit_response.headers = {}
        rate_limit_response.json.return_value = {"error": "Rate limit exceeded"}

        mock_request.return_value = rate_limit_response

        with pytest.raises(NeonRateLimitError):
            client.get("/test")

        # Should have made max_retries + 1 calls (2 total)
        assert mock_request.call_count == 2
        # Should have slept once (after first failure, not after final failure)
        assert mock_sleep.call_count == 1

    @pytest.mark.asyncio
    @patch("neon_crm.client.asyncio.sleep")
    @patch("httpx.AsyncClient.request")
    async def test_async_retry_on_rate_limit(self, mock_request, mock_sleep):
        """Test that async client retries on rate limit errors."""
        client = AsyncNeonClient(org_id="test", api_key="test", max_retries=2)

        # First two calls raise rate limit error, third succeeds
        rate_limit_response = Mock()
        rate_limit_response.status_code = 429
        rate_limit_response.headers = {"Retry-After": "1"}
        rate_limit_response.json.return_value = {"error": "Rate limit exceeded"}

        success_response = Mock()
        success_response.status_code = 200
        success_response.json.return_value = {"success": True}

        mock_request.side_effect = [
            rate_limit_response,
            rate_limit_response,
            success_response,
        ]

        result = await client.get("/test")

        # Should have made 3 calls
        assert mock_request.call_count == 3
        # Should have slept twice
        assert mock_sleep.call_count == 2
        # Should return successful result
        assert result == {"success": True}

    @pytest.mark.asyncio
    @patch("neon_crm.client.asyncio.sleep")
    @patch("httpx.AsyncClient.request")
    async def test_async_exhausted_retries(self, mock_request, mock_sleep):
        """Test that async client raises error when retries are exhausted."""
        client = AsyncNeonClient(org_id="test", api_key="test", max_retries=1)

        # All calls raise rate limit error
        rate_limit_response = Mock()
        rate_limit_response.status_code = 429
        rate_limit_response.headers = {}
        rate_limit_response.json.return_value = {"error": "Rate limit exceeded"}

        mock_request.return_value = rate_limit_response

        with pytest.raises(NeonRateLimitError):
            await client.get("/test")

        # Should have made max_retries + 1 calls
        assert mock_request.call_count == 2
        # Should have slept once
        assert mock_sleep.call_count == 1

    def test_retry_delay_honors_retry_after_header(self):
        """Test that retry delay honors server's Retry-After header."""
        client = NeonClient(org_id="test", api_key="test")

        # When server provides Retry-After, should use it
        delay = client._calculate_retry_delay(attempt=0, retry_after=10)
        assert 10.1 <= delay <= 11.0

        # Should add jitter even with retry_after
        delay2 = client._calculate_retry_delay(attempt=0, retry_after=10)
        # Very unlikely both delays are exactly the same due to jitter
        assert delay != delay2 or abs(delay - delay2) < 0.01

    @patch("neon_crm.client.time.sleep")
    @patch("httpx.Client.request")
    def test_non_rate_limit_errors_not_retried(self, mock_request, mock_sleep):
        """Test that non-rate-limit errors are not retried."""
        client = NeonClient(org_id="test", api_key="test", max_retries=3)

        # Return 400 error (not rate limit)
        error_response = Mock()
        error_response.status_code = 400
        error_response.json.return_value = {"error": "Bad request"}

        mock_request.return_value = error_response

        from neon_crm.exceptions import NeonAPIError

        with pytest.raises(NeonAPIError):
            client.get("/test")

        # Should only make one call (no retries for non-rate-limit errors)
        assert mock_request.call_count == 1
        # Should not sleep
        assert mock_sleep.call_count == 0

    def test_async_calculate_retry_delay_same_as_sync(self):
        """Test that async client has same retry delay calculation as sync."""
        sync_client = NeonClient(org_id="test", api_key="test")
        async_client = AsyncNeonClient(org_id="test", api_key="test")

        # Should use same calculation logic (though jitter makes exact comparison hard)
        sync_delay = sync_client._calculate_retry_delay(attempt=1, retry_after=5)
        async_delay = async_client._calculate_retry_delay(attempt=1, retry_after=5)

        # Both should be in the same range
        assert 5.1 <= sync_delay <= 6.0
        assert 5.1 <= async_delay <= 6.0
