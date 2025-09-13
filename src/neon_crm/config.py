"""Configuration management for the Neon CRM SDK."""

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional, Union

from .types import Environment


class ConfigLoader:
    """Loads configuration from various sources with priority order."""

    DEFAULT_CONFIG_PATH = "~/.neon/config.json"

    def __init__(self, config_path: Optional[Union[str, Path]] = None):
        """Initialize the config loader.

        Args:
            config_path: Path to config file. If None, uses default path.
        """
        self.config_path = Path(config_path or self.DEFAULT_CONFIG_PATH).expanduser()
        self._config_data: Optional[Dict[str, Any]] = None

    def _load_config_file(self) -> Dict[str, Any]:
        """Load configuration from file if it exists."""
        if self._config_data is not None:
            return self._config_data

        if self.config_path.exists():
            try:
                with open(self.config_path) as f:
                    self._config_data = json.load(f)
            except (OSError, json.JSONDecodeError):
                self._config_data = {}
        else:
            self._config_data = {}

        return self._config_data

    def _get_env_value(self, key: str) -> Optional[str]:
        """Get value from environment variables."""
        return os.getenv(key)

    def get_config(
        self,
        org_id: Optional[str] = None,
        api_key: Optional[str] = None,
        environment: Optional[Environment] = None,
        api_version: Optional[str] = None,
        timeout: Optional[float] = None,
        max_retries: Optional[int] = None,
        base_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get configuration with priority: init params > config file > env vars > defaults.

        Args:
            org_id: Organization ID
            api_key: API key
            environment: Environment ("production" or "trial")
            api_version: API version
            timeout: Request timeout in seconds
            max_retries: Number of retries for failed requests
            base_url: Custom base URL

        Returns:
            Dictionary with configuration values
        """
        config_file = self._load_config_file()

        # Priority order: init params > config file > env vars > defaults
        result = {
            "org_id": (
                org_id
                or config_file.get("org_id")
                or self._get_env_value("NEON_ORG_ID")
            ),
            "api_key": (
                api_key
                or config_file.get("api_key")
                or self._get_env_value("NEON_API_KEY")
            ),
            "environment": (
                environment
                or config_file.get("environment")
                or self._get_env_value("NEON_ENVIRONMENT")
                or "production"
            ),
            "api_version": (
                api_version
                or config_file.get("api_version")
                or self._get_env_value("NEON_API_VERSION")
                or "2.10"
            ),
            "timeout": (
                timeout
                or config_file.get("timeout")
                or (
                    float(self._get_env_value("NEON_TIMEOUT"))
                    if self._get_env_value("NEON_TIMEOUT")
                    else None
                )
                or 30.0
            ),
            "max_retries": (
                max_retries
                or config_file.get("max_retries")
                or (
                    int(self._get_env_value("NEON_MAX_RETRIES"))
                    if self._get_env_value("NEON_MAX_RETRIES")
                    else None
                )
                or 3
            ),
            "base_url": (
                base_url
                or config_file.get("base_url")
                or self._get_env_value("NEON_BASE_URL")
            ),
        }

        return result

    def save_config(self, **kwargs) -> None:
        """Save configuration to file.

        Args:
            **kwargs: Configuration values to save
        """
        # Create directory if it doesn't exist
        self.config_path.parent.mkdir(parents=True, exist_ok=True)

        # Load existing config and update with new values
        config = self._load_config_file()
        config.update(kwargs)

        # Save to file
        with open(self.config_path, "w") as f:
            json.dump(config, f, indent=2)

        # Update cached config
        self._config_data = config
