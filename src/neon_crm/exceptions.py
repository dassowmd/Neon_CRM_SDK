"""Exception classes for the Neon CRM SDK."""

from typing import Any, Dict, Optional


class NeonError(Exception):
    """Base exception for all Neon CRM SDK errors."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}


class NeonAPIError(NeonError):
    """Exception raised when the API returns an error response."""

    def __init__(
        self,
        message: str,
        status_code: int,
        response_data: Optional[Dict[str, Any]] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message, details)
        self.status_code = status_code
        self.response_data = response_data or {}


class NeonBadRequestError(NeonAPIError):
    """Exception raised when bad request (400)."""

    def __init__(
        self,
        message: str = "Bad Request.",
        response_data: Optional[Dict[str, Any]] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message, 400, response_data, details)


class NeonAuthenticationError(NeonAPIError):
    """Exception raised when authentication fails (401)."""

    def __init__(
        self,
        message: str = "Authentication failed. Please check your organization ID and API key.",
        response_data: Optional[Dict[str, Any]] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message, 401, response_data, details)


class NeonForbiddenError(NeonAPIError):
    """Exception raised when access is forbidden (403)."""

    def __init__(
        self,
        message: str = "Access forbidden. You don't have permission to access this resource.",
        response_data: Optional[Dict[str, Any]] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message, 403, response_data, details)


class NeonNotFoundError(NeonAPIError):
    """Exception raised when a resource is not found (404)."""

    def __init__(
        self,
        message: str = "Resource not found.",
        response_data: Optional[Dict[str, Any]] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message, 404, response_data, details)


class NeonRateLimitError(NeonAPIError):
    """Exception raised when rate limit is exceeded (429)."""

    def __init__(
        self,
        message: str = "Rate limit exceeded. Please retry after some time.",
        retry_after: Optional[int] = None,
        response_data: Optional[Dict[str, Any]] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message, 429, response_data, details)
        self.retry_after = retry_after


class NeonConflictError(NeonAPIError):
    """Exception raised when there's a conflict (409)."""

    def __init__(
        self,
        message: str = "Conflict. The request conflicts with the current state.",
        response_data: Optional[Dict[str, Any]] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message, 409, response_data, details)


class NeonUnprocessableEntityError(NeonAPIError):
    """Exception raised when request is unprocessable (422)."""

    def __init__(
        self,
        message: str = "Unprocessable Entity. The request was well-formed but contains semantic errors.",
        response_data: Optional[Dict[str, Any]] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message, 422, response_data, details)


class NeonServerError(NeonAPIError):
    """Exception raised for server errors (500-599)."""

    def __init__(
        self,
        message: str = "Internal Server Error. Please try again later.",
        status_code: int = 500,
        response_data: Optional[Dict[str, Any]] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message, status_code, response_data, details)


class NeonValidationError(NeonError):
    """Exception raised when request validation fails."""

    def __init__(
        self,
        message: str,
        validation_errors: Optional[Dict[str, Any]] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message, details)
        self.validation_errors = validation_errors or {}


class NeonTimeoutError(NeonError):
    """Exception raised when a request times out."""

    def __init__(
        self,
        message: str = "Request timed out.",
        timeout: Optional[float] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message, details)
        self.timeout = timeout


class NeonConnectionError(NeonError):
    """Exception raised when there's a connection error."""

    def __init__(
        self,
        message: str = "Connection error occurred.",
        original_error: Optional[Exception] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message, details)
        self.original_error = original_error
