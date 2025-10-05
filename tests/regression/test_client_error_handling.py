"""Regression tests for NeonClient error handling.

These tests are slower and test real error scenarios that may involve retries,
rate limiting, and other time-consuming operations.
"""

from unittest.mock import Mock, patch

import pytest

from neon_crm.client import NeonClient
from neon_crm.exceptions import NeonRateLimitError


class TestClientRateLimiting:
    """Test client rate limiting behavior."""

    def setup_method(self):
        """Set up test fixtures."""
        self.client = NeonClient(org_id="test", api_key="test")

    @patch("httpx.Client.request")
    def test_429_rate_limit_error(self, mock_request):
        """Test 429 Rate Limit error handling.

        This test is in regression because rate limit handling may involve
        delays or retries that make it too slow for unit tests.
        """
        mock_response = Mock()
        mock_response.status_code = 429
        mock_response.headers = {"Retry-After": "60"}
        mock_response.json.return_value = {"error": "Rate limit exceeded"}
        mock_request.return_value = mock_response

        with pytest.raises(NeonRateLimitError) as exc_info:
            self.client.get("/test")

        assert exc_info.value.retry_after == 60
