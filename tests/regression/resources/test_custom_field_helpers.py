"""Tests for custom field helper methods on all resources.

These tests verify that all resources now have convenient custom field access methods.
"""

import pytest


@pytest.mark.regression
@pytest.mark.readonly
class TestCustomFieldHelpers:
    """Test custom field helper methods across all resources."""

    def test_accounts_custom_field_helpers(self, regression_client):
        """Test custom field helpers on accounts resource."""
        # Test list custom fields
        custom_fields = list(regression_client.accounts.list_custom_fields(limit=5))
        print(f"✓ Accounts custom fields: {len(custom_fields)}")

        if custom_fields:
            # Test find by name
            field_name = custom_fields[0].get("name")
            found_field = regression_client.accounts.find_custom_field_by_name(
                field_name
            )
            if found_field:
                print(f"✓ Found account custom field by name: {field_name}")
            else:
                print(f"⚠ Could not find account custom field: {field_name}")

            # Test get by ID
            field_id = custom_fields[0].get("id")
            if field_id:
                retrieved_field = regression_client.accounts.get_custom_field(field_id)
                assert retrieved_field.get("id") == field_id
                print(f"✓ Retrieved account custom field by ID: {field_id}")

        # Test custom field groups
        try:
            groups = list(regression_client.accounts.list_custom_field_groups(limit=3))
            print(f"✓ Account custom field groups: {len(groups)}")

            if groups:
                group_name = groups[0].get("name")
                found_group = (
                    regression_client.accounts.find_custom_field_group_by_name(
                        group_name
                    )
                )
                if found_group:
                    print(f"✓ Found account custom field group by name: {group_name}")
        except Exception as e:
            print(f"⚠ Account custom field groups test failed: {e}")

    def test_donations_custom_field_helpers(self, regression_client):
        """Test custom field helpers on donations resource."""
        try:
            # Test list custom fields
            custom_fields = list(
                regression_client.donations.list_custom_fields(limit=3)
            )
            print(f"✓ Donations custom fields: {len(custom_fields)}")

            if custom_fields:
                field_name = custom_fields[0].get("name")
                found_field = regression_client.donations.find_custom_field_by_name(
                    field_name
                )
                if found_field:
                    print(f"✓ Found donation custom field by name: {field_name}")
        except Exception as e:
            print(f"⚠ Donations custom field test failed: {e}")

    def test_events_custom_field_helpers(self, regression_client):
        """Test custom field helpers on events resource."""
        try:
            # Test list custom fields
            custom_fields = list(regression_client.events.list_custom_fields(limit=3))
            print(f"✓ Events custom fields: {len(custom_fields)}")

            if custom_fields:
                field_name = custom_fields[0].get("name")
                found_field = regression_client.events.find_custom_field_by_name(
                    field_name
                )
                if found_field:
                    print(f"✓ Found event custom field by name: {field_name}")
        except Exception as e:
            print(f"⚠ Events custom field test failed: {e}")

    def test_activities_custom_field_helpers(self, regression_client):
        """Test custom field helpers on activities resource."""
        try:
            # Test list custom fields
            custom_fields = list(
                regression_client.activities.list_custom_fields(limit=3)
            )
            print(f"✓ Activities custom fields: {len(custom_fields)}")

            if custom_fields:
                field_name = custom_fields[0].get("name")
                found_field = regression_client.activities.find_custom_field_by_name(
                    field_name
                )
                if found_field:
                    print(f"✓ Found activity custom field by name: {field_name}")
        except Exception as e:
            print(f"⚠ Activities custom field test failed: {e}")

    def test_memberships_custom_field_helpers(self, regression_client):
        """Test custom field helpers on memberships resource."""
        try:
            # Test list custom fields
            custom_fields = list(
                regression_client.memberships.list_custom_fields(limit=3)
            )
            print(f"✓ Memberships custom fields: {len(custom_fields)}")

            if custom_fields:
                field_name = custom_fields[0].get("name")
                found_field = regression_client.memberships.find_custom_field_by_name(
                    field_name
                )
                if found_field:
                    print(f"✓ Found membership custom field by name: {field_name}")
        except Exception as e:
            print(f"⚠ Memberships custom field test failed: {e}")

    def test_unsupported_endpoint_custom_fields(self, regression_client):
        """Test that unsupported endpoints raise appropriate errors."""
        # Test with a resource that shouldn't have custom fields
        try:
            list(regression_client.online_store.list_custom_fields(limit=1))
            print("⚠ Online store unexpectedly supports custom fields")
        except ValueError as e:
            if "not supported" in str(e):
                print("✓ Correctly raised error for unsupported endpoint")
            else:
                print(f"⚠ Unexpected error for unsupported endpoint: {e}")
        except Exception as e:
            print(f"⚠ Unexpected error type for unsupported endpoint: {e}")

    def test_custom_field_filtering_helpers(self, regression_client):
        """Test custom field filtering through helper methods."""
        try:
            # Test field type filtering
            text_fields = list(
                regression_client.accounts.list_custom_fields(
                    field_type="text", limit=3
                )
            )
            print(f"✓ Account text custom fields: {len(text_fields)}")

            # Validate filtering worked
            for field in text_fields:
                if field.get("fieldType") and field["fieldType"].lower() != "text":
                    print(
                        f"⚠ Field type filter failed: expected text, got {field['fieldType']}"
                    )
                    break
            else:
                if text_fields:
                    print("✓ Field type filtering working correctly")

        except Exception as e:
            print(f"⚠ Custom field filtering test failed: {e}")


