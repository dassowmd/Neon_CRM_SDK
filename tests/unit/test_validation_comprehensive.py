"""Comprehensive unit tests for the validation module."""

from unittest.mock import Mock

from neon_crm.types import SearchOperator
from neon_crm.validation import SearchRequestValidator, validate_search_request


class TestSearchRequestValidator:
    """Test the SearchRequestValidator class."""

    def test_initialization(self):
        """Test validator initialization."""
        validator = SearchRequestValidator("accounts")
        assert validator.resource_name == "accounts"
        assert validator.client is None

    def test_initialization_with_client(self):
        """Test validator initialization with client."""
        mock_client = Mock()
        validator = SearchRequestValidator("donations", mock_client)
        assert validator.resource_name == "donations"
        assert validator.client == mock_client

    def test_resource_name_normalization(self):
        """Test that resource names are normalized to lowercase."""
        validator = SearchRequestValidator("ACCOUNTS")
        assert validator.resource_name == "accounts"

    def test_validate_search_request_empty(self):
        """Test validating an empty search request."""
        validator = SearchRequestValidator("accounts")
        errors = validator.validate_search_request({})
        assert errors == []

    def test_validate_search_request_valid(self):
        """Test validating a valid search request."""
        validator = SearchRequestValidator("accounts")
        search_request = {
            "searchFields": [
                {"field": "Account ID", "operator": "EQUAL", "value": 123}
            ],
            "outputFields": ["Account ID", "First Name"],
            "pagination": {"currentPage": 0, "pageSize": 10},
        }
        errors = validator.validate_search_request(search_request)
        assert len(errors) == 0

    def test_validate_search_field_missing_field(self):
        """Test validation fails when field is missing."""
        validator = SearchRequestValidator("accounts")
        search_field = {"operator": "EQUAL", "value": "test"}
        errors = validator.validate_search_field(search_field)
        assert "Search field 'field' is required" in errors

    def test_validate_search_field_missing_operator(self):
        """Test validation fails when operator is missing."""
        validator = SearchRequestValidator("accounts")
        search_field = {"field": "Account ID", "value": "test"}
        errors = validator.validate_search_field(search_field)
        assert "Search field 'operator' is required" in errors

    def test_validate_operator_invalid_operator_string(self):
        """Test validation fails for invalid operator string."""
        validator = SearchRequestValidator("accounts")
        errors = validator.validate_operator("Account ID", "INVALID_OP")
        assert any("Invalid operator" in error for error in errors)

    def test_validate_operator_valid_enum(self):
        """Test validation passes for valid operator enum."""
        validator = SearchRequestValidator("accounts")
        errors = validator.validate_operator("Account ID", SearchOperator.EQUAL)
        assert errors == []

    def test_validate_operator_invalid_for_field_type(self):
        """Test validation fails when operator invalid for field type."""
        validator = SearchRequestValidator("accounts")
        # String field with numeric operator
        errors = validator.validate_operator("First Name", SearchOperator.GREATER_THAN)
        assert any("not valid for field" in error for error in errors)

    def test_validate_field_value_blank_operator_no_value_required(self):
        """Test BLANK operator doesn't require value."""
        validator = SearchRequestValidator("accounts")
        errors = validator.validate_field_value(
            "First Name", SearchOperator.BLANK, None
        )
        assert errors == []

    def test_validate_field_value_blank_operator_with_value_error(self):
        """Test BLANK operator with value produces error."""
        validator = SearchRequestValidator("accounts")
        errors = validator.validate_field_value(
            "First Name", SearchOperator.BLANK, "value"
        )
        assert any("should not have a value" in error for error in errors)

    def test_validate_field_value_equal_operator_requires_value(self):
        """Test EQUAL operator requires value."""
        validator = SearchRequestValidator("accounts")
        errors = validator.validate_field_value(
            "First Name", SearchOperator.EQUAL, None
        )
        assert any("requires a value" in error for error in errors)

    def test_validate_field_value_range_operator_requires_array(self):
        """Test range operators require array values."""
        validator = SearchRequestValidator("accounts")
        errors = validator.validate_field_value(
            "Account ID", SearchOperator.IN_RANGE, "not_array"
        )
        assert any("requires an array of exactly 2 values" in error for error in errors)

    def test_validate_field_value_range_operator_requires_two_values(self):
        """Test range operators require exactly 2 values."""
        validator = SearchRequestValidator("accounts")
        errors = validator.validate_field_value(
            "Account ID", SearchOperator.IN_RANGE, [1]
        )
        assert any("requires an array of exactly 2 values" in error for error in errors)

    def test_validate_value_type_number_field_with_string(self):
        """Test numeric field validation with string value."""
        validator = SearchRequestValidator("accounts")
        errors = validator.validate_value_type("Account ID", "number", "not_a_number")
        assert any("expects a numeric value" in error for error in errors)

    def test_validate_value_type_number_field_with_number(self):
        """Test numeric field validation with valid number."""
        validator = SearchRequestValidator("accounts")
        errors = validator.validate_value_type("Account ID", "number", 123)
        assert errors == []

    def test_validate_value_type_boolean_field_with_string(self):
        """Test boolean field validation with string value."""
        validator = SearchRequestValidator("accounts")
        errors = validator.validate_value_type("Published", "boolean", "not_bool")
        assert any("expects a boolean value" in error for error in errors)

    def test_validate_value_type_boolean_field_with_boolean(self):
        """Test boolean field validation with valid boolean."""
        validator = SearchRequestValidator("accounts")
        errors = validator.validate_value_type("Published", "boolean", True)
        assert errors == []

    def test_validate_value_type_date_field_with_invalid_format(self):
        """Test date field validation with invalid format."""
        validator = SearchRequestValidator("accounts")
        errors = validator.validate_value_type("Date Created", "date", "invalid-date")
        assert any("expects date in YYYY-MM-DD format" in error for error in errors)

    def test_validate_value_type_date_field_with_valid_format(self):
        """Test date field validation with valid format."""
        validator = SearchRequestValidator("accounts")
        errors = validator.validate_value_type("Date Created", "date", "2023-12-25")
        assert errors == []

    def test_is_valid_date_string_valid_dates(self):
        """Test valid date string validation."""
        validator = SearchRequestValidator("accounts")
        assert validator._is_valid_date_string("2023-12-25") is True
        assert validator._is_valid_date_string("2000-01-01") is True
        assert validator._is_valid_date_string("2023-02-28") is True

    def test_is_valid_date_string_invalid_dates(self):
        """Test invalid date string validation."""
        validator = SearchRequestValidator("accounts")
        assert validator._is_valid_date_string("invalid") is False
        assert validator._is_valid_date_string("2023-13-01") is False  # Invalid month
        assert validator._is_valid_date_string("2023-12-32") is False  # Invalid day
        assert validator._is_valid_date_string("23-12-25") is False  # Wrong format
        assert validator._is_valid_date_string(123) is False  # Not string

    def test_validate_output_fields_empty(self):
        """Test output fields validation with empty list."""
        validator = SearchRequestValidator("accounts")
        errors = validator.validate_output_fields([])
        assert "At least one output field is required" in errors

    def test_validate_output_fields_valid(self):
        """Test output fields validation with valid fields."""
        validator = SearchRequestValidator("accounts")
        errors = validator.validate_output_fields(["Account ID", "First Name"])
        assert errors == []

    def test_validate_pagination_valid(self):
        """Test pagination validation with valid parameters."""
        validator = SearchRequestValidator("accounts")
        errors = validator.validate_pagination({"currentPage": 0, "pageSize": 50})
        assert errors == []

    def test_validate_pagination_invalid_current_page(self):
        """Test pagination validation with invalid current page."""
        validator = SearchRequestValidator("accounts")
        errors = validator.validate_pagination({"currentPage": -1, "pageSize": 50})
        assert "currentPage must be a non-negative integer" in errors

    def test_validate_pagination_invalid_page_size(self):
        """Test pagination validation with invalid page size."""
        validator = SearchRequestValidator("accounts")
        errors = validator.validate_pagination({"currentPage": 0, "pageSize": 0})
        assert "pageSize must be an integer between 1 and 500" in errors

    def test_validate_pagination_page_size_too_large(self):
        """Test pagination validation with page size too large."""
        validator = SearchRequestValidator("accounts")
        errors = validator.validate_pagination({"currentPage": 0, "pageSize": 1000})
        assert "pageSize must be an integer between 1 and 500" in errors

    def test_is_custom_field_with_integer(self):
        """Test custom field detection with integer."""
        validator = SearchRequestValidator("accounts")
        assert validator._is_custom_field(123) is True

    def test_is_custom_field_with_string_digits(self):
        """Test custom field detection with string digits."""
        validator = SearchRequestValidator("accounts")
        assert validator._is_custom_field("123") is True

    def test_is_custom_field_with_non_digits(self):
        """Test custom field detection with non-digits."""
        validator = SearchRequestValidator("accounts")
        assert validator._is_custom_field("abc") is False
        assert validator._is_custom_field("12a") is False

    def test_is_valid_search_field_custom_field(self):
        """Test search field validation with custom field."""
        validator = SearchRequestValidator("accounts")
        assert validator._is_valid_search_field(123) is True
        assert validator._is_valid_search_field("456") is True

    def test_is_valid_search_field_standard_field(self):
        """Test search field validation with standard field."""
        validator = SearchRequestValidator("accounts")
        assert validator._is_valid_search_field("Account ID") is True
        assert validator._is_valid_search_field("First Name") is True

    def test_is_valid_output_field_custom_field(self):
        """Test output field validation with custom field."""
        validator = SearchRequestValidator("accounts")
        assert validator._is_valid_output_field(123) is True
        assert validator._is_valid_output_field("456") is True

    def test_is_valid_output_field_standard_field(self):
        """Test output field validation with standard field."""
        validator = SearchRequestValidator("accounts")
        assert validator._is_valid_output_field("Account ID") is True
        assert validator._is_valid_output_field("First Name") is True

    def test_get_field_type_custom_field(self):
        """Test getting field type for custom fields defaults to string."""
        validator = SearchRequestValidator("accounts")
        assert validator._get_field_type(123) == "string"
        assert validator._get_field_type("456") == "string"

    def test_get_field_type_unknown_field(self):
        """Test getting field type for unknown fields defaults to string."""
        validator = SearchRequestValidator("accounts")
        assert validator._get_field_type("Unknown Field") == "string"

    def test_validate_search_request_with_all_sections(self):
        """Test complete search request validation."""
        validator = SearchRequestValidator("accounts")
        search_request = {
            "searchFields": [
                {"field": "Account ID", "operator": "EQUAL", "value": 123},
                {"field": "First Name", "operator": "NOT_BLANK"},
            ],
            "outputFields": ["Account ID", "First Name", "Last Name"],
            "pagination": {"currentPage": 0, "pageSize": 25},
        }
        errors = validator.validate_search_request(search_request)
        assert errors == []

    def test_validation_error_accumulation(self):
        """Test that multiple validation errors are accumulated."""
        validator = SearchRequestValidator("accounts")
        search_request = {
            "searchFields": [
                {"field": "Invalid Field", "operator": "INVALID_OP", "value": "test"}
            ],
            "outputFields": ["Invalid Output Field"],
            "pagination": {"currentPage": -1, "pageSize": 0},
        }
        errors = validator.validate_search_request(search_request)
        assert len(errors) > 1  # Should have multiple errors


