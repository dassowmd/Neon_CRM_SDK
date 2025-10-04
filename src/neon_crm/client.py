"""Main client for the Neon CRM SDK."""

import asyncio
import base64
import os
import random
import time
from pathlib import Path
from typing import Any, Dict, Optional, Union
from urllib.parse import urljoin

import httpx

from .cache import NeonCache
from .config import ConfigLoader
from .exceptions import (
    NeonAPIError,
    NeonAuthenticationError,
    NeonBadRequestError,
    NeonConflictError,
    NeonConnectionError,
    NeonForbiddenError,
    NeonNotFoundError,
    NeonRateLimitError,
    NeonServerError,
    NeonTimeoutError,
    NeonUnprocessableEntityError,
    NeonUnsupportedMediaTypeError,
)
from .logging import NeonLogger
from .resources import (
    AccountsResource,
    ActivitiesResource,
    AddressesResource,
    CampaignsResource,
    CustomFieldsResource,
    CustomObjectsResource,
    DonationsResource,
    EventsResource,
    GrantsResource,
    HouseholdsResource,
    MembershipsResource,
    OnlineStoreResource,
    OrdersResource,
    PaymentsResource,
    PledgesResource,
    PropertiesResource,
    RecurringDonationsResource,
    SoftCreditsResource,
    VolunteersResource,
    WebhooksResource,
)
from .types import Environment
from .governance import (
    PermissionContext,
    UserPermissions,
    PermissionConfig,
    Role,
    ResourceType,
    Permission,
    create_user_permissions,
)


