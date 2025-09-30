"""Unit tests for field mapping functionality."""

import pytest

from neon_crm.field_mapping import FieldNameMapper
from neon_crm.types import SearchRequest


@pytest.mark.unit
class TestFieldNameMapper:
    """Test cases for FieldNameMapper."""

    def test_display_to_api_mapping(self):
        """Test conversion from display names to API names."""
        test_cases = [
            ("First Name", "firstName"),
            ("Last Name", "lastName"),
            ("Account ID", "accountId"),
            ("Email 1", "email1"),
            ("Donation Amount", "amount"),
            ("Campaign Name", "name"),
            ("State/Province", "stateProvince"),
        ]

        for display_name, expected_api_name in test_cases:
            actual_api_name = FieldNameMapper.to_api_field_name(display_name)
            assert (
                actual_api_name == expected_api_name
            ), f"Expected '{display_name}' to map to '{expected_api_name}', got '{actual_api_name}'"

    def test_api_to_display_mapping(self):
        """Test conversion from API names to display names."""
        test_cases = [
            ("firstName", "First Name"),
            ("lastName", "Last Name"),
            ("accountId", "Account ID"),
            ("email1", "Email 1"),
            (
                "amount",
                "Donation Amount",
            ),  # Note: This should map back to preferred display name
        ]

        for api_name, expected_display_name in test_cases:
            actual_display_name = FieldNameMapper.to_display_field_name(api_name)
            assert (
                actual_display_name == expected_display_name
            ), f"Expected '{api_name}' to map to '{expected_display_name}', got '{actual_display_name}'"

    def test_convert_search_fields(self):
        """Test conversion of search fields."""
        search_fields = [
            {"field": "First Name", "operator": "CONTAIN", "value": "John"},
            {"field": "Account Type", "operator": "EQUAL", "value": "Individual"},
            {"field": "Donation Amount", "operator": "GREATER_THAN", "value": "100"},
        ]

        converted = FieldNameMapper.convert_search_fields(search_fields)

        expected = [
            {"field": "firstName", "operator": "CONTAIN", "value": "John"},
            {"field": "accountType", "operator": "EQUAL", "value": "Individual"},
            {"field": "amount", "operator": "GREATER_THAN", "value": "100"},
        ]

        assert converted == expected

    def test_convert_output_fields(self):
        """Test conversion of output fields."""
        output_fields = [
            "Account ID",
            "First Name",
            "Last Name",
            "Email 1",
            "Company Name",
        ]

        converted = FieldNameMapper.convert_output_fields(output_fields)

        expected = ["accountId", "firstName", "lastName", "email1", "companyName"]

        assert converted == expected

    def test_convert_search_request(self):
        """Test conversion of complete search request."""
        search_request: SearchRequest = {
            "searchFields": [
                {"field": "First Name", "operator": "CONTAIN", "value": "test"},
                {"field": "Account Type", "operator": "EQUAL", "value": "Individual"},
            ],
            "outputFields": ["Account ID", "First Name", "Last Name", "Email 1"],
            "pagination": {"currentPage": 0, "pageSize": 50},
        }

        converted = FieldNameMapper.convert_search_request(search_request)

        expected: SearchRequest = {
            "searchFields": [
                {"field": "firstName", "operator": "CONTAIN", "value": "test"},
                {"field": "accountType", "operator": "EQUAL", "value": "Individual"},
            ],
            "outputFields": ["accountId", "firstName", "lastName", "email1"],
            "pagination": {"currentPage": 0, "pageSize": 50},
        }

        assert converted == expected

    def test_already_api_format_unchanged(self):
        """Test that fields already in API format are unchanged."""
        api_fields = ["firstName", "lastName", "accountId", "email1"]

        for field in api_fields:
            converted = FieldNameMapper.to_api_field_name(field)
            assert converted == field, f"API field '{field}' should remain unchanged"

    def test_unknown_field_passthrough(self):
        """Test that unknown fields are passed through unchanged."""
        unknown_fields = ["unknownField", "customField123", "some_custom_field"]

        for field in unknown_fields:
            converted = FieldNameMapper.to_api_field_name(field)
            assert (
                converted == field
            ), f"Unknown field '{field}' should pass through unchanged"

    def test_get_suggested_fields(self):
        """Test field suggestion functionality."""
        available_fields = ["accountId", "firstName", "lastName", "email1", "phone1"]

        test_cases = [
            ("First Name", ["firstName"]),
            ("Account ID", ["accountId"]),
            ("Email", ["email1"]),
            ("phone", ["phone1"]),
        ]

        for invalid_field, expected_suggestions in test_cases:
            suggestions = FieldNameMapper.get_suggested_fields(
                invalid_field, available_fields
            )

            # Check that expected suggestions are present
            for expected in expected_suggestions:
                assert (
                    expected in suggestions
                ), f"Expected '{expected}' in suggestions for '{invalid_field}', got {suggestions}"

    def test_is_valid_field_format(self):
        """Test field format validation."""
        valid_api_fields = [
            "firstName",
            "lastName",
            "accountId",
            "email1",
            "dateCreated",
        ]
        invalid_fields = ["First Name", "Account ID", "Email 1", "Date Created"]

        for field in valid_api_fields:
            assert FieldNameMapper.is_valid_field_format(
                field
            ), f"'{field}' should be recognized as valid API format"

        for field in invalid_fields:
            assert not FieldNameMapper.is_valid_field_format(
                field
            ), f"'{field}' should be recognized as invalid API format"

    def test_mixed_format_handling(self):
        """Test handling of mixed format in search requests."""
        mixed_request: SearchRequest = {
            "searchFields": [
                {
                    "field": "First Name",
                    "operator": "EQUAL",
                    "value": "John",
                },  # Display format
                {
                    "field": "lastName",
                    "operator": "EQUAL",
                    "value": "Doe",
                },  # API format
            ],
            "outputFields": [
                "Account ID",  # Display format
                "firstName",  # API format
                "Last Name",  # Display format
            ],
        }

        converted = FieldNameMapper.convert_search_request(mixed_request)

        # All should be converted to API format
        assert converted["searchFields"][0]["field"] == "firstName"
        assert converted["searchFields"][1]["field"] == "lastName"
        assert converted["outputFields"] == ["accountId", "firstName", "lastName"]

    def test_campaign_field_mapping(self):
        """Test campaign-specific field mappings."""
        campaign_test_cases = [
            ("Campaign ID", "id"),
            ("Campaign Name", "name"),  # Campaign Name maps to "name"
            ("Campaign Code", "code"),
            ("Campaign Goal", "goal"),
            ("Campaign Start Date", "startDate"),
            ("Campaign End Date", "endDate"),
            ("Campaign Status", "status"),
            ("Campaign Type", "type"),
        ]

        for display_name, expected_api_name in campaign_test_cases:
            actual_api_name = FieldNameMapper.to_api_field_name(display_name)
            assert (
                actual_api_name == expected_api_name
            ), f"Campaign field '{display_name}' should map to '{expected_api_name}', got '{actual_api_name}'"

    def test_donation_field_mapping(self):
        """Test donation-specific field mappings."""
        donation_test_cases = [
            ("Donation ID", "id"),
            ("Donation Amount", "amount"),
            ("Donation Date", "date"),
            ("Payment Method", "paymentMethod"),
            ("Tender Type", "paymentMethod"),  # Alternative name
            ("Anonymous Type", "anonymousType"),
        ]

        for display_name, expected_api_name in donation_test_cases:
            actual_api_name = FieldNameMapper.to_api_field_name(display_name)
            assert (
                actual_api_name == expected_api_name
            ), f"Donation field '{display_name}' should map to '{expected_api_name}', got '{actual_api_name}'"

    def test_event_field_mapping(self):
        """Test event-specific field mappings."""
        event_test_cases = [
            ("Event ID", "id"),
            ("Event Name", "name"),
            ("Start Date", "startDate"),
            ("End Date", "endDate"),
            ("Maximum Attendees", "maximumAttendees"),
            ("Current Attendees", "currentAttendees"),
            ("Published", "publishEvent"),
        ]

        for display_name, expected_api_name in event_test_cases:
            actual_api_name = FieldNameMapper.to_api_field_name(display_name)
            assert (
                actual_api_name == expected_api_name
            ), f"Event field '{display_name}' should map to '{expected_api_name}', got '{actual_api_name}'"


