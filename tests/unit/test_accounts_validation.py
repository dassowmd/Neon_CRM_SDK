"""Tests for accounts resource validation."""

import pytest

from neon_crm.client import NeonClient
from neon_crm.types import UserType


class TestAccountsValidation:
    """Test validation in AccountsResource."""

    def test_list_requires_user_type(self):
        """Test that list() requires user_type parameter."""
        client = NeonClient(org_id="test", api_key="test")

        with pytest.raises(ValueError, match="user_type is required"):
            # This should raise an error before making any HTTP request
            list(client.accounts.list())

    def test_list_validates_user_type_values(self):
        """Test that list() validates user_type parameter values."""
        client = NeonClient(org_id="test", api_key="test")

        # Test invalid user_type
        with pytest.raises(ValueError, match="Invalid user_type 'INVALID'"):
            list(client.accounts.list(user_type="INVALID"))

        # Test case sensitivity
        with pytest.raises(ValueError, match="Invalid user_type 'individual'"):
            list(client.accounts.list(user_type="individual"))

        with pytest.raises(ValueError, match="Invalid user_type 'company'"):
            list(client.accounts.list(user_type="company"))

    def test_list_accepts_valid_user_types(self):
        """Test that list() accepts valid user_type values."""
        client = NeonClient(org_id="test", api_key="test")

        # These should not raise validation errors
        # (They'll fail later when making HTTP requests, but that's expected)
        try:
            list(client.accounts.list(user_type=UserType.INDIVIDUAL))
        except Exception as e:
            # Should not be a ValueError about user_type
            assert "user_type" not in str(e)

        try:
            list(client.accounts.list(user_type=UserType.COMPANY))
        except Exception as e:
            # Should not be a ValueError about user_type
            assert "user_type" not in str(e)

    def test_validation_error_message_helpful(self):
        """Test that validation error messages are helpful."""
        client = NeonClient(org_id="test", api_key="test")

        # Test missing user_type
        with pytest.raises(ValueError) as exc_info:
            list(client.accounts.list())

        error_msg = str(exc_info.value)
        assert "user_type is required" in error_msg
        assert "INDIVIDUAL" in error_msg
        assert "COMPANY" in error_msg

    def test_validation_error_message_for_invalid_value(self):
        """Test error message for invalid user_type values."""
        client = NeonClient(org_id="test", api_key="test")

        with pytest.raises(ValueError) as exc_info:
            list(client.accounts.list(user_type="WRONG"))

        error_msg = str(exc_info.value)
        assert "Invalid user_type 'WRONG'" in error_msg
        assert "INDIVIDUAL" in error_msg
        assert "COMPANY" in error_msg

    def test_validation_happens_before_http_request(self):
        """Test that validation happens before making HTTP request."""
        # This test ensures validation is client-side, not server-side
        client = NeonClient(org_id="invalid", api_key="invalid")

        # Even with invalid credentials, validation should catch the error first
        with pytest.raises(ValueError, match="user_type is required"):
            list(client.accounts.list())

        # Should not see authentication errors or connection errors
        # because validation fails first

    def test_other_parameters_still_work(self):
        """Test that other filtering parameters still work with validation."""
        client = NeonClient(org_id="test", api_key="test")

        # These should pass validation but fail on HTTP request
        try:
            list(
                client.accounts.list(
                    user_type=UserType.INDIVIDUAL,
                    email="test@example.com",
                    first_name="John",
                    last_name="Doe",
                    page_size=10,
                )
            )
        except Exception as e:
            # Should not be a ValueError about user_type
            assert "user_type" not in str(e)
            # Should not be validation error about other params
            assert "email" not in str(e)
            assert "first_name" not in str(e)
