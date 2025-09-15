"""Configuration management for the Neon CRM SDK."""

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional, Union

from .types import Environment


class ConfigLoader:
    """Loads configuration from various sources with priority order.

    Supports profiles for managing multiple environments (prod, sandbox, etc).
    """

    DEFAULT_CONFIG_PATH = "~/.neon/config.json"
    DEFAULT_PROFILE = "default"

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

    def _get_profile_config(
        self, config_data: Dict[str, Any], profile: str
    ) -> Dict[str, Any]:
        """Get configuration for a specific profile.

        Args:
            config_data: Full config data from file
            profile: Profile name to extract

        Returns:
            Configuration for the specified profile
        """
        # If profiles section exists, look for the specified profile
        if "profiles" in config_data:
            profiles = config_data["profiles"]
            if profile in profiles:
                # Return profile-specific config, falling back to top-level defaults
                profile_config = profiles[profile].copy()
                # Merge with top-level config (profile takes precedence)
                top_level = {k: v for k, v in config_data.items() if k != "profiles"}
                result = {**top_level, **profile_config}
                return result
            elif profile != self.DEFAULT_PROFILE:
                raise ValueError(
                    f"Profile '{profile}' not found in config file. "
                    f"Available profiles: {list(profiles.keys())}"
                )

        # No profiles section or using default profile - return top-level config
        return {k: v for k, v in config_data.items() if k != "profiles"}

    def get_config(
        self,
        profile: Optional[str] = None,
        org_id: Optional[str] = None,
        api_key: Optional[str] = None,
        environment: Optional[Environment] = None,
        api_version: Optional[str] = None,
        timeout: Optional[float] = None,
        max_retries: Optional[int] = None,
        base_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get configuration with priority: init params > profile config > env vars > defaults.

        Args:
            profile: Profile name to use from config file. If None, uses env var NEON_PROFILE or 'default'
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
        config_file_data = self._load_config_file()

        # Determine which profile to use
        active_profile = (
            profile or self._get_env_value("NEON_PROFILE") or self.DEFAULT_PROFILE
        )

        # Get profile-specific config
        profile_config = self._get_profile_config(config_file_data, active_profile)

        # Priority order: init params > profile config > env vars > defaults
        result = {
            "org_id": (
                org_id
                or profile_config.get("org_id")
                or self._get_env_value("NEON_ORG_ID")
            ),
            "api_key": (
                api_key
                or profile_config.get("api_key")
                or self._get_env_value("NEON_API_KEY")
            ),
            "environment": (
                environment
                or profile_config.get("environment")
                or self._get_env_value("NEON_ENVIRONMENT")
                or "production"
            ),
            "api_version": (
                api_version
                or profile_config.get("api_version")
                or self._get_env_value("NEON_API_VERSION")
                or "2.10"
            ),
            "timeout": (
                timeout
                or profile_config.get("timeout")
                or (
                    float(self._get_env_value("NEON_TIMEOUT"))
                    if self._get_env_value("NEON_TIMEOUT")
                    else None
                )
                or 30.0
            ),
            "max_retries": (
                max_retries
                or profile_config.get("max_retries")
                or (
                    int(self._get_env_value("NEON_MAX_RETRIES"))
                    if self._get_env_value("NEON_MAX_RETRIES")
                    else None
                )
                or 3
            ),
            "base_url": (
                base_url
                or profile_config.get("base_url")
                or self._get_env_value("NEON_BASE_URL")
            ),
        }

        # Add the active profile to the result for reference
        result["active_profile"] = active_profile

        return result

    def list_profiles(self) -> list[str]:
        """List all available profiles in the config file.

        Returns:
            List of profile names
        """
        config_data = self._load_config_file()
        if "profiles" in config_data:
            return list(config_data["profiles"].keys())
        return [self.DEFAULT_PROFILE]

    def save_config(self, profile: Optional[str] = None, **kwargs) -> None:
        """Save configuration to file.

        Args:
            profile: Profile name to save to. If None, saves to top-level config
            **kwargs: Configuration values to save
        """
        # Create directory if it doesn't exist
        self.config_path.parent.mkdir(parents=True, exist_ok=True)

        # Load existing config
        config = self._load_config_file()

        if profile and profile != self.DEFAULT_PROFILE:
            # Save to a specific profile
            if "profiles" not in config:
                config["profiles"] = {}
            if profile not in config["profiles"]:
                config["profiles"][profile] = {}
            config["profiles"][profile].update(kwargs)
        else:
            # Save to top-level config (default profile)
            # Remove from profiles section to avoid conflicts
            filtered_kwargs = {k: v for k, v in kwargs.items() if k != "profiles"}
            config.update(filtered_kwargs)

        # Save to file
        with open(self.config_path, "w") as f:
            json.dump(config, f, indent=2)

        # Update cached config
        self._config_data = config

    def delete_profile(self, profile: str) -> None:
        """Delete a profile from the config file.

        Args:
            profile: Profile name to delete

        Raises:
            ValueError: If trying to delete the default profile or profile doesn't exist
        """
        if profile == self.DEFAULT_PROFILE:
            raise ValueError(
                f"Cannot delete the default profile '{self.DEFAULT_PROFILE}'"
            )

        config = self._load_config_file()
        if "profiles" not in config or profile not in config["profiles"]:
            raise ValueError(f"Profile '{profile}' not found")

        del config["profiles"][profile]

        # If no profiles left, remove the profiles section
        if not config["profiles"]:
            del config["profiles"]

        # Save to file
        with open(self.config_path, "w") as f:
            json.dump(config, f, indent=2)

        # Update cached config
        self._config_data = config
