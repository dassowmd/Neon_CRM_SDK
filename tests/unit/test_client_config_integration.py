"""Tests for NeonClient configuration integration."""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from neon_crm.client import AsyncNeonClient, NeonClient


class TestNeonClientConfigIntegration:
    """Test NeonClient integration with configuration loader."""

    def test_client_uses_init_params(self):
        """Test that client prioritizes init parameters."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "config.json"

            client = NeonClient(
                org_id="init_org",
                api_key="init_key",
                environment="trial",
                config_path=config_path,
            )

            assert client.org_id == "init_org"
            assert client.api_key == "init_key"
            assert client.environment == "trial"
            assert client.base_url == "https://trial.neoncrm.com/v2/"

    def test_client_uses_config_file(self):
        """Test that client uses config file when init params not provided."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "config.json"
            config_data = {
                "org_id": "file_org",
                "api_key": "file_key",
                "environment": "trial",
                "api_version": "2.5",
                "timeout": 45.0,
            }

            with open(config_path, "w") as f:
                json.dump(config_data, f)

            with patch.dict(os.environ, {}, clear=True):
                client = NeonClient(config_path=config_path)

                assert client.org_id == "file_org"
                assert client.api_key == "file_key"
                assert client.environment == "trial"
                assert client.api_version == "2.5"
                assert client.timeout == 45.0

    def test_client_uses_env_vars(self):
        """Test that client uses environment variables as fallback."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "nonexistent.json"

            env_vars = {
                "NEON_ORG_ID": "env_org",
                "NEON_API_KEY": "env_key",
                "NEON_ENVIRONMENT": "trial",
            }

            with patch.dict(os.environ, env_vars, clear=True):
                client = NeonClient(config_path=config_path)

                assert client.org_id == "env_org"
                assert client.api_key == "env_key"
                assert client.environment == "trial"

    def test_client_priority_order(self):
        """Test that client follows correct configuration priority."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "config.json"
            config_data = {"org_id": "file_org", "api_key": "file_key", "timeout": 60.0}

            with open(config_path, "w") as f:
                json.dump(config_data, f)

            env_vars = {"NEON_ORG_ID": "env_org", "NEON_TIMEOUT": "90.0"}

            with patch.dict(os.environ, env_vars, clear=True):
                client = NeonClient(
                    org_id="init_org",  # Should override file and env
                    config_path=config_path,
                )

                assert client.org_id == "init_org"  # init param wins
                assert client.api_key == "file_key"  # from config file
                assert client.timeout == 60.0  # from config file (not env)

    def test_client_missing_required_config_raises_error(self):
        """Test that client raises error when required config is missing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "nonexistent.json"

            with patch.dict(os.environ, {}, clear=True):
                with pytest.raises(ValueError, match="org_id is required"):
                    NeonClient(config_path=config_path)

    def test_client_custom_base_url_from_config(self):
        """Test that client uses custom base URL from config."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "config.json"
            config_data = {
                "org_id": "test_org",
                "api_key": "test_key",
                "base_url": "https://custom.neon.com/v2",
            }

            with open(config_path, "w") as f:
                json.dump(config_data, f)

            with patch.dict(os.environ, {}, clear=True):
                client = NeonClient(config_path=config_path)

                assert client.base_url == "https://custom.neon.com/v2"


class TestAsyncNeonClientConfigIntegration:
    """Test AsyncNeonClient integration with configuration loader."""

    def test_async_client_uses_init_params(self):
        """Test that async client prioritizes init parameters."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "config.json"

            client = AsyncNeonClient(
                org_id="init_org",
                api_key="init_key",
                environment="trial",
                config_path=config_path,
            )

            assert client.org_id == "init_org"
            assert client.api_key == "init_key"
            assert client.environment == "trial"
            assert client.base_url == "https://trial.neoncrm.com/v2/"

    def test_async_client_uses_config_file(self):
        """Test that async client uses config file when init params not provided."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "config.json"
            config_data = {
                "org_id": "file_org",
                "api_key": "file_key",
                "environment": "production",
                "api_version": "2.8",
            }

            with open(config_path, "w") as f:
                json.dump(config_data, f)

            with patch.dict(os.environ, {}, clear=True):
                client = AsyncNeonClient(config_path=config_path)

                assert client.org_id == "file_org"
                assert client.api_key == "file_key"
                assert client.environment == "production"
                assert client.api_version == "2.8"

    def test_async_client_missing_required_config_raises_error(self):
        """Test that async client raises error when required config is missing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "nonexistent.json"

            with patch.dict(os.environ, {}, clear=True):
                with pytest.raises(ValueError, match="api_key is required"):
                    AsyncNeonClient(org_id="test_org", config_path=config_path)