class NeonClient:
    """Synchronous client for the Neon CRM API."""

    def __init__(
        self,
        profile: Optional[str] = None,
        org_id: Optional[str] = None,
        api_key: Optional[str] = None,
        environment: Optional[Environment] = None,
        api_version: Optional[str] = None,
        timeout: Optional[float] = None,
        max_retries: Optional[int] = None,
        base_url: Optional[str] = None,
        config_path: Optional[Union[str, Path]] = None,
        log_level: Optional[str] = None,
        enable_caching: bool = True,
        enable_field_cache: Optional[bool] = None,
        user_permissions: Optional[UserPermissions] = None,
        permission_config: Optional[PermissionConfig] = None,
        default_role: Optional[Union[str, Role]] = None,
        permission_overrides: Optional[Dict[Union[str, ResourceType], set]] = None,
        enable_governance: Optional[bool] = None,
    ) -> None:
        """Initialize the Neon CRM client.

        Args:
            profile: Profile name to use from config file. If not provided, will look in NEON_PROFILE env var or use 'default'.
            org_id: Your Neon organization ID. If not provided, will look in config file then NEON_ORG_ID env var.
            api_key: Your API key. If not provided, will look in config file then NEON_API_KEY env var.
            environment: "production" or "trial". If not provided, will look in config file then NEON_ENVIRONMENT env var, defaults to "production".
            api_version: API version to use. If not provided, will look in config file then NEON_API_VERSION env var, defaults to "2.10".
            timeout: Request timeout in seconds. If not provided, will look in config file then NEON_TIMEOUT env var, defaults to 30.0.
            max_retries: Number of retries for failed requests. If not provided, will look in config file then NEON_MAX_RETRIES env var, defaults to 3.
            base_url: Custom base URL. If provided, overrides environment setting. Can also be set in config file or NEON_BASE_URL env var.
            config_path: Path to configuration file. Defaults to ~/.neon/config.json.
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL). If not provided, will look in NEON_LOG_LEVEL env var, defaults to INFO.
            enable_caching: Whether to enable caching for custom fields, objects, etc. (default: True).
            enable_field_cache: Whether to enable field discovery caching (default: True unless NEON_DISABLE_FIELD_CACHE=true).
            user_permissions: (Advanced) User permissions for access control. Use default_role instead for simpler configuration.
            permission_config: (Advanced) Permission configuration system. If not provided, uses default.
            default_role: Default role for all operations. Can be a Role enum or string ('viewer', 'editor', 'admin', 'fundraiser', 'event_manager', 'volunteer_coordinator').
                         If not provided, will look in NEON_DEFAULT_ROLE env var. If still not set, defaults to 'viewer' (read-only).
            permission_overrides: Dict mapping resource types to sets of permissions to override the default role.
                                 Example: {ResourceType.DONATIONS: {Permission.READ, Permission.WRITE}}
                                 Can also use strings: {"donations": {"read", "write"}}
            enable_governance: Whether to enable governance checks. If not provided, will look in NEON_ENABLE_GOVERNANCE env var.
                              Defaults to True. Set to False to disable permission checks (not recommended).
        """
        # Setup logging first
        if log_level:
            NeonLogger.set_level_from_string(log_level)
        self._logger = NeonLogger.get_logger("client")

        # Setup caching
        self._cache = NeonCache() if enable_caching else None

        # Setup field cache control - check environment variable if not explicitly set
        if enable_field_cache is None:
            enable_field_cache = (
                os.getenv("NEON_DISABLE_FIELD_CACHE", "false").lower() != "true"
            )
        self.field_cache_enabled = enable_field_cache
        self._field_caches = {}  # Per-resource field caches

        # Load configuration using config loader
        config_loader = ConfigLoader(config_path)
        config = config_loader.get_config(
            profile=profile,
            org_id=org_id,
            api_key=api_key,
            environment=environment,
            api_version=api_version,
            timeout=timeout,
            max_retries=max_retries,
            base_url=base_url,
        )

        self.org_id = config["org_id"]
        self.api_key = config["api_key"]
        self.active_profile = config["active_profile"]

        if not self.org_id:
            raise ValueError(
                "org_id is required. Provide it directly, in config file, or set NEON_ORG_ID environment variable."
            )
        if not self.api_key:
            raise ValueError(
                "api_key is required. Provide it directly, in config file, or set NEON_API_KEY environment variable."
            )

        self.environment = config["environment"]
        self.api_version = config["api_version"]
        self.timeout = config["timeout"]
        self.max_retries = config["max_retries"]

        # Set up governance
        self.permission_config = permission_config or PermissionConfig()
        self.governance_enabled = self._determine_governance_enabled(enable_governance)

        # Configure user permissions
        if user_permissions:
            # Advanced usage: user provided explicit permissions
            self.user_permissions = user_permissions
        elif self.governance_enabled or default_role or permission_overrides:
            # Simplified usage: create permissions from role and overrides
            self.user_permissions = self._create_permissions_from_config(
                default_role, permission_overrides
            )
        else:
            # No governance configured
            self.user_permissions = None

        # Set permissions in context so permission checks can access them
        if self.user_permissions:
            from .governance.access_control import _current_permissions

            _current_permissions.set(self.user_permissions)

        # Set base URL
        if config["base_url"]:
            self.base_url = config["base_url"]
        elif self.environment == "trial":
            self.base_url = "https://trial.neoncrm.com/v2/"
        else:
            self.base_url = "https://api.neoncrm.com/v2/"

        # Create HTTP client
        self._client = httpx.Client(
            timeout=self.timeout,
            headers=self._get_default_headers(),
        )

        # Initialize resource managers
        self.accounts = AccountsResource(self)
        self.addresses = AddressesResource(self)
        self.donations = DonationsResource(self)
        self.events = EventsResource(self)
        self.memberships = MembershipsResource(self)
        self.activities = ActivitiesResource(self)
        self.campaigns = CampaignsResource(self)
        self.custom_fields = CustomFieldsResource(self)
        self.custom_objects = CustomObjectsResource(self)
        self.grants = GrantsResource(self)
        self.households = HouseholdsResource(self)
        self.online_store = OnlineStoreResource(self)
        self.orders = OrdersResource(self)
        self.payments = PaymentsResource(self)
        self.pledges = PledgesResource(self)
        self.properties = PropertiesResource(self)
        self.recurring_donations = RecurringDonationsResource(self)
        self.soft_credits = SoftCreditsResource(self)
        self.volunteers = VolunteersResource(self)
        self.webhooks = WebhooksResource(self)

    def _determine_governance_enabled(self, enable_governance: Optional[bool]) -> bool:
        """Determine if governance should be enabled based on parameters and environment.

        Args:
            enable_governance: Explicit governance setting from initialization

        Returns:
            True if governance should be enabled
        """
        if enable_governance is not None:
            return enable_governance

        # Check environment variable
        env_value = os.getenv("NEON_ENABLE_GOVERNANCE", "").lower()
        if env_value in ("true", "1", "yes"):
            return True
        elif env_value in ("false", "0", "no"):
            return False

        # Default to True - governance enabled by default
        return True

    def _create_permissions_from_config(
        self,
        default_role: Optional[Union[str, Role]],
        permission_overrides: Optional[Dict[Union[str, ResourceType], set]],
    ) -> UserPermissions:
        """Create user permissions from simplified configuration.

        Args:
            default_role: Role name or Role enum
            permission_overrides: Resource permission overrides

        Returns:
            UserPermissions object
        """
        # Determine the role
        if default_role is None:
            # Check environment variable
            role_str = os.getenv("NEON_DEFAULT_ROLE", "viewer").lower()
        elif isinstance(default_role, Role):
            role_str = default_role.value
        else:
            role_str = str(default_role).lower()

        # Parse role
        try:
            role = Role(role_str)
        except ValueError:
            self._logger.warning(
                f"Invalid role '{role_str}', defaulting to 'viewer' (read-only)"
            )
            role = Role.VIEWER

        # Process permission overrides
        processed_overrides = {}
        if permission_overrides:
            for resource_key, permissions in permission_overrides.items():
                # Convert resource key to ResourceType
                if isinstance(resource_key, ResourceType):
                    resource = resource_key
                else:
                    try:
                        resource = ResourceType(str(resource_key).lower())
                    except ValueError:
                        self._logger.warning(
                            f"Invalid resource type '{resource_key}', skipping override"
                        )
                        continue

                # Convert permissions to Permission enums
                perm_set = set()
                for perm in permissions:
                    if isinstance(perm, Permission):
                        perm_set.add(perm)
                    else:
                        try:
                            perm_set.add(Permission(str(perm).lower()))
                        except ValueError:
                            self._logger.warning(
                                f"Invalid permission '{perm}', skipping"
                            )
                            continue

                processed_overrides[resource] = perm_set

        # Create and return permissions
        return create_user_permissions(
            user_id="client_user", role=role, custom_overrides=processed_overrides
        )

    def set_user_permissions(self, permissions: UserPermissions):
        """Set user permissions for this client session.

        Args:
            permissions: UserPermissions object containing user's access rights
        """
        self.user_permissions = permissions
        if permissions and not self.governance_enabled:
            self.governance_enabled = True

    def set_user_by_id(self, user_id: str) -> bool:
        """Set user permissions by looking up user ID in the permission config.

        Args:
            user_id: The user identifier to look up

        Returns:
            True if user was found and permissions set, False otherwise
        """
        permissions = self.permission_config.get_user_permissions(user_id)
        if permissions:
            self.user_permissions = permissions
            return True
        return False

    def _calculate_retry_delay(
        self, attempt: int, retry_after: Optional[int] = None
    ) -> float:
        """Calculate delay for retry with exponential backoff and jitter.

        Args:
            attempt: Current retry attempt (0-indexed)
            retry_after: Retry-After header value in seconds if provided by server

        Returns:
            Delay in seconds
        """
        if retry_after is not None:
            # Honor server's Retry-After header with small jitter
            return retry_after + random.uniform(0.1, 1.0)

        # Exponential backoff: 2^attempt seconds with jitter
        base_delay = 2**attempt
        # Add jitter to prevent thundering herd
        jitter = random.uniform(0.1, 0.5) * base_delay
        return min(base_delay + jitter, 60.0)  # Cap at 60 seconds

    def _get_default_headers(self) -> Dict[str, str]:
        """Get default headers for API requests."""
        # Create basic auth header
        credentials = f"{self.org_id}:{self.api_key}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()

        return {
            "Authorization": f"Basic {encoded_credentials}",
            "NEON-API-VERSION": self.api_version,
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "neon-crm-python-sdk/0.1.0",
        }

    def _format_error_message(self, status_code: int, response_data: Any) -> str:
        """Format a detailed error message from API response."""
        base_message = f"HTTP {status_code}"

        # If response_data is a list (like your example), extract error messages
        if isinstance(response_data, list):
            error_messages = []
            for error in response_data:
                if isinstance(error, dict):
                    code = error.get("code", "Unknown")
                    message = error.get("message", "No message provided")
                    error_messages.append(f"[Code {code}] {message}")
                else:
                    error_messages.append(str(error))
            if error_messages:
                return f"{base_message}: " + "; ".join(error_messages)

        # If response_data is a dict, extract common error fields
        elif isinstance(response_data, dict):
            error_parts = []

            # Check for common error message fields
            if "message" in response_data:
                error_parts.append(response_data["message"])
            elif "error" in response_data:
                error_parts.append(str(response_data["error"]))
            elif "detail" in response_data:
                error_parts.append(response_data["detail"])

            # Check for validation errors or error lists
            if "errors" in response_data:
                errors = response_data["errors"]
                if isinstance(errors, list):
                    for error in errors:
                        if isinstance(error, dict):
                            code = error.get("code", "Unknown")
                            message = error.get("message", "No message provided")
                            error_parts.append(f"[Code {code}] {message}")
                        else:
                            error_parts.append(str(error))

            if error_parts:
                return f"{base_message}: " + "; ".join(error_parts)

        # Fallback to basic message with response data if available
        if response_data:
            return f"{base_message}: {str(response_data)}"

        return f"{base_message}: Error occurred"

    def _handle_response(self, response: httpx.Response) -> Dict[str, Any]:
        """Handle API response and raise appropriate exceptions."""
        if response.status_code == 200:
            try:
                return response.json()
            except ValueError:
                return {}

        # Get response data for error context
        try:
            response_data = response.json()
        except ValueError:
            response_data = {"error": response.text}

        # Create detailed error message
        detailed_message = self._format_error_message(
            response.status_code, response_data
        )

        # Handle specific error codes with detailed messages
        if response.status_code == 400:
            raise NeonBadRequestError(
                message=detailed_message, response_data=response_data
            )
        elif response.status_code == 401:
            raise NeonAuthenticationError(
                message=detailed_message, response_data=response_data
            )
        elif response.status_code == 403:
            raise NeonForbiddenError(
                message=detailed_message, response_data=response_data
            )
        elif response.status_code == 404:
            raise NeonNotFoundError(
                message=detailed_message, response_data=response_data
            )
        elif response.status_code == 409:
            raise NeonConflictError(
                message=detailed_message, response_data=response_data
            )
        elif response.status_code == 415:
            raise NeonUnsupportedMediaTypeError(
                message=detailed_message, response_data=response_data
            )
        elif response.status_code == 422:
            raise NeonUnprocessableEntityError(
                message=detailed_message, response_data=response_data
            )
        elif response.status_code == 429:
            retry_after = response.headers.get("Retry-After")
            retry_after_int = int(retry_after) if retry_after else None
            raise NeonRateLimitError(
                message=detailed_message,
                retry_after=retry_after_int,
                response_data=response_data,
            )
        elif 500 <= response.status_code < 600:
            raise NeonServerError(
                message=detailed_message,
                status_code=response.status_code,
                response_data=response_data,
            )
        else:
            raise NeonAPIError(detailed_message, response.status_code, response_data)

    def _recreate_client_if_needed(self) -> None:
        """Recreate the HTTP client if it has been closed."""
        if self._client.is_closed:
            self._logger.warning("HTTP client was closed, recreating connection")
            self._client = httpx.Client(
                timeout=self.timeout,
                headers=self._get_default_headers(),
            )

    def request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Make an HTTP request to the API with retry logic for rate limits.

        Args:
            method: HTTP method (GET, POST, PUT, PATCH, DELETE)
            endpoint: API endpoint (e.g., "/accounts")
            params: Query parameters
            json_data: JSON data for request body
            headers: Additional headers

        Returns:
            Response data as dictionary

        Raises:
            NeonAPIError: For API errors
            NeonTimeoutError: For timeout errors
            NeonConnectionError: For connection errors
            NeonRateLimitError: For rate limit errors after all retries exhausted
        """
        url = urljoin(self.base_url, endpoint.lstrip("/"))

        # Merge headers
        request_headers = self._get_default_headers()
        if headers:
            request_headers.update(headers)

        last_exception = None

        for attempt in range(self.max_retries + 1):
            try:
                # Check if client is closed and recreate if needed
                self._recreate_client_if_needed()

                # Set permission context if governance is enabled and permissions are available
                if self.governance_enabled and self.user_permissions:
                    with PermissionContext(self.user_permissions):
                        response = self._client.request(
                            method=method,
                            url=url,
                            params=params,
                            json=json_data,
                            headers=request_headers,
                        )
                        return self._handle_response(response)
                else:
                    response = self._client.request(
                        method=method,
                        url=url,
                        params=params,
                        json=json_data,
                        headers=request_headers,
                    )
                    return self._handle_response(response)

            except NeonRateLimitError as e:
                last_exception = e
                if attempt == self.max_retries:
                    # Final attempt, don't retry
                    raise

                # Calculate delay based on Retry-After header or exponential backoff
                delay = self._calculate_retry_delay(attempt, e.retry_after)
                time.sleep(delay)
                continue

            except httpx.TimeoutException as e:
                last_exception = NeonTimeoutError(
                    timeout=self.timeout, details={"original_error": str(e)}
                )
                if attempt == self.max_retries:
                    raise last_exception from e

                # Retry on timeout with exponential backoff
                delay = self._calculate_retry_delay(attempt)
                time.sleep(delay)
                continue

            except httpx.ConnectError as e:
                last_exception = NeonConnectionError(
                    original_error=e, details={"url": url}
                )
                if attempt == self.max_retries:
                    raise last_exception from e

                # Retry on connection error with exponential backoff
                delay = self._calculate_retry_delay(attempt)
                time.sleep(delay)
                continue

            except (httpx.NetworkError, httpx.RemoteProtocolError) as e:
                # Handle other network-related errors
                last_exception = NeonConnectionError(
                    original_error=e,
                    details={"url": url, "error_type": type(e).__name__},
                )
                if attempt == self.max_retries:
                    raise last_exception from e

                # Retry on network error with exponential backoff
                delay = self._calculate_retry_delay(attempt)
                time.sleep(delay)
                continue

            except NeonServerError as e:
                # Retry on certain server errors (502 Bad Gateway, 503 Service Unavailable, 504 Gateway Timeout)
                if e.status_code in (502, 503, 504):
                    last_exception = e
                    if attempt == self.max_retries:
                        self._logger.error(
                            f"Server error {e.status_code} after {self.max_retries} retries: {url}"
                        )
                        raise

                    # Retry on server error with exponential backoff
                    delay = self._calculate_retry_delay(attempt)
                    self._logger.warning(
                        f"Server error {e.status_code}, retrying in {delay:.2f}s (attempt {attempt + 1}/{self.max_retries + 1}): {url}"
                    )
                    time.sleep(delay)
                    continue
                else:
                    # Don't retry on other server errors (500, 501, etc.)
                    raise

            except httpx.HTTPStatusError as e:
                return self._handle_response(e.response)
            except RuntimeError as e:
                # Handle "client has been closed" errors
                if (
                    "client has been closed" in str(e).lower()
                    or "closed" in str(e).lower()
                ):
                    last_exception = NeonConnectionError(
                        message="HTTP client was closed during request",
                        original_error=e,
                        details={"url": url, "attempt": attempt + 1},
                    )
                    if attempt == self.max_retries:
                        self._logger.error(
                            f"Client closed error after {self.max_retries} retries: {url}"
                        )
                        raise last_exception from e

                    # Force recreation of client and retry
                    self._logger.warning(
                        f"Client closed during request, recreating and retrying (attempt {attempt + 1}/{self.max_retries + 1}): {url}"
                    )
                    self._client.close()  # Ensure properly closed first
                    self._client = httpx.Client(
                        timeout=self.timeout,
                        headers=self._get_default_headers(),
                    )

                    delay = self._calculate_retry_delay(attempt)
                    time.sleep(delay)
                    continue
                else:
                    raise e
            except Exception as e:
                raise e

        # This shouldn't be reached, but just in case
        if last_exception:
            raise last_exception

    def get(
        self, endpoint: str, params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make a GET request."""
        return self.request("GET", endpoint, params=params)

    def post(
        self,
        endpoint: str,
        json_data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Make a POST request."""
        return self.request("POST", endpoint, params=params, json_data=json_data)

    def put(
        self,
        endpoint: str,
        json_data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Make a PUT request."""
        return self.request("PUT", endpoint, params=params, json_data=json_data)

    def patch(
        self,
        endpoint: str,
        json_data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Make a PATCH request."""
        return self.request("PATCH", endpoint, params=params, json_data=json_data)

    def delete(
        self, endpoint: str, params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make a DELETE request."""
        return self.request("DELETE", endpoint, params=params)

    def clear_cache(self) -> None:
        """Clear all cached data."""
        if self._cache:
            self._cache.clear_all()
            self._logger.debug("Cache cleared")

    def get_cache_stats(self) -> Dict[str, int]:
        """Get cache statistics.

        Returns:
            Dictionary with cache names and their sizes, empty dict if caching disabled
        """
        return self._cache.get_cache_stats() if self._cache else {}

    def close(self) -> None:
        """Close the HTTP client."""
        self._client.close()

    def clear_field_cache(self, resource: Optional[str] = None) -> None:
        """Clear field discovery cache.

        Args:
            resource: Specific resource to clear cache for. If None, clears all.
        """
        if resource:
            self._field_caches.pop(resource, None)
            self._logger.debug(f"Cleared field cache for {resource}")
        else:
            self._field_caches.clear()
            self._logger.debug("Cleared all field caches")

    def refresh_field_cache(self, resource: Optional[str] = None) -> None:
        """Force refresh field discovery cache.

        Args:
            resource: Specific resource to refresh cache for. If None, refreshes all.
        """
        if resource:
            # Clear the cache for this resource so it gets reloaded
            self._field_caches.pop(resource, None)
            self._logger.debug(f"Refreshed field cache for {resource}")
        else:
            # Clear all caches so they get reloaded
            self._field_caches.clear()
            self._logger.debug("Refreshed all field caches")

    def get_field_cache_status(self) -> Dict[str, bool]:
        """Get field cache status for all resources.

        Returns:
            Dictionary mapping resource names to cache status (True if cached).
        """
        return {
            resource: bool(cache_data)
            for resource, cache_data in self._field_caches.items()
        }

    def __enter__(self) -> "NeonClient":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        self.close()


class AsyncNeonClient:
    """Asynchronous client for the Neon CRM API."""

    def __init__(
        self,
        profile: Optional[str] = None,
        org_id: Optional[str] = None,
        api_key: Optional[str] = None,
        environment: Optional[Environment] = None,
        api_version: Optional[str] = None,
        timeout: Optional[float] = None,
        max_retries: Optional[int] = None,
        base_url: Optional[str] = None,
        config_path: Optional[Union[str, Path]] = None,
        log_level: Optional[str] = None,
        enable_caching: bool = True,
    ) -> None:
        """Initialize the async Neon CRM client.

        Args:
            profile: Profile name to use from config file. If not provided, will look in NEON_PROFILE env var or use 'default'.
            org_id: Your Neon organization ID. If not provided, will look in config file then NEON_ORG_ID env var.
            api_key: Your API key. If not provided, will look in config file then NEON_API_KEY env var.
            environment: "production" or "trial". If not provided, will look in config file then NEON_ENVIRONMENT env var, defaults to "production".
            api_version: API version to use. If not provided, will look in config file then NEON_API_VERSION env var, defaults to "2.10".
            timeout: Request timeout in seconds. If not provided, will look in config file then NEON_TIMEOUT env var, defaults to 30.0.
            max_retries: Number of retries for failed requests. If not provided, will look in config file then NEON_MAX_RETRIES env var, defaults to 3.
            base_url: Custom base URL. If provided, overrides environment setting. Can also be set in config file or NEON_BASE_URL env var.
            config_path: Path to configuration file. Defaults to ~/.neon/config.json.
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL). If not provided, will look in NEON_LOG_LEVEL env var, defaults to INFO.
            enable_caching: Whether to enable caching for custom fields, objects, etc. (default: True).
        """
        # Setup logging first
        if log_level:
            NeonLogger.set_level_from_string(log_level)
        self._logger = NeonLogger.get_logger("async_client")

        # Setup caching
        self._cache = NeonCache() if enable_caching else None

        # Load configuration using config loader
        config_loader = ConfigLoader(config_path)
        config = config_loader.get_config(
            profile=profile,
            org_id=org_id,
            api_key=api_key,
            environment=environment,
            api_version=api_version,
            timeout=timeout,
            max_retries=max_retries,
            base_url=base_url,
        )

        self.org_id = config["org_id"]
        self.api_key = config["api_key"]
        self.active_profile = config["active_profile"]

        if not self.org_id:
            raise ValueError(
                "org_id is required. Provide it directly, in config file, or set NEON_ORG_ID environment variable."
            )
        if not self.api_key:
            raise ValueError(
                "api_key is required. Provide it directly, in config file, or set NEON_API_KEY environment variable."
            )

        self.environment = config["environment"]
        self.api_version = config["api_version"]
        self.timeout = config["timeout"]
        self.max_retries = config["max_retries"]

        # Set base URL
        if config["base_url"]:
            self.base_url = config["base_url"]
        elif self.environment == "trial":
            self.base_url = "https://trial.neoncrm.com/v2"
        else:
            self.base_url = "https://api.neoncrm.com/v2"

        # HTTP client will be created when needed
        self._client: Optional[httpx.AsyncClient] = None

    def _calculate_retry_delay(
        self, attempt: int, retry_after: Optional[int] = None
    ) -> float:
        """Calculate delay for retry with exponential backoff and jitter.

        Args:
            attempt: Current retry attempt (0-indexed)
            retry_after: Retry-After header value in seconds if provided by server

        Returns:
            Delay in seconds
        """
        if retry_after is not None:
            # Honor server's Retry-After header with small jitter
            return retry_after + random.uniform(0.1, 1.0)

        # Exponential backoff: 2^attempt seconds with jitter
        base_delay = 2**attempt
        # Add jitter to prevent thundering herd
        jitter = random.uniform(0.1, 0.5) * base_delay
        return min(base_delay + jitter, 60.0)  # Cap at 60 seconds

    def _get_default_headers(self) -> Dict[str, str]:
        """Get default headers for API requests."""
        # Create basic auth header
        credentials = f"{self.org_id}:{self.api_key}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()

        return {
            "Authorization": f"Basic {encoded_credentials}",
            "NEON-API-VERSION": self.api_version,
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "neon-crm-python-sdk/0.1.0",
        }

    def _format_error_message(self, status_code: int, response_data: Any) -> str:
        """Format a detailed error message from API response."""
        base_message = f"HTTP {status_code}"

        # If response_data is a list (like your example), extract error messages
        if isinstance(response_data, list):
            error_messages = []
            for error in response_data:
                if isinstance(error, dict):
                    code = error.get("code", "Unknown")
                    message = error.get("message", "No message provided")
                    error_messages.append(f"[Code {code}] {message}")
                else:
                    error_messages.append(str(error))
            if error_messages:
                return f"{base_message}: " + "; ".join(error_messages)

        # If response_data is a dict, extract common error fields
        elif isinstance(response_data, dict):
            error_parts = []

            # Check for common error message fields
            if "message" in response_data:
                error_parts.append(response_data["message"])
            elif "error" in response_data:
                error_parts.append(str(response_data["error"]))
            elif "detail" in response_data:
                error_parts.append(response_data["detail"])

            # Check for validation errors or error lists
            if "errors" in response_data:
                errors = response_data["errors"]
                if isinstance(errors, list):
                    for error in errors:
                        if isinstance(error, dict):
                            code = error.get("code", "Unknown")
                            message = error.get("message", "No message provided")
                            error_parts.append(f"[Code {code}] {message}")
                        else:
                            error_parts.append(str(error))

            if error_parts:
                return f"{base_message}: " + "; ".join(error_parts)

        # Fallback to basic message with response data if available
        if response_data:
            return f"{base_message}: {str(response_data)}"

        return f"{base_message}: Error occurred"

    def _get_client(self) -> httpx.AsyncClient:
        """Get or create the HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=self.timeout,
                headers=self._get_default_headers(),
            )
        return self._client

    async def _recreate_client_if_needed(self) -> None:
        """Recreate the async HTTP client if it has been closed."""
        if self._client is not None and self._client.is_closed:
            self._logger.warning("Async HTTP client was closed, recreating connection")
            self._client = httpx.AsyncClient(
                timeout=self.timeout,
                headers=self._get_default_headers(),
            )

    def _handle_response(self, response: httpx.Response) -> Dict[str, Any]:
        """Handle API response and raise appropriate exceptions."""
        if response.status_code == 200:
            try:
                return response.json()
            except ValueError:
                return {}

        # Get response data for error context
        try:
            response_data = response.json()
        except ValueError:
            response_data = {"error": response.text}

        # Create detailed error message
        detailed_message = self._format_error_message(
            response.status_code, response_data
        )

        # Handle specific error codes with detailed messages
        if response.status_code == 400:
            raise NeonBadRequestError(
                message=detailed_message, response_data=response_data
            )
        elif response.status_code == 401:
            raise NeonAuthenticationError(
                message=detailed_message, response_data=response_data
            )
        elif response.status_code == 403:
            raise NeonForbiddenError(
                message=detailed_message, response_data=response_data
            )
        elif response.status_code == 404:
            raise NeonNotFoundError(
                message=detailed_message, response_data=response_data
            )
        elif response.status_code == 409:
            raise NeonConflictError(
                message=detailed_message, response_data=response_data
            )
        elif response.status_code == 415:
            raise NeonUnsupportedMediaTypeError(
                message=detailed_message, response_data=response_data
            )
        elif response.status_code == 422:
            raise NeonUnprocessableEntityError(
                message=detailed_message, response_data=response_data
            )
        elif response.status_code == 429:
            retry_after = response.headers.get("Retry-After")
            retry_after_int = int(retry_after) if retry_after else None
            raise NeonRateLimitError(
                message=detailed_message,
                retry_after=retry_after_int,
                response_data=response_data,
            )
        elif 500 <= response.status_code < 600:
            raise NeonServerError(
                message=detailed_message,
                status_code=response.status_code,
                response_data=response_data,
            )
        else:
            raise NeonAPIError(detailed_message, response.status_code, response_data)

    async def request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Make an async HTTP request to the API with retry logic for rate limits.

        Args:
            method: HTTP method (GET, POST, PUT, PATCH, DELETE)
            endpoint: API endpoint (e.g., "/accounts")
            params: Query parameters
            json_data: JSON data for request body
            headers: Additional headers

        Returns:
            Response data as dictionary

        Raises:
            NeonAPIError: For API errors
            NeonTimeoutError: For timeout errors
            NeonConnectionError: For connection errors
            NeonRateLimitError: For rate limit errors after all retries exhausted
        """
        client = self._get_client()
        url = urljoin(self.base_url, endpoint.lstrip("/"))

        # Merge headers
        request_headers = self._get_default_headers()
        if headers:
            request_headers.update(headers)

        last_exception = None

        for attempt in range(self.max_retries + 1):
            try:
                # Check if client is closed and recreate if needed
                await self._recreate_client_if_needed()
                client = self._get_client()

                response = await client.request(
                    method=method,
                    url=url,
                    params=params,
                    json=json_data,
                    headers=request_headers,
                )
                return self._handle_response(response)

            except NeonRateLimitError as e:
                last_exception = e
                if attempt == self.max_retries:
                    # Final attempt, don't retry
                    raise

                # Calculate delay based on Retry-After header or exponential backoff
                delay = self._calculate_retry_delay(attempt, e.retry_after)
                await asyncio.sleep(delay)
                continue

            except httpx.TimeoutException as e:
                last_exception = NeonTimeoutError(
                    timeout=self.timeout, details={"original_error": str(e)}
                )
                if attempt == self.max_retries:
                    raise last_exception from e

                # Retry on timeout with exponential backoff
                delay = self._calculate_retry_delay(attempt)
                await asyncio.sleep(delay)
                continue

            except httpx.ConnectError as e:
                last_exception = NeonConnectionError(
                    original_error=e, details={"url": url}
                )
                if attempt == self.max_retries:
                    raise last_exception from e

                # Retry on connection error with exponential backoff
                delay = self._calculate_retry_delay(attempt)
                await asyncio.sleep(delay)
                continue

            except (httpx.NetworkError, httpx.RemoteProtocolError) as e:
                # Handle other network-related errors
                last_exception = NeonConnectionError(
                    original_error=e,
                    details={"url": url, "error_type": type(e).__name__},
                )
                if attempt == self.max_retries:
                    raise last_exception from e

                # Retry on network error with exponential backoff
                delay = self._calculate_retry_delay(attempt)
                await asyncio.sleep(delay)
                continue

            except NeonServerError as e:
                # Retry on certain server errors (502 Bad Gateway, 503 Service Unavailable, 504 Gateway Timeout)
                if e.status_code in (502, 503, 504):
                    last_exception = e
                    if attempt == self.max_retries:
                        raise

                    # Retry on server error with exponential backoff
                    delay = self._calculate_retry_delay(attempt)
                    await asyncio.sleep(delay)
                    continue
                else:
                    # Don't retry on other server errors (500, 501, etc.)
                    raise

            except httpx.HTTPStatusError as e:
                return self._handle_response(e.response)
            except RuntimeError as e:
                # Handle "client has been closed" errors
                if (
                    "client has been closed" in str(e).lower()
                    or "closed" in str(e).lower()
                ):
                    last_exception = NeonConnectionError(
                        message="Async HTTP client was closed during request",
                        original_error=e,
                        details={"url": url, "attempt": attempt + 1},
                    )
                    if attempt == self.max_retries:
                        self._logger.error(
                            f"Async client closed error after {self.max_retries} retries: {url}"
                        )
                        raise last_exception from e

                    # Force recreation of client and retry
                    self._logger.warning(
                        f"Async client closed during request, recreating and retrying (attempt {attempt + 1}/{self.max_retries + 1}): {url}"
                    )
                    if self._client:
                        await self._client.aclose()  # Ensure properly closed first
                    self._client = httpx.AsyncClient(
                        timeout=self.timeout,
                        headers=self._get_default_headers(),
                    )

                    delay = self._calculate_retry_delay(attempt)
                    await asyncio.sleep(delay)
                    continue
                else:
                    raise e

        # This shouldn't be reached, but just in case
        if last_exception:
            raise last_exception

    async def get(
        self, endpoint: str, params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make an async GET request."""
        return await self.request("GET", endpoint, params=params)

    async def post(
        self,
        endpoint: str,
        json_data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Make an async POST request."""
        return await self.request("POST", endpoint, params=params, json_data=json_data)

    async def put(
        self,
        endpoint: str,
        json_data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Make an async PUT request."""
        return await self.request("PUT", endpoint, params=params, json_data=json_data)

    async def patch(
        self,
        endpoint: str,
        json_data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Make an async PATCH request."""
        return await self.request("PATCH", endpoint, params=params, json_data=json_data)

    async def delete(
        self, endpoint: str, params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make an async DELETE request."""
        return await self.request("DELETE", endpoint, params=params)

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()

    async def __aenter__(self) -> "AsyncNeonClient":
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        await self.close()