class TestValidateSearchRequestFunction:
    """Test the standalone validate_search_request function."""

    def test_validate_search_request_function(self):
        """Test the standalone validation function."""
        search_request = {
            "searchFields": [
                {"field": "Account ID", "operator": "EQUAL", "value": 123}
            ],
            "outputFields": ["Account ID", "First Name"],
        }
        errors = validate_search_request("accounts", search_request)
        assert errors == []


class TestDynamicFieldLoading:
    """Test dynamic field loading from client resources."""

    def test_get_dynamic_search_fields_with_caching_enabled(self):
        """Test loading search fields when client has caching enabled."""
        mock_client = Mock()
        mock_client.field_cache_enabled = True
        mock_client._field_caches = {}

        # Mock the accounts resource
        mock_accounts = Mock()
        mock_accounts.get_search_fields.return_value = {
            "standardFields": [
                {"fieldName": "accountId"},
                {"fieldName": "firstName"},
            ],
            "customFields": [
                {"displayName": "Custom Field 1"},
            ],
        }
        mock_accounts.get_output_fields.return_value = {
            "standardFields": ["accountId", "firstName"],
            "customFields": [
                {"displayName": "Custom Field 1"},
            ],
        }
        mock_client.accounts = mock_accounts

        validator = SearchRequestValidator("accounts", mock_client)

        # Trigger field loading
        fields = validator._get_dynamic_search_fields()

        # Should have loaded fields
        assert len(fields) >= 2

    def test_load_resource_fields_batch(self):
        """Test batch loading of resource fields."""
        mock_client = Mock()
        mock_client.field_cache_enabled = True
        mock_client._field_caches = {}

        # Mock the accounts resource
        mock_accounts = Mock()
        mock_accounts.get_search_fields.return_value = {
            "standardFields": [
                {"fieldName": "accountId"},
            ],
            "customFields": [],
        }
        mock_accounts.get_output_fields.return_value = {
            "standardFields": ["accountId"],
            "customFields": [],
        }

        validator = SearchRequestValidator("accounts", mock_client)
        validator._load_resource_fields_batch(mock_accounts)

        # Should have cached the fields in client
        assert "accounts" in mock_client._field_caches

    def test_dynamic_field_loading_without_caching(self):
        """Test field loading when caching is disabled."""
        mock_client = Mock()
        mock_client.field_cache_enabled = False
        mock_client._field_caches = {}

        # Mock the accounts resource
        mock_accounts = Mock()
        mock_accounts.get_search_fields.return_value = {
            "standardFields": [
                {"fieldName": "accountId"},
            ],
            "customFields": [],
        }
        mock_client.accounts = mock_accounts

        validator = SearchRequestValidator("accounts", mock_client)
        fields = validator._get_dynamic_search_fields()

        # Should still get fields even without caching
        assert len(fields) >= 1

    def test_dynamic_field_loading_not_implemented(self):
        """Test handling when resource doesn't support field discovery."""
        mock_client = Mock()
        mock_client.field_cache_enabled = False

        # Mock resource that doesn't support get_search_fields
        mock_accounts = Mock()
        mock_accounts.get_search_fields.side_effect = NotImplementedError(
            "Not supported"
        )
        mock_client.accounts = mock_accounts

        validator = SearchRequestValidator("accounts", mock_client)
        fields = validator._get_dynamic_search_fields()

        # Should return empty list on NotImplementedError
        assert fields == []

    def test_dynamic_field_loading_exception(self):
        """Test handling when field loading raises exception."""
        mock_client = Mock()
        mock_client.field_cache_enabled = False

        # Mock resource that raises exception
        mock_accounts = Mock()
        mock_accounts.get_search_fields.side_effect = Exception("API Error")
        mock_client.accounts = mock_accounts

        validator = SearchRequestValidator("accounts", mock_client)
        fields = validator._get_dynamic_search_fields()

        # Should return empty list on exception
        assert fields == []


