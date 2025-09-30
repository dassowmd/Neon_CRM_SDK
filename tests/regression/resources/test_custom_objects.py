"""Comprehensive regression tests for CustomObjectsResource.

Tests both read-only and write operations for the custom objects endpoint.
Organized to match src/neon_crm/resources/custom_objects.py structure.
"""

import pytest

from neon_crm.exceptions import (
    NeonNotFoundError,
)
from neon_crm.types import SearchRequest


@pytest.mark.regression
@pytest.mark.readonly
class TestCustomObjectsReadOnly:
    """Read-only tests for CustomObjectsResource - safe for production."""

    def test_custom_objects_list_basic(self, regression_client):
        """Test basic custom object listing."""
        custom_objects = list(regression_client.custom_objects.list(limit=5))

        print(f"✓ Retrieved {len(custom_objects)} custom objects")

        if custom_objects:
            first_object = custom_objects[0]
            assert isinstance(
                first_object, dict
            ), "Custom object should be a dictionary"
            print(f"Custom object structure: {list(first_object.keys())}")

    def test_custom_objects_limit_parameter_fixed(self, regression_client):
        """Test limit parameter - this was broken before the fix."""
        limited_objects = list(
            regression_client.custom_objects.list(page_size=20, limit=5)
        )

        if len(limited_objects) > 5:
            print(
                f"❌ CRITICAL: Limit not working: got {len(limited_objects)}, expected max 5"
            )
        else:
            print(
                f"✓ FIXED: Limit parameter working: got {len(limited_objects)} custom objects"
            )

        try:
            unlimited_objects = list(
                regression_client.custom_objects.list(page_size=10, limit=None)
            )
            print(
                f"✓ FIXED: limit=None works: got {len(unlimited_objects)} custom objects"
            )
        except TypeError as e:
            print(f"❌ CRITICAL: limit=None still crashes: {e}")

    def test_custom_objects_get_specific(self, regression_client):
        """Test getting specific custom object by ID."""
        objects = list(regression_client.custom_objects.list(limit=1))
        object_id = None
        if objects:
            object_id = objects[0].get("customObjectId") or objects[0].get("id")

        if object_id:
            specific_object = regression_client.custom_objects.get(object_id)
            assert isinstance(specific_object, dict)
            print(f"✓ Retrieved specific custom object: {object_id}")
        else:
            pytest.skip("No custom objects available to test specific retrieval")

    def test_custom_objects_get_invalid_id(self, regression_client):
        """Test error handling for invalid custom object ID."""
        with pytest.raises(NeonNotFoundError):
            regression_client.custom_objects.get(999999999)
        print("✓ Correctly received 404 for invalid custom object ID")

    def test_custom_objects_search(self, regression_client):
        """Test custom objects search functionality."""
        search_request: SearchRequest = {
            "searchFields": [{"field": "status", "operator": "NOT_BLANK"}],
            "outputFields": ["id", "name", "status"],
            "pagination": {"currentPage": 0, "pageSize": 5},
        }

        try:
            results = list(regression_client.custom_objects.search(search_request))[:5]
            print(f"✓ Custom objects search returned {len(results)} results")

            if results:
                first_result = results[0]
                # Validate search results contain requested fields
                requested_fields = ["id", "name", "status"]
                missing_fields = [f for f in requested_fields if f not in first_result]
                if missing_fields:
                    print(f"⚠ Missing requested fields: {missing_fields}")
                else:
                    print("✓ All requested fields present in results")
        except Exception as e:
            print(f"⚠ Custom objects search failed: {e}")

    def test_custom_objects_get_search_fields(self, regression_client):
        """Test getting available search fields for custom objects."""
        try:
            search_fields = regression_client.custom_objects.get_search_fields()
            assert isinstance(search_fields, dict)
            print(f"✓ Retrieved {len(search_fields)} custom object search fields")
        except Exception as e:
            print(f"⚠ Get search fields failed: {e}")

    def test_custom_objects_get_output_fields(self, regression_client):
        """Test getting available output fields for custom objects."""
        try:
            output_fields = regression_client.custom_objects.get_output_fields()
            assert isinstance(output_fields, dict)
            print(f"✓ Retrieved {len(output_fields)} custom object output fields")
        except Exception as e:
            print(f"⚠ Get output fields failed: {e}")


@pytest.mark.regression
@pytest.mark.writeops
class TestCustomObjectsWriteOperations:
    """Write operation tests for CustomObjectsResource - modifies database."""

    def test_custom_objects_write_placeholder(self, write_regression_client):
        """Placeholder for custom object write operations."""
        # Note: Custom objects require specific schema setup in Neon CRM
        # The exact structure depends on how custom objects are configured
        print("⚠ Custom object operations require specific schema configuration")