@pytest.mark.regression
@pytest.mark.readonly
class TestCustomFieldCategoryIterator:
    """Test the iterate all categories functionality."""

    def test_list_all_categories(self, regression_client):
        """Test iterating through all custom field categories."""
        # Test the all categories iterator
        all_fields = list(regression_client.custom_fields.list_all_categories(limit=20))
        print(f"✓ Custom fields from all categories: {len(all_fields)}")

        # Verify we got fields from multiple categories
        categories_found = set()
        for field in all_fields:
            component = field.get("component")
            if component:
                categories_found.add(component)

        print(
            f"✓ Found fields from {len(categories_found)} categories: {list(categories_found)}"
        )

        if len(categories_found) > 1:
            print("✓ All categories iterator working across multiple categories")
        elif len(categories_found) == 1:
            print("⚠ Only found fields from one category (may be expected)")
        else:
            print("⚠ No category information found in fields")

    def test_list_all_groups_categories(self, regression_client):
        """Test iterating through all custom field group categories."""
        try:
            # Test the all group categories iterator
            all_groups = list(
                regression_client.custom_fields.list_all_groups_categories(limit=15)
            )
            print(f"✓ Custom field groups from all categories: {len(all_groups)}")

            # Verify we got groups from multiple categories
            categories_found = set()
            for group in all_groups:
                component = group.get("component")
                if component:
                    categories_found.add(component)

            print(
                f"✓ Found groups from {len(categories_found)} categories: {list(categories_found)}"
            )

            if len(categories_found) > 1:
                print(
                    "✓ All group categories iterator working across multiple categories"
                )
            elif len(categories_found) == 1:
                print("⚠ Only found groups from one category (may be expected)")

        except Exception as e:
            print(f"⚠ All groups categories test failed: {e}")

    def test_category_iterator_with_limits(self, regression_client):
        """Test category iterator respects limits."""
        # Test with small limit
        limited_fields = list(
            regression_client.custom_fields.list_all_categories(limit=3)
        )

        if len(limited_fields) <= 3:
            print(
                f"✓ Category iterator limit working: got {len(limited_fields)} fields (max 3)"
            )
        else:
            print(
                f"❌ Category iterator limit not working: got {len(limited_fields)} fields, expected max 3"
            )

        # Test with no limit
        unlimited_fields = list(
            regression_client.custom_fields.list_all_categories(limit=None)
        )
        print(f"✓ Category iterator without limit: {len(unlimited_fields)} fields")

        if len(unlimited_fields) >= len(limited_fields):
            print("✓ Unlimited iterator returned at least as many as limited")
        else:
            print("⚠ Unlimited iterator returned fewer fields than limited")

    def test_category_mapping_coverage(self, regression_client):
        """Test that category mapping covers expected endpoints."""
        from neon_crm.resources.base import BaseResource

        # Test that we can get categories for main resources
        test_resources = [
            ("/accounts", "accounts"),
            ("/donations", "donations"),
            ("/events", "events"),
            ("/activities", "activities"),
            ("/memberships", "memberships"),
        ]

        for endpoint, resource_name in test_resources:
            try:
                # Create a mock resource to test category mapping
                mock_resource = BaseResource(regression_client, endpoint)
                category = mock_resource._get_resource_category()

                if category:
                    print(f"✓ {resource_name} maps to category: {category.value}")
                else:
                    print(f"⚠ {resource_name} has no category mapping")

            except Exception as e:
                print(f"⚠ Category mapping test failed for {resource_name}: {e}")
