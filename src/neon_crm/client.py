"""Main client for the Neon CRM SDK."""

import base64
import os
from typing import Any, Dict, Optional
from urllib.parse import urljoin

import httpx

from .exceptions import (
    NeonAPIError,
    NeonAuthenticationError,
    NeonConnectionError,
    NeonForbiddenError,
    NeonNotFoundError,
    NeonRateLimitError,
    NeonTimeoutError,
)
from .resources import (
    AccountsResource,
    ActivitiesResource,
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
from .governance import PermissionContext, UserPermissions, PermissionConfig


class NeonClient:
    """Synchronous client for the Neon CRM API."""

    def __init__(
        self,
        org_id: Optional[str] = None,
        api_key: Optional[str] = None,
        environment: Environment = "production",
        api_version: str = "2.10",
        timeout: float = 30.0,
        max_retries: int = 3,
        base_url: Optional[str] = None,
        user_permissions: Optional[UserPermissions] = None,
        permission_config: Optional[PermissionConfig] = None,
    ) -> None:
        """Initialize the Neon CRM client.

        Args:
            org_id: Your Neon organization ID. If not provided, will look for NEON_ORG_ID env var.
            api_key: Your API key. If not provided, will look for NEON_API_KEY env var.
            environment: "production" or "trial". Defaults to production.
            api_version: API version to use. Defaults to "2.10".
            timeout: Request timeout in seconds. Defaults to 30.0.
            max_retries: Number of retries for failed requests. Defaults to 3.
            base_url: Custom base URL. If provided, overrides environment setting.
            user_permissions: User permissions for access control. If provided, enables governance.
            permission_config: Permission configuration system. If not provided, uses default.
        """
        self.org_id = org_id or os.getenv("NEON_ORG_ID")
        self.api_key = api_key or os.getenv("NEON_API_KEY")

        if not self.org_id:
            raise ValueError(
                "org_id is required. Provide it directly or set NEON_ORG_ID environment variable."
            )
        if not self.api_key:
            raise ValueError(
                "api_key is required. Provide it directly or set NEON_API_KEY environment variable."
            )

        self.environment = environment
        self.api_version = api_version
        self.timeout = timeout
        self.max_retries = max_retries
        
        # Set up governance
        self.user_permissions = user_permissions
        self.permission_config = permission_config or PermissionConfig()

        # Set base URL
        if base_url:
            self.base_url = base_url
        elif environment == "trial":
            self.base_url = "https://trial.neoncrm.com/v2"
        else:
            self.base_url = "https://api.neoncrm.com/v2"

        # Create HTTP client
        self._client = httpx.Client(
            timeout=timeout,
            headers=self._get_default_headers(),
        )

        # Initialize resource managers
        self.accounts = AccountsResource(self)
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
        
    def set_user_permissions(self, permissions: UserPermissions):
        """Set user permissions for this client session.
        
        Args:
            permissions: UserPermissions object containing user's access rights
        """
        self.user_permissions = permissions
    
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
    
    def get_permission_context(self) -> PermissionContext:
        """Get a permission context manager for this client's user permissions.
        
        Returns:
            PermissionContext that can be used as a context manager
            
        Raises:
            ValueError: If no user permissions are set
        """
        if self.user_permissions is None:
            raise ValueError("No user permissions set. Call set_user_permissions() first.")
        
        return PermissionContext(self.user_permissions)

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

        # Handle specific error codes
        if response.status_code == 401:
            raise NeonAuthenticationError(response_data=response_data)
        elif response.status_code == 403:
            raise NeonForbiddenError(response_data=response_data)
        elif response.status_code == 404:
            raise NeonNotFoundError(response_data=response_data)
        elif response.status_code == 429:
            retry_after = response.headers.get("Retry-After")
            retry_after_int = int(retry_after) if retry_after else None
            raise NeonRateLimitError(
                retry_after=retry_after_int, response_data=response_data
            )
        else:
            message = response_data.get("message", f"API error: {response.status_code}")
            raise NeonAPIError(message, response.status_code, response_data)

    def request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Make an HTTP request to the API.

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
        """
        url = urljoin(self.base_url, endpoint.lstrip("/"))

        # Merge headers
        request_headers = self._get_default_headers()
        if headers:
            request_headers.update(headers)

        try:
            # Set permission context if user permissions are available
            if self.user_permissions:
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

        except httpx.TimeoutException as e:
            raise NeonTimeoutError(
                timeout=self.timeout, details={"original_error": str(e)}
            )
        except httpx.ConnectError as e:
            raise NeonConnectionError(original_error=e, details={"url": url})
        except httpx.HTTPStatusError as e:
            return self._handle_response(e.response)

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

    def close(self) -> None:
        """Close the HTTP client."""
        self._client.close()

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
        org_id: Optional[str] = None,
        api_key: Optional[str] = None,
        environment: Environment = "production",
        api_version: str = "2.10",
        timeout: float = 30.0,
        max_retries: int = 3,
        base_url: Optional[str] = None,
    ) -> None:
        """Initialize the async Neon CRM client.

        Args:
            org_id: Your Neon organization ID. If not provided, will look for NEON_ORG_ID env var.
            api_key: Your API key. If not provided, will look for NEON_API_KEY env var.
            environment: "production" or "trial". Defaults to production.
            api_version: API version to use. Defaults to "2.10".
            timeout: Request timeout in seconds. Defaults to 30.0.
            max_retries: Number of retries for failed requests. Defaults to 3.
            base_url: Custom base URL. If provided, overrides environment setting.
        """
        self.org_id = org_id or os.getenv("NEON_ORG_ID")
        self.api_key = api_key or os.getenv("NEON_API_KEY")

        if not self.org_id:
            raise ValueError(
                "org_id is required. Provide it directly or set NEON_ORG_ID environment variable."
            )
        if not self.api_key:
            raise ValueError(
                "api_key is required. Provide it directly or set NEON_API_KEY environment variable."
            )

        self.environment = environment
        self.api_version = api_version
        self.timeout = timeout
        self.max_retries = max_retries

        # Set base URL
        if base_url:
            self.base_url = base_url
        elif environment == "trial":
            self.base_url = "https://trial.neoncrm.com/v2"
        else:
            self.base_url = "https://api.neoncrm.com/v2"

        # HTTP client will be created when needed
        self._client: Optional[httpx.AsyncClient] = None

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

    def _get_client(self) -> httpx.AsyncClient:
        """Get or create the HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=self.timeout,
                headers=self._get_default_headers(),
            )
        return self._client

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

        # Handle specific error codes
        if response.status_code == 401:
            raise NeonAuthenticationError(response_data=response_data)
        elif response.status_code == 403:
            raise NeonForbiddenError(response_data=response_data)
        elif response.status_code == 404:
            raise NeonNotFoundError(response_data=response_data)
        elif response.status_code == 429:
            retry_after = response.headers.get("Retry-After")
            retry_after_int = int(retry_after) if retry_after else None
            raise NeonRateLimitError(
                retry_after=retry_after_int, response_data=response_data
            )
        else:
            message = response_data.get("message", f"API error: {response.status_code}")
            raise NeonAPIError(message, response.status_code, response_data)

    async def request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Make an async HTTP request to the API.

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
        """
        client = self._get_client()
        url = urljoin(self.base_url, endpoint.lstrip("/"))

        # Merge headers
        request_headers = self._get_default_headers()
        if headers:
            request_headers.update(headers)

        try:
            response = await client.request(
                method=method,
                url=url,
                params=params,
                json=json_data,
                headers=request_headers,
            )
            return self._handle_response(response)

        except httpx.TimeoutException as e:
            raise NeonTimeoutError(
                timeout=self.timeout, details={"original_error": str(e)}
            )
        except httpx.ConnectError as e:
            raise NeonConnectionError(original_error=e, details={"url": url})
        except httpx.HTTPStatusError as e:
            return self._handle_response(e.response)

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
