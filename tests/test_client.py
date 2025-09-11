"""Tests for the Neon CRM client."""

import os
from unittest.mock import MagicMock, patch

import pytest

from neon_crm import NeonClient
from neon_crm.exceptions import NeonAuthenticationError


class TestNeonClient:
    """Test cases for the NeonClient class."""

    def test_client_initialization_with_params(self):
        """Test client initialization with explicit parameters."""
        client = NeonClient(
            org_id="test_org", api_key="test_key", environment="production"
        )

        assert client.org_id == "test_org"
        assert client.api_key == "test_key"
        assert client.environment == "production"
        assert client.base_url == "https://api.neoncrm.com/v2"

    def test_client_initialization_with_env_vars(self):
        """Test client initialization with environment variables."""
        with patch.dict(
            os.environ, {"NEON_ORG_ID": "env_org", "NEON_API_KEY": "env_key"}
        ):
            client = NeonClient()
            assert client.org_id == "env_org"
            assert client.api_key == "env_key"

    def test_client_initialization_missing_org_id(self):
        """Test client initialization fails when org_id is missing."""
        with pytest.raises(ValueError, match="org_id is required"):
            NeonClient(api_key="test_key")

    def test_client_initialization_missing_api_key(self):
        """Test client initialization fails when api_key is missing."""
        with pytest.raises(ValueError, match="api_key is required"):
            NeonClient(org_id="test_org")

    def test_trial_environment_url(self):
        """Test that trial environment uses correct URL."""
        client = NeonClient(org_id="test_org", api_key="test_key", environment="trial")
        assert client.base_url == "https://trial.neoncrm.com/v2"

    def test_custom_base_url(self):
        """Test client with custom base URL."""
        custom_url = "https://custom.neoncrm.com/v2"
        client = NeonClient(org_id="test_org", api_key="test_key", base_url=custom_url)
        assert client.base_url == custom_url

    def test_resource_initialization(self):
        """Test that resource managers are properly initialized."""
        client = NeonClient(org_id="test_org", api_key="test_key")

        # Check that key resources are available
        assert hasattr(client, "accounts")
        assert hasattr(client, "donations")
        assert hasattr(client, "events")
        assert hasattr(client, "memberships")
        assert hasattr(client, "volunteers")

    def test_default_headers(self):
        """Test that default headers are properly set."""
        client = NeonClient(org_id="test_org", api_key="test_key")
        headers = client._get_default_headers()

        assert "Authorization" in headers
        assert "NEON-API-VERSION" in headers
        assert "Content-Type" in headers
        assert "Accept" in headers
        assert "User-Agent" in headers

        assert headers["NEON-API-VERSION"] == "2.10"
        assert headers["Content-Type"] == "application/json"
        assert headers["Accept"] == "application/json"

    @patch("httpx.Client")
    def test_context_manager(self, mock_client_class):
        """Test client as context manager."""
        mock_client_instance = MagicMock()
        mock_client_class.return_value = mock_client_instance

        with NeonClient(org_id="test_org", api_key="test_key") as client:
            assert client is not None

        # Verify close was called
        mock_client_instance.close.assert_called_once()


class TestNeonClientRequests:
    """Test cases for NeonClient HTTP requests."""

    @patch("httpx.Client")
    def test_successful_get_request(self, mock_client_class):
        """Test successful GET request."""
        mock_client_instance = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"test": "data"}
        mock_client_instance.request.return_value = mock_response
        mock_client_class.return_value = mock_client_instance

        client = NeonClient(org_id="test_org", api_key="test_key")
        result = client.get("/test")

        assert result == {"test": "data"}
        mock_client_instance.request.assert_called_once()

    @patch("httpx.Client")
    def test_authentication_error_handling(self, mock_client_class):
        """Test handling of 401 authentication errors."""
        mock_client_instance = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.json.return_value = {"error": "Unauthorized"}
        mock_client_instance.request.return_value = mock_response
        mock_client_class.return_value = mock_client_instance

        client = NeonClient(org_id="test_org", api_key="test_key")

        with pytest.raises(NeonAuthenticationError):
            client.get("/test")