@pytest.mark.unit
class TestFieldMappingIntegration:
    """Integration tests for field mapping with validation."""

    def test_field_mapping_improves_validation_errors(self):
        """Test that field mapping provides better validation error messages."""
        # This would require creating a mock client/validator
        # For now, we test the structure that would be used

        available_fields = ["accountId", "firstName", "lastName", "email1"]
        invalid_field = "First Name"

        suggestions = FieldNameMapper.get_suggested_fields(
            invalid_field, available_fields
        )

        # Simulate the improved error message format
        error_msg = f"Field '{invalid_field}' is not valid for resource 'accounts'. Valid fields: {sorted(available_fields)}"
        if suggestions:
            error_msg += f". Did you mean: {', '.join(suggestions[:3])}?"

        assert "Did you mean: firstName?" in error_msg
        assert "firstName" in suggestions

    def test_backwards_compatibility_maintained(self):
        """Test that old field names still work through mapping."""
        # Test that legacy field names get converted properly
        legacy_fields = ["First Name", "Last Name", "Account ID", "Email 1"]

        for legacy_field in legacy_fields:
            api_field = FieldNameMapper.to_api_field_name(legacy_field)
            # Should convert to a different (API) format
            assert api_field != legacy_field
            # Should be in camelCase format
            assert FieldNameMapper.is_valid_field_format(api_field)
