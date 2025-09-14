"""Main client for the Neon CRM SDK."""

import asyncio
import base64
import random
import time
from pathlib import Path
from typing import Any, Dict, Optional, Union
from urllib.parse import urljoin

import httpx

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


class NeonClient:
    """Synchronous client for the Neon CRM API."""

    def __init__(
        self,
        org_id: Optional[str] = None,
        api_key: Optional[str] = None,
        environment: Optional[Environment] = None,
        api_version: Optional[str] = None,
        timeout: Optional[float] = None,
        max_retries: Optional[int] = None,
        base_url: Optional[str] = None,
        config_path: Optional[Union[str, Path]] = None,
    ) -> None:
        """Initialize the Neon CRM client.

        Args:
            org_id: Your Neon organization ID. If not provided, will look in config file then NEON_ORG_ID env var.
            api_key: Your API key. If not provided, will look in config file then NEON_API_KEY env var.
            environment: "production" or "trial". If not provided, will look in config file then NEON_ENVIRONMENT env var, defaults to "production".
            api_version: API version to use. If not provided, will look in config file then NEON_API_VERSION env var, defaults to "2.10".
            timeout: Request timeout in seconds. If not provided, will look in config file then NEON_TIMEOUT env var, defaults to 30.0.
            max_retries: Number of retries for failed requests. If not provided, will look in config file then NEON_MAX_RETRIES env var, defaults to 3.
            base_url: Custom base URL. If provided, overrides environment setting. Can also be set in config file or NEON_BASE_URL env var.
            config_path: Path to configuration file. Defaults to ~/.neon/config.json.
        """
        # Load configuration using config loader
        config_loader = ConfigLoader(config_path)
        config = config_loader.get_config(
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
                raise NeonTimeoutError(
                    timeout=self.timeout, details={"original_error": str(e)}
                ) from e
            except httpx.ConnectError as e:
                raise NeonConnectionError(original_error=e, details={"url": url}) from e
            except httpx.HTTPStatusError as e:
                return self._handle_response(e.response)
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
        environment: Optional[Environment] = None,
        api_version: Optional[str] = None,
        timeout: Optional[float] = None,
        max_retries: Optional[int] = None,
        base_url: Optional[str] = None,
        config_path: Optional[Union[str, Path]] = None,
    ) -> None:
        """Initialize the async Neon CRM client.

        Args:
            org_id: Your Neon organization ID. If not provided, will look in config file then NEON_ORG_ID env var.
            api_key: Your API key. If not provided, will look in config file then NEON_API_KEY env var.
            environment: "production" or "trial". If not provided, will look in config file then NEON_ENVIRONMENT env var, defaults to "production".
            api_version: API version to use. If not provided, will look in config file then NEON_API_VERSION env var, defaults to "2.10".
            timeout: Request timeout in seconds. If not provided, will look in config file then NEON_TIMEOUT env var, defaults to 30.0.
            max_retries: Number of retries for failed requests. If not provided, will look in config file then NEON_MAX_RETRIES env var, defaults to 3.
            base_url: Custom base URL. If provided, overrides environment setting. Can also be set in config file or NEON_BASE_URL env var.
            config_path: Path to configuration file. Defaults to ~/.neon/config.json.
        """
        # Load configuration using config loader
        config_loader = ConfigLoader(config_path)
        config = config_loader.get_config(
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
                raise NeonTimeoutError(
                    timeout=self.timeout, details={"original_error": str(e)}
                ) from e
            except httpx.ConnectError as e:
                raise NeonConnectionError(original_error=e, details={"url": url}) from e
            except httpx.HTTPStatusError as e:
                return self._handle_response(e.response)

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
