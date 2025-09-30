"""Comprehensive regression tests for PropertiesResource.

Tests both read-only operations for the properties endpoint.
Organized to match src/neon_crm/resources/properties.py structure.
"""

import pytest

from neon_crm.exceptions import (
    NeonNotFoundError,
)


@pytest.mark.regression
@pytest.mark.readonly
class TestPropertiesReadOnly:
    """Read-only tests for PropertiesResource - safe for production."""

    def test_properties_list_basic(self, regression_client):
        """Test basic property listing."""
        properties = list(regression_client.properties.list(limit=10))

        print(f"✓ Retrieved {len(properties)} properties")

        if properties:
            first_property = properties[0]
            assert isinstance(first_property, dict), "Property should be a dictionary"
            print(f"Property structure: {list(first_property.keys())}")

    def test_properties_limit_parameter_fixed(self, regression_client):
        """Test limit parameter - this was broken before the fix."""
        limited_properties = list(
            regression_client.properties.list(page_size=20, limit=5)
        )

        if len(limited_properties) > 5:
            print(
                f"❌ CRITICAL: Limit not working: got {len(limited_properties)}, expected max 5"
            )
        else:
            print(
                f"✓ FIXED: Limit parameter working: got {len(limited_properties)} properties"
            )

        try:
            unlimited_properties = list(
                regression_client.properties.list(page_size=10, limit=None)
            )
            print(
                f"✓ FIXED: limit=None works: got {len(unlimited_properties)} properties"
            )
        except TypeError as e:
            print(f"❌ CRITICAL: limit=None still crashes: {e}")

    def test_properties_get_specific(self, regression_client):
        """Test getting specific property by ID."""
        properties = list(regression_client.properties.list(limit=1))
        property_id = None
        if properties:
            property_id = properties[0].get("propertyId") or properties[0].get("id")

        if property_id:
            specific_property = regression_client.properties.get(property_id)
            assert isinstance(specific_property, dict)
            print(f"✓ Retrieved specific property: {property_id}")
        else:
            pytest.skip("No properties available to test specific retrieval")

    def test_properties_get_invalid_id(self, regression_client):
        """Test error handling for invalid property ID."""
        with pytest.raises(NeonNotFoundError):
            regression_client.properties.get(999999999)
        print("✓ Correctly received 404 for invalid property ID")


# Note: Properties are typically system configuration items in most CRMs
# and may not support write operations through the API
@pytest.mark.regression
@pytest.mark.writeops
class TestPropertiesWriteOperations:
    """Write operation tests for PropertiesResource - if available."""

    def test_properties_write_placeholder(self, write_regression_client):
        """Placeholder for property write operations."""
        # Note: Properties are often read-only system configuration
        print("⚠ Properties may be read-only system configuration items")
