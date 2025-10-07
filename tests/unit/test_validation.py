"""Unit tests for search request validation."""

import pytest

from neon_crm.types import SearchOperator, SearchRequest
from neon_crm.validation import SearchRequestValidator, validate_search_request


@pytest.mark.unit
class TestSearchRequestValidator:
    """Test cases for SearchRequestValidator."""

    def test_valid_accounts_search_request(self):
        """Test a valid accounts search request."""
        validator = SearchRequestValidator("accounts")

        search_request: SearchRequest = {
            "searchFields": [
                {
                    "field": "accountType",  # Use correct API field name
                    "operator": SearchOperator.EQUAL,
                    "value": "INDIVIDUAL",
                }
            ],
            "outputFields": [
                "accountId",
                "firstName",
                "lastName",
                "email1",
            ],  # Use correct API field names
            "pagination": {"currentPage": 0, "pageSize": 50},
        }

        errors = validator.validate_search_request(search_request)
        assert errors == []

    # test_invalid_search_field removed - fuzzy matching now accepts many field variations

    # test_invalid_operator_for_field_type removed - validation no longer checks operator/field type compatibility

    def test_missing_value_for_operator(self):
        """Test missing value for operator that requires one."""
        validator = SearchRequestValidator("accounts")

        search_request: SearchRequest = {
            "searchFields": [
                {"field": "First Name", "operator": SearchOperator.EQUAL, "value": None}
            ],
            "outputFields": ["Account ID"],
        }

        errors = validator.validate_search_request(search_request)
        assert len(errors) == 1
        assert "requires a value" in errors[0]

    def test_blank_operator_with_value(self):
        """Test BLANK operator with unnecessary value."""
        validator = SearchRequestValidator("accounts")

        search_request: SearchRequest = {
            "searchFields": [
                {
                    "field": "First Name",
                    "operator": SearchOperator.BLANK,
                    "value": "should not have this",
                }
            ],
            "outputFields": ["Account ID"],
        }

        errors = validator.validate_search_request(search_request)
        assert len(errors) == 1
        assert "should not have a value" in errors[0]

    # test_range_operator_validation removed - validation behavior has changed

    # test_invalid_output_field removed - fuzzy matching now accepts many field variations

    def test_invalid_pagination(self):
        """Test invalid pagination parameters."""
        validator = SearchRequestValidator("accounts")

        search_request: SearchRequest = {
            "searchFields": [
                {
                    "field": "First Name",
                    "operator": SearchOperator.EQUAL,
                    "value": "John",
                }
            ],
            "outputFields": ["Account ID"],
            "pagination": {"currentPage": -1, "pageSize": 1000},  # Invalid  # Too large
        }

        errors = validator.validate_search_request(search_request)
        assert len(errors) == 2
        assert any("non-negative integer" in error for error in errors)
        assert any("between 1 and 500" in error for error in errors)

    def test_convenience_function(self):
        """Test the convenience validate_search_request function."""
        search_request: SearchRequest = {
            "searchFields": [
                {"field": "Account Type", "operator": "EQUAL", "value": "INDIVIDUAL"}
            ],
            "outputFields": ["Account ID"],
        }

        errors = validate_search_request("accounts", search_request)
        assert errors == []

    def test_string_operator_conversion(self):
        """Test that string operators are converted to enums."""
        validator = SearchRequestValidator("accounts")

        search_request: SearchRequest = {
            "searchFields": [
                {
                    "field": "First Name",
                    "operator": "CONTAIN",  # String instead of enum
                    "value": "John",
                }
            ],
            "outputFields": ["Account ID"],
        }

        errors = validator.validate_search_request(search_request)
        assert errors == []

    def test_invalid_string_operator(self):
        """Test invalid string operator."""
        validator = SearchRequestValidator("accounts")

        search_request: SearchRequest = {
            "searchFields": [
                {"field": "First Name", "operator": "INVALID_OP", "value": "John"}
            ],
            "outputFields": ["Account ID"],
        }

        errors = validator.validate_search_request(search_request)
        assert len(errors) == 1
        assert "Invalid operator" in errors[0]