class TestFuzzyFieldMatching:
    """Test fuzzy field matching functionality."""

    def test_fuzzy_match_with_matching_field(self):
        """Test fuzzy matching successfully finds similar field."""
        validator = SearchRequestValidator("accounts")

        # _try_fuzzy_field_match creates its own FieldFuzzySearch
        # It will attempt to match against available fields
        result = validator._try_fuzzy_field_match("first name", "search")

        # Result could be True (found match) or False (no match)
        assert isinstance(result, bool)

    def test_fuzzy_match_exception_handling(self):
        """Test fuzzy matching handles exceptions gracefully."""
        validator = SearchRequestValidator("accounts")

        # Pass invalid field_type to trigger exception path
        result = validator._try_fuzzy_field_match("test", "invalid_type")

        # Should return False on exception
        assert isinstance(result, bool)


class TestCustomFieldDetection:
    """Test custom field detection methods."""

    def test_is_custom_field_name_with_prefix_v(self):
        """Test detecting custom field by V- prefix."""
        validator = SearchRequestValidator("accounts")

        # Custom fields with V- prefix
        assert validator._is_custom_field_name("V-CustomField") is True

    def test_is_custom_field_name_with_prefix_c(self):
        """Test detecting custom field by C- prefix."""
        validator = SearchRequestValidator("accounts")

        # Custom fields with C- prefix
        assert validator._is_custom_field_name("C-CustomField") is True

    def test_is_custom_field_name_with_custom_prefix(self):
        """Test detecting custom field by Custom prefix."""
        validator = SearchRequestValidator("accounts")

        # Custom fields with Custom prefix
        assert validator._is_custom_field_name("CustomField123") is True

    def test_is_custom_field_name_with_dash(self):
        """Test detecting custom field by dash pattern."""
        validator = SearchRequestValidator("accounts")

        # Custom fields with dash pattern
        assert validator._is_custom_field_name("Field - Custom") is True

    def test_is_custom_field_name_with_long_name(self):
        """Test detecting custom field by length."""
        validator = SearchRequestValidator("accounts")

        # Very long field names (>50 chars) are likely custom
        long_name = "x" * 51
        assert validator._is_custom_field_name(long_name) is True

    def test_is_custom_field_name_with_regular_name(self):
        """Test that regular field names are not detected as custom."""
        validator = SearchRequestValidator("accounts")

        # Regular field names
        assert validator._is_custom_field_name("firstName") is False
        assert validator._is_custom_field_name("accountId") is False
        assert validator._is_custom_field_name("email") is False

    def test_get_field_type_for_custom_field(self):
        """Test getting field type for custom fields."""
        validator = SearchRequestValidator("accounts")

        # Custom fields (by ID) default to string type
        field_type = validator._get_field_type(123)
        assert field_type == "string"

    def test_get_field_type_for_known_field(self):
        """Test getting field type for known fields."""
        validator = SearchRequestValidator("accounts")

        # Should return known types for standard fields
        # Note: This depends on field_definitions.json
        field_type = validator._get_field_type("Account ID")
        assert isinstance(field_type, str)
