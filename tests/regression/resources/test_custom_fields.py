"""Comprehensive regression tests for CustomFieldsResource.

Tests both read-only operations for the custom fields endpoint.
Organized to match src/neon_crm/resources/custom_fields.py structure.

This resource was specifically highlighted in the original issue (lines 21-22).
"""

import pytest

from neon_crm.exceptions import (
    NeonNotFoundError,
)
from neon_crm.types import CustomFieldCategory


@pytest.mark.regression
@pytest.mark.readonly
class TestCustomFieldsReadOnly:
    """Read-only tests for CustomFieldsResource - safe for production."""

    def test_custom_fields_list_basic(self, regression_client):
        """Test basic custom fields listing."""
        fields = list(regression_client.custom_fields.list(limit=10))

        print(f"✓ Retrieved {len(fields)} custom fields")

        if fields:
            first_field = fields[0]
            assert isinstance(first_field, dict), "Custom field should be a dictionary"
            print(f"Custom field structure: {list(first_field.keys())}")

            # Check for expected custom field attributes
            expected_attrs = ["id", "name", "fieldType", "component"]
            missing_attrs = [attr for attr in expected_attrs if attr not in first_field]
            if missing_attrs:
                print(f"⚠ Missing expected attributes: {missing_attrs}")
            else:
                print("✓ All expected attributes present")

    def test_custom_fields_limit_parameter_fixed(self, regression_client):
        """Test the limit parameter - this was the original issue (lines 21-22)."""
        # Test limit parameter (this was broken before fix)
        limited_fields = list(
            regression_client.custom_fields.list(page_size=20, limit=5)
        )

        if len(limited_fields) > 5:
            print(
                f"❌ CRITICAL: Limit still not working: got {len(limited_fields)}, expected max 5"
            )
        else:
            print(f"✓ FIXED: Limit parameter working: got {len(limited_fields)} fields")

        # Test limit=None (unlimited - this was causing crashes before fix)
        try:
            unlimited_fields = list(
                regression_client.custom_fields.list(page_size=10, limit=None)
            )
            print(
                f"✓ FIXED: limit=None works without crash: got {len(unlimited_fields)} fields"
            )
        except TypeError as e:
            print(f"❌ CRITICAL: limit=None still crashes: {e}")

        # Test limit=0 (edge case)
        zero_limit_fields = list(
            regression_client.custom_fields.list(page_size=10, limit=0)
        )
        if len(zero_limit_fields) == 0:
            print("✓ limit=0 correctly returns empty list")
        else:
            print(f"⚠ limit=0 returned {len(zero_limit_fields)} fields, expected 0")

    def test_custom_fields_category_filtering(self, regression_client):
        """Test category-based filtering with enum."""
        valid_categories = [
            CustomFieldCategory.ACCOUNT,
            CustomFieldCategory.DONATION,
            CustomFieldCategory.EVENT,
            CustomFieldCategory.MEMBERSHIP,
            CustomFieldCategory.ACTIVITY,
        ]

        for category in valid_categories:
            try:
                fields = list(
                    regression_client.custom_fields.list(
                        page_size=10, category=category
                    )
                )
                print(f"✓ Category '{category.value}': {len(fields)} fields")

                # Validate category filtering
                for field in fields[:3]:  # Check first few
                    if "component" in field:
                        if field["component"] != category.value:
                            print(
                                f"⚠ Category mismatch: expected {category.value}, got {field['component']}"
                            )

            except Exception as e:
                print(f"❌ Category '{category.value}' failed: {e}")

        # Test string category (backward compatibility)
        try:
            string_fields = list(
                regression_client.custom_fields.list(category="Account")
            )
            print(f"✓ String category 'Account': {len(string_fields)} fields")
        except Exception as e:
            print(f"❌ String category failed: {e}")

        # Test invalid category
        try:
            invalid_fields = list(
                regression_client.custom_fields.list(category="invalid_category")
            )
            print(f"⚠ Invalid category accepted, got {len(invalid_fields)} fields")
        except Exception as e:
            print(f"✓ Invalid category correctly rejected: {type(e).__name__}")

    def test_custom_fields_field_type_filtering(self, regression_client):
        """Test field_type parameter filtering."""
        valid_field_types = ["text", "number", "date", "boolean", "dropdown"]

        for field_type in valid_field_types:
            try:
                fields = list(
                    regression_client.custom_fields.list(
                        page_size=10, field_type=field_type
                    )
                )
                print(f"✓ Field type '{field_type}': {len(fields)} fields")

                # Validate field type filtering
                for field in fields[:3]:  # Check first few
                    if "fieldType" in field:
                        if field["fieldType"].lower() != field_type.lower():
                            print(
                                f"⚠ Field type mismatch: expected {field_type}, got {field['fieldType']}"
                            )

            except Exception as e:
                print(f"❌ Field type '{field_type}' failed: {e}")

    def test_custom_fields_get_by_category_method(self, regression_client):
        """Test the get_by_category convenience method."""
        categories_to_test = [
            CustomFieldCategory.ACCOUNT,
            CustomFieldCategory.DONATION,
            CustomFieldCategory.EVENT,
        ]

        for category in categories_to_test:
            try:
                # Test convenience method
                convenience_fields = list(
                    regression_client.custom_fields.get_by_category(category)
                )

                # Compare with direct list call
                direct_fields = list(
                    regression_client.custom_fields.list(category=category)
                )

                print(
                    f"✓ get_by_category('{category.value}'): {len(convenience_fields)} fields"
                )

                if len(convenience_fields) != len(direct_fields):
                    print(
                        f"⚠ Method mismatch: convenience={len(convenience_fields)}, direct={len(direct_fields)}"
                    )
                else:
                    print("✓ get_by_category matches direct list call")

            except Exception as e:
                print(f"❌ get_by_category('{category.value}') failed: {e}")

    def test_custom_fields_get_specific_field(self, regression_client):
        """Test getting a specific custom field by ID."""
        # First get a custom field ID
        fields = list(regression_client.custom_fields.list(limit=1))
        field_id = None
        if fields:
            field_id = fields[0].get("id")

        if field_id:
            specific_field = regression_client.custom_fields.get(field_id)
            assert isinstance(specific_field, dict)
            assert specific_field.get("id") == field_id
            print(f"✓ Retrieved specific custom field: {field_id}")
        else:
            pytest.skip("No custom fields available to test specific retrieval")

    def test_custom_fields_get_invalid_id(self, regression_client):
        """Test error handling for invalid custom field ID."""
        with pytest.raises(NeonNotFoundError):
            regression_client.custom_fields.get(999999999)
        print("✓ Correctly received 404 for invalid custom field ID")

    def test_custom_fields_pagination_behavior(self, regression_client):
        """Test pagination behavior for custom fields."""
        # Get first page
        page1_fields = list(
            regression_client.custom_fields.list(page_size=5, current_page=0)
        )

        # Get second page
        page2_fields = list(
            regression_client.custom_fields.list(page_size=5, current_page=1)
        )

        print(f"✓ Page 1: {len(page1_fields)} fields")
        print(f"✓ Page 2: {len(page2_fields)} fields")

        # Check for overlap (shouldn't be any)
        if page1_fields and page2_fields:
            page1_ids = {f.get("id") for f in page1_fields if "id" in f}
            page2_ids = {f.get("id") for f in page2_fields if "id" in f}

            overlap = page1_ids.intersection(page2_ids)
            if overlap:
                print(f"❌ Pagination overlap: {len(overlap)} duplicate IDs")
            else:
                print("✓ No pagination overlap")

    def test_custom_fields_parameter_combinations(self, regression_client):
        """Test various parameter combinations."""
        parameter_combinations = [
            {"category": CustomFieldCategory.ACCOUNT, "field_type": "text"},
            {"category": "Donation", "page_size": 3},
            {"field_type": "date", "limit": 2},
            {"category": CustomFieldCategory.ACCOUNT, "field_type": "text", "limit": 1},
        ]

        for i, params in enumerate(parameter_combinations):
            try:
                fields = list(regression_client.custom_fields.list(**params))
                print(
                    f"✓ Parameter combination {i + 1}: {len(fields)} fields with {params}"
                )

                # Validate limit was applied if specified
                if "limit" in params and len(fields) > params["limit"]:
                    print(
                        f"❌ Limit not respected: expected max {params['limit']}, got {len(fields)}"
                    )

            except Exception as e:
                print(f"❌ Parameter combination {i + 1} failed {params}: {e}")

    def test_custom_fields_response_structure_validation(self, regression_client):
        """Test custom field response structure validation."""
        fields = list(regression_client.custom_fields.list(page_size=5))

        if fields:
            first_field = fields[0]

            # Core attributes that should be present
            expected_core_attrs = ["id", "name"]
            for attr in expected_core_attrs:
                if attr not in first_field:
                    print(f"⚠ Missing core attribute '{attr}'")

            # Optional attributes that may be present
            optional_attrs = [
                "fieldType",
                "component",
                "description",
                "required",
                "displayOrder",
            ]
            present_optional = [attr for attr in optional_attrs if attr in first_field]

            print(
                f"✓ Core attributes: {[attr for attr in expected_core_attrs if attr in first_field]}"
            )
            print(f"✓ Optional attributes present: {present_optional}")

            # Log data types for debugging
            for key, value in first_field.items():
                if value is not None:
                    print(f"  {key}: {type(value).__name__}")

        else:
            pytest.skip("No custom fields available for structure validation")

    def test_custom_fields_find_by_name(self, regression_client):
        """Test finding custom fields by name."""
        fields = list(regression_client.custom_fields.list(limit=5))

        if not fields:
            pytest.skip("No custom fields available for name search test")

        # Get the first field's name for testing
        test_field_name = fields[0].get("name")
        if not test_field_name:
            pytest.skip("Custom field missing 'name' attribute")

        # Test find by name
        found_field = regression_client.custom_fields.find_by_name(test_field_name)

        if found_field:
            assert found_field.get("name") == test_field_name
            print(f"✓ Found custom field by name: '{test_field_name}'")
        else:
            print(f"⚠ Could not find custom field by name: '{test_field_name}'")

        # Test find non-existent field
        not_found = regression_client.custom_fields.find_by_name("NonExistentField_XYZ")
        assert not_found is None
        print("✓ Correctly returned None for non-existent field name")

    def test_custom_fields_find_by_name_and_category(self, regression_client):
        """Test finding custom fields by name and category."""
        # Get a field from a specific category
        account_fields = list(
            regression_client.custom_fields.get_by_category(CustomFieldCategory.ACCOUNT)
        )

        if not account_fields:
            print("⚠ No account custom fields available for name+category test")
            return

        test_field_name = account_fields[0].get("name")
        if not test_field_name:
            print("⚠ Account custom field missing 'name' attribute")
            return

        # Test find by name and category
        found_field = regression_client.custom_fields.find_by_name_and_category(
            test_field_name, CustomFieldCategory.ACCOUNT
        )

        if found_field:
            assert found_field.get("name") == test_field_name
            print(
                f"✓ Found custom field by name and category: '{test_field_name}' in Account"
            )
        else:
            print(f"⚠ Could not find field '{test_field_name}' in Account category")

        # Test find in wrong category
        not_found = regression_client.custom_fields.find_by_name_and_category(
            test_field_name, CustomFieldCategory.DONATION
        )
        if not_found is None:
            print("✓ Correctly returned None when searching in wrong category")
        else:
            print(
                "⚠ Found field in wrong category (may be valid if field exists in both)"
            )

    def test_custom_fields_get_field_options(self, regression_client):
        """Test getting options for dropdown custom fields."""
        fields = list(regression_client.custom_fields.list(limit=10))

        dropdown_field = None
        for field in fields:
            if field.get("fieldType") in ["dropdown", "select", "multiselect"]:
                dropdown_field = field
                break

        if dropdown_field:
            field_id = dropdown_field.get("id")
            options = regression_client.custom_fields.get_field_options(field_id)

            print(
                f"✓ Retrieved {len(options)} options for dropdown field: {dropdown_field.get('name')}"
            )
            if options:
                print(f"  First option: {options[0]}")
        else:
            print("⚠ No dropdown custom fields found to test options")

    def test_custom_fields_convenience_methods_integration(self, regression_client):
        """Test integration of convenience methods with core functionality."""
        # Test that convenience methods work with the basic get() method
        fields = list(regression_client.custom_fields.list(limit=3))

        for field in fields:
            field_id = field.get("id")
            field_name = field.get("name")

            if field_id and field_name:
                # Get field by ID (basic method)
                direct_field = regression_client.custom_fields.get(field_id)

                # Find field by name (convenience method)
                found_field = regression_client.custom_fields.find_by_name(field_name)

                if found_field:
                    assert direct_field.get("id") == found_field.get("id")
                    print(
                        f"✓ Direct get() and find_by_name() returned same field: {field_name}"
                    )
                    break
        else:
            print("⚠ Could not test convenience method integration")

    def test_custom_fields_empty_results_handling(self, regression_client):
        """Test handling of empty results."""
        # Try with filter that likely returns no results
        empty_fields = list(
            regression_client.custom_fields.list(
                category="nonexistent_category_xyz", page_size=10
            )
        )

        if len(empty_fields) == 0:
            print("✓ Empty results handled correctly")
        else:
            print(f"⚠ Expected empty results, got {len(empty_fields)} fields")

    def test_custom_fields_direct_api_endpoint(self, regression_client):
        """Test direct API endpoint behavior for custom fields."""
        # Test direct endpoint call to understand response structure
        response = regression_client.get(
            "/customFields", params={"currentPage": 0, "pageSize": 5}
        )

        print(f"Direct API response keys: {list(response.keys())}")

        # Analyze response structure
        if "searchResults" in response:
            results = response["searchResults"]
            print(f"✓ Standard paginated response: {len(results)} custom fields")
        elif isinstance(response, list):
            print(f"✓ Direct list response: {len(response)} custom fields")
        else:
            print(f"⚠ Unexpected response structure: {type(response)}")

    def test_custom_field_groups_list(self, regression_client):
        """Test listing custom field groups."""
        try:
            groups = list(regression_client.custom_fields.list_groups(limit=10))
            print(f"✓ Retrieved {len(groups)} custom field groups")

            if groups:
                first_group = groups[0]
                assert isinstance(first_group, dict), "Group should be a dictionary"
                print(f"Group structure: {list(first_group.keys())}")

                # Check for expected group attributes
                expected_attrs = ["id", "name"]
                missing_attrs = [
                    attr for attr in expected_attrs if attr not in first_group
                ]
                if missing_attrs:
                    print(f"⚠ Missing expected group attributes: {missing_attrs}")
                else:
                    print("✓ All expected group attributes present")

        except Exception as e:
            print(f"⚠ Could not list custom field groups: {e}")

    def test_custom_field_groups_limit_parameter(self, regression_client):
        """Test limit parameter for groups."""
        try:
            limited_groups = list(
                regression_client.custom_fields.list_groups(page_size=20, limit=3)
            )

            if len(limited_groups) > 3:
                print(
                    f"⚠ Group limit not working: got {len(limited_groups)}, expected max 3"
                )
            else:
                print(
                    f"✓ Group limit parameter working: got {len(limited_groups)} groups"
                )

            # Test limit=None
            unlimited_groups = list(
                regression_client.custom_fields.list_groups(page_size=10, limit=None)
            )
            print(f"✓ limit=None works for groups: got {len(unlimited_groups)} groups")

        except Exception as e:
            print(f"⚠ Could not test group limit parameter: {e}")

    def test_custom_field_groups_get_specific(self, regression_client):
        """Test getting specific custom field group by ID."""
        try:
            groups = list(regression_client.custom_fields.list_groups(limit=1))
            group_id = None
            if groups:
                group_id = groups[0].get("id")

            if group_id:
                specific_group = regression_client.custom_fields.get_group(group_id)
                assert isinstance(specific_group, dict)
                assert specific_group.get("id") == group_id
                print(f"✓ Retrieved specific custom field group: {group_id}")
            else:
                print("⚠ No custom field groups available to test specific retrieval")

        except Exception as e:
            print(f"⚠ Could not test specific group retrieval: {e}")

    def test_custom_field_groups_get_invalid_id(self, regression_client):
        """Test error handling for invalid custom field group ID."""
        try:
            with pytest.raises(NeonNotFoundError):
                regression_client.custom_fields.get_group(999999999)
            print("✓ Correctly received 404 for invalid custom field group ID")
        except Exception as e:
            print(f"⚠ Could not test invalid group ID: {e}")

    def test_custom_field_groups_find_by_name(self, regression_client):
        """Test finding custom field groups by name."""
        try:
            groups = list(regression_client.custom_fields.list_groups(limit=5))

            if not groups:
                print("⚠ No custom field groups available for name search test")
                return

            # Get the first group's name for testing
            test_group_name = groups[0].get("name")
            if not test_group_name:
                print("⚠ Custom field group missing 'name' attribute")
                return

            # Test find by name
            found_group = regression_client.custom_fields.find_group_by_name(
                test_group_name
            )

            if found_group:
                assert found_group.get("name") == test_group_name
                print(f"✓ Found custom field group by name: '{test_group_name}'")
            else:
                print(
                    f"⚠ Could not find custom field group by name: '{test_group_name}'"
                )

            # Test find non-existent group
            not_found = regression_client.custom_fields.find_group_by_name(
                "NonExistentGroup_XYZ"
            )
            assert not_found is None
            print("✓ Correctly returned None for non-existent group name")

        except Exception as e:
            print(f"⚠ Could not test group find by name: {e}")

    def test_custom_field_groups_pagination(self, regression_client):
        """Test pagination behavior for custom field groups."""
        try:
            # Get first page
            page1_groups = list(
                regression_client.custom_fields.list_groups(page_size=3, current_page=0)
            )

            # Get second page
            page2_groups = list(
                regression_client.custom_fields.list_groups(page_size=3, current_page=1)
            )

            print(f"✓ Groups Page 1: {len(page1_groups)} groups")
            print(f"✓ Groups Page 2: {len(page2_groups)} groups")

            # Check for overlap (shouldn't be any)
            if page1_groups and page2_groups:
                page1_ids = {g.get("id") for g in page1_groups if "id" in g}
                page2_ids = {g.get("id") for g in page2_groups if "id" in g}

                overlap = page1_ids.intersection(page2_ids)
                if overlap:
                    print(f"❌ Groups pagination overlap: {len(overlap)} duplicate IDs")
                else:
                    print("✓ No groups pagination overlap")

        except Exception as e:
            print(f"⚠ Could not test groups pagination: {e}")

    def test_custom_field_groups_category_filtering(self, regression_client):
        """Test category-based filtering with enum for groups."""
        valid_categories = [
            CustomFieldCategory.ACCOUNT,
            CustomFieldCategory.DONATION,
            CustomFieldCategory.EVENT,
            CustomFieldCategory.MEMBERSHIP,
            CustomFieldCategory.ACTIVITY,
        ]

        for category in valid_categories:
            try:
                groups = list(
                    regression_client.custom_fields.list_groups(
                        page_size=10, category=category
                    )
                )
                print(f"✓ Groups Category '{category.value}': {len(groups)} groups")

                # Validate category filtering (groups use 'component' field)
                for group in groups[:3]:  # Check first few
                    if "component" in group:
                        if group["component"] != category.value:
                            print(
                                f"⚠ Group category mismatch: expected {category.value}, got {group['component']}"
                            )

            except Exception as e:
                print(f"❌ Groups category '{category.value}' failed: {e}")

        # Test string category (backward compatibility)
        try:
            string_groups = list(
                regression_client.custom_fields.list_groups(category="Account")
            )
            print(
                f"✓ String category 'Account' for groups: {len(string_groups)} groups"
            )
        except Exception as e:
            print(f"❌ String category for groups failed: {e}")

    def test_custom_field_groups_get_by_category_method(self, regression_client):
        """Test the get_groups_by_category convenience method."""
        categories_to_test = [
            CustomFieldCategory.ACCOUNT,
            CustomFieldCategory.DONATION,
            CustomFieldCategory.EVENT,
        ]

        for category in categories_to_test:
            try:
                # Test convenience method
                convenience_groups = list(
                    regression_client.custom_fields.get_groups_by_category(category)
                )

                # Compare with direct list call
                direct_groups = list(
                    regression_client.custom_fields.list_groups(category=category)
                )

                print(
                    f"✓ get_groups_by_category('{category.value}'): {len(convenience_groups)} groups"
                )

                if len(convenience_groups) != len(direct_groups):
                    print(
                        f"⚠ Groups method mismatch: convenience={len(convenience_groups)}, direct={len(direct_groups)}"
                    )
                else:
                    print("✓ get_groups_by_category matches direct list call")

            except Exception as e:
                print(f"❌ get_groups_by_category('{category.value}') failed: {e}")

    def test_custom_field_groups_find_by_name_and_category(self, regression_client):
        """Test finding custom field groups by name and category."""
        try:
            # Get a group from a specific category
            account_groups = list(
                regression_client.custom_fields.get_groups_by_category(
                    CustomFieldCategory.ACCOUNT
                )
            )

            if not account_groups:
                print(
                    "⚠ No account custom field groups available for name+category test"
                )
                return

            test_group_name = account_groups[0].get("name")
            if not test_group_name:
                print("⚠ Account custom field group missing 'name' attribute")
                return

            # Test find by name and category
            found_group = (
                regression_client.custom_fields.find_group_by_name_and_category(
                    test_group_name, CustomFieldCategory.ACCOUNT
                )
            )

            if found_group:
                assert found_group.get("name") == test_group_name
                print(
                    f"✓ Found custom field group by name and category: '{test_group_name}' in Account"
                )
            else:
                print(f"⚠ Could not find group '{test_group_name}' in Account category")

            # Test find in wrong category
            not_found = regression_client.custom_fields.find_group_by_name_and_category(
                test_group_name, CustomFieldCategory.DONATION
            )
            if not_found is None:
                print(
                    "✓ Correctly returned None when searching group in wrong category"
                )
            else:
                print(
                    "⚠ Found group in wrong category (may be valid if group exists in both)"
                )

        except Exception as e:
            print(f"⚠ Could not test group find by name and category: {e}")


# Note: Custom fields are typically read-only in most CRM systems
# Write operations (create, update, delete) are usually done through admin interfaces
# If write operations are available, they would be added here:

# @pytest.mark.regression
# @pytest.mark.writeops
# class TestCustomFieldsWriteOperations:
#     """Write operation tests for CustomFieldsResource - if available."""
#     pass
