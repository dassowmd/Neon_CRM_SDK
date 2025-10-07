"""Unit tests for exception classes."""

import pytest

from neon_crm.exceptions import (
    NeonAPIError,
    NeonAuthenticationError,
    NeonBadRequestError,
    NeonConflictError,
    NeonConnectionError,
    NeonError,
    NeonForbiddenError,
    NeonNotFoundError,
    NeonRateLimitError,
    NeonServerError,
    NeonTimeoutError,
    NeonUnsupportedMediaTypeError,
    NeonUnprocessableEntityError,
    NeonValidationError,
)


class TestNeonError:
    """Test the base NeonError exception."""

    def test_basic_error(self):
        """Test creating a basic error."""
        error = NeonError("Test error")
        assert str(error) == "Test error"
        assert error.message == "Test error"
        assert error.details == {}

    def test_error_with_details(self):
        """Test creating an error with details."""
        details = {"field": "value", "code": 123}
        error = NeonError("Test error", details=details)
        assert error.message == "Test error"
        assert error.details == details


class TestNeonAPIError:
    """Test the NeonAPIError exception."""

    def test_api_error(self):
        """Test creating an API error."""
        error = NeonAPIError("API failed", status_code=500)
        assert str(error) == "API failed"
        assert error.message == "API failed"
        assert error.status_code == 500
        assert error.response_data == {}
        assert error.details == {}

    def test_api_error_with_response_data(self):
        """Test creating an API error with response data."""
        response_data = {"error": "Server error", "code": "INTERNAL_ERROR"}
        details = {"request_id": "12345"}
        error = NeonAPIError(
            "API failed", status_code=500, response_data=response_data, details=details
        )
        assert error.status_code == 500
        assert error.response_data == response_data
        assert error.details == details


class TestNeonBadRequestError:
    """Test the NeonBadRequestError exception."""

    def test_default_message(self):
        """Test bad request error with default message."""
        error = NeonBadRequestError()
        assert error.message == "Bad Request."
        assert error.status_code == 400

    def test_custom_message(self):
        """Test bad request error with custom message."""
        error = NeonBadRequestError("Invalid input")
        assert error.message == "Invalid input"
        assert error.status_code == 400

    def test_with_response_data(self):
        """Test bad request error with response data."""
        response_data = {"field_errors": {"email": "Invalid email"}}
        error = NeonBadRequestError(response_data=response_data)
        assert error.response_data == response_data


class TestNeonAuthenticationError:
    """Test the NeonAuthenticationError exception."""

    def test_default_message(self):
        """Test authentication error with default message."""
        error = NeonAuthenticationError()
        assert (
            "Authentication failed. Please check your organization ID and API key."
            in error.message
        )
        assert error.status_code == 401

    def test_custom_message(self):
        """Test authentication error with custom message."""
        error = NeonAuthenticationError("Invalid API key")
        assert error.message == "Invalid API key"
        assert error.status_code == 401


class TestNeonForbiddenError:
    """Test the NeonForbiddenError exception."""

    def test_default_message(self):
        """Test forbidden error with default message."""
        error = NeonForbiddenError()
        assert "Access forbidden" in error.message
        assert error.status_code == 403

    def test_custom_message(self):
        """Test forbidden error with custom message."""
        error = NeonForbiddenError("No permission to delete")
        assert error.message == "No permission to delete"
        assert error.status_code == 403


class TestNeonNotFoundError:
    """Test the NeonNotFoundError exception."""

    def test_default_message(self):
        """Test not found error with default message."""
        error = NeonNotFoundError()
        assert error.message == "Resource not found."
        assert error.status_code == 404

    def test_custom_message(self):
        """Test not found error with custom message."""
        error = NeonNotFoundError("Account #123 not found")
        assert error.message == "Account #123 not found"
        assert error.status_code == 404


class TestNeonRateLimitError:
    """Test the NeonRateLimitError exception."""

    def test_default_message(self):
        """Test rate limit error with default message."""
        error = NeonRateLimitError()
        assert "Rate limit exceeded" in error.message
        assert error.status_code == 429
        assert error.retry_after is None

    def test_with_retry_after(self):
        """Test rate limit error with retry_after value."""
        error = NeonRateLimitError(retry_after=60)
        assert error.retry_after == 60
        assert error.status_code == 429


class TestNeonConflictError:
    """Test the NeonConflictError exception."""

    def test_default_message(self):
        """Test conflict error with default message."""
        error = NeonConflictError()
        assert "Conflict" in error.message
        assert error.status_code == 409

    def test_custom_message(self):
        """Test conflict error with custom message."""
        error = NeonConflictError("Duplicate email address")
        assert error.message == "Duplicate email address"
        assert error.status_code == 409


class TestNeonUnsupportedMediaTypeError:
    """Test the NeonUnsupportedMediaTypeError exception."""

    def test_default_message(self):
        """Test unsupported media type error with default message."""
        error = NeonUnsupportedMediaTypeError()
        assert "Unsupported Media Type" in error.message
        assert error.status_code == 415

    def test_custom_message(self):
        """Test unsupported media type error with custom message."""
        error = NeonUnsupportedMediaTypeError("JSON required")
        assert error.message == "JSON required"
        assert error.status_code == 415


class TestNeonUnprocessableEntityError:
    """Test the NeonUnprocessableEntityError exception."""

    def test_default_message(self):
        """Test unprocessable entity error with default message."""
        error = NeonUnprocessableEntityError()
        assert "Unprocessable Entity" in error.message
        assert error.status_code == 422

    def test_custom_message(self):
        """Test unprocessable entity error with custom message."""
        error = NeonUnprocessableEntityError("Invalid date format")
        assert error.message == "Invalid date format"
        assert error.status_code == 422


class TestNeonServerError:
    """Test the NeonServerError exception."""

    def test_default_message_and_status(self):
        """Test server error with default message and status."""
        error = NeonServerError()
        assert "Internal Server Error" in error.message
        assert error.status_code == 500

    def test_custom_status_code(self):
        """Test server error with custom status code."""
        error = NeonServerError(message="Service unavailable", status_code=503)
        assert error.message == "Service unavailable"
        assert error.status_code == 503


class TestNeonValidationError:
    """Test the NeonValidationError exception."""

    def test_basic_validation_error(self):
        """Test creating a validation error."""
        error = NeonValidationError("Validation failed")
        assert error.message == "Validation failed"
        assert error.validation_errors == {}

    def test_with_validation_errors(self):
        """Test validation error with validation errors dict."""
        validation_errors = {
            "email": "Invalid email format",
            "age": "Must be positive",
        }
        error = NeonValidationError("Validation failed", validation_errors)
        assert error.validation_errors == validation_errors


class TestNeonTimeoutError:
    """Test the NeonTimeoutError exception."""

    def test_default_message(self):
        """Test timeout error with default message."""
        error = NeonTimeoutError()
        assert error.message == "Request timed out."
        assert error.timeout is None

    def test_with_timeout_value(self):
        """Test timeout error with timeout value."""
        error = NeonTimeoutError("Request timed out", timeout=30.0)
        assert error.message == "Request timed out"
        assert error.timeout == 30.0


class TestNeonConnectionError:
    """Test the NeonConnectionError exception."""

    def test_default_message(self):
        """Test connection error with default message."""
        error = NeonConnectionError()
        assert error.message == "Connection error occurred."
        assert error.original_error is None

    def test_with_original_error(self):
        """Test connection error with original error."""
        original = ConnectionError("Network unreachable")
        error = NeonConnectionError("Failed to connect", original_error=original)
        assert error.message == "Failed to connect"
        assert error.original_error == original
