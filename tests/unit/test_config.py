"""Tests for configuration loader functionality."""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

from neon_crm.config import ConfigLoader


class TestConfigLoader:
    """Test the ConfigLoader class."""

    def test_init_with_default_path(self):
        """Test initialization with default config path."""
        loader = ConfigLoader()
        assert loader.config_path == Path("~/.neon/config.json").expanduser()

    def test_init_with_custom_path(self):
        """Test initialization with custom config path."""
        custom_path = "/custom/path/config.json"
        loader = ConfigLoader(custom_path)
        assert loader.config_path == Path(custom_path)

    def test_get_config_with_defaults_only(self):
        """Test get_config returns defaults when no other sources available."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "nonexistent_config.json"
            loader = ConfigLoader(config_path)

            with patch.dict(os.environ, {}, clear=True):
                config = loader.get_config()

                assert config["org_id"] is None
                assert config["api_key"] is None
                assert config["environment"] == "production"
                assert config["api_version"] == "2.10"
                assert config["timeout"] == 30.0
                assert config["max_retries"] == 3
                assert config["base_url"] is None

    def test_get_config_with_env_vars(self):
        """Test get_config uses environment variables."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "nonexistent_config.json"
            loader = ConfigLoader(config_path)

            env_vars = {
                "NEON_ORG_ID": "test_org",
                "NEON_API_KEY": "test_key",
                "NEON_ENVIRONMENT": "trial",
                "NEON_API_VERSION": "2.5",
                "NEON_TIMEOUT": "45.0",
                "NEON_MAX_RETRIES": "5",
                "NEON_BASE_URL": "https://custom.api.com/v2",
            }

            with patch.dict(os.environ, env_vars, clear=True):
                config = loader.get_config()

                assert config["org_id"] == "test_org"
                assert config["api_key"] == "test_key"
                assert config["environment"] == "trial"
                assert config["api_version"] == "2.5"
                assert config["timeout"] == 45.0
                assert config["max_retries"] == 5
                assert config["base_url"] == "https://custom.api.com/v2"

    def test_get_config_with_config_file(self):
        """Test get_config uses configuration file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "config.json"
            config_data = {
                "org_id": "file_org",
                "api_key": "file_key",
                "environment": "trial",
                "api_version": "2.8",
                "timeout": 60.0,
                "max_retries": 7,
                "base_url": "https://file.api.com/v2",
            }

            with open(config_path, "w") as f:
                json.dump(config_data, f)

            loader = ConfigLoader(config_path)

            with patch.dict(os.environ, {}, clear=True):
                config = loader.get_config()

                assert config["org_id"] == "file_org"
                assert config["api_key"] == "file_key"
                assert config["environment"] == "trial"
                assert config["api_version"] == "2.8"
                assert config["timeout"] == 60.0
                assert config["max_retries"] == 7
                assert config["base_url"] == "https://file.api.com/v2"

    def test_get_config_priority_order(self):
        """Test that configuration sources follow correct priority order."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "config.json"
            config_data = {
                "org_id": "file_org",
                "api_key": "file_key",
                "environment": "trial",
            }

            with open(config_path, "w") as f:
                json.dump(config_data, f)

            loader = ConfigLoader(config_path)

            env_vars = {
                "NEON_ORG_ID": "env_org",
                "NEON_API_KEY": "env_key",
            }

            with patch.dict(os.environ, env_vars, clear=True):
                # Init params should override config file and env vars
                config = loader.get_config(org_id="init_org", api_key="init_key")

                assert config["org_id"] == "init_org"  # init param wins
                assert config["api_key"] == "init_key"  # init param wins
                assert (
                    config["environment"] == "trial"
                )  # from config file (no env var or init param)

    def test_get_config_with_partial_sources(self):
        """Test get_config with partial information from different sources."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "config.json"
            config_data = {
                "org_id": "file_org",
                "timeout": 45.0,
            }

            with open(config_path, "w") as f:
                json.dump(config_data, f)

            loader = ConfigLoader(config_path)

            env_vars = {
                "NEON_API_KEY": "env_key",
                "NEON_ENVIRONMENT": "trial",
            }

            with patch.dict(os.environ, env_vars, clear=True):
                config = loader.get_config(api_version="3.0")

                assert config["org_id"] == "file_org"  # from config file
                assert config["api_key"] == "env_key"  # from env var
                assert config["environment"] == "trial"  # from env var
                assert config["api_version"] == "3.0"  # from init param
                assert config["timeout"] == 45.0  # from config file
                assert config["max_retries"] == 3  # default value
                assert config["base_url"] is None  # default value

    def test_save_config(self):
        """Test saving configuration to file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "config.json"
            loader = ConfigLoader(config_path)

            loader.save_config(
                org_id="saved_org", api_key="saved_key", environment="trial"
            )

            # Verify file was created and contains correct data
            assert config_path.exists()
            with open(config_path) as f:
                saved_data = json.load(f)

            assert saved_data["org_id"] == "saved_org"
            assert saved_data["api_key"] == "saved_key"
            assert saved_data["environment"] == "trial"

    def test_save_config_updates_existing(self):
        """Test saving configuration updates existing file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "config.json"
            initial_data = {
                "org_id": "initial_org",
                "api_key": "initial_key",
                "timeout": 30.0,
            }

            with open(config_path, "w") as f:
                json.dump(initial_data, f)

            loader = ConfigLoader(config_path)

            # Update some values
            loader.save_config(org_id="updated_org", environment="trial")

            # Verify file was updated
            with open(config_path) as f:
                saved_data = json.load(f)

            assert saved_data["org_id"] == "updated_org"  # updated
            assert saved_data["api_key"] == "initial_key"  # preserved
            assert saved_data["timeout"] == 30.0  # preserved
            assert saved_data["environment"] == "trial"  # added

    def test_load_config_file_invalid_json(self):
        """Test handling of invalid JSON in config file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "config.json"

            # Write invalid JSON
            with open(config_path, "w") as f:
                f.write("{ invalid json }")

            loader = ConfigLoader(config_path)

            # Should not raise an exception and return defaults
            config = loader.get_config()
            assert config["environment"] == "production"  # default value
