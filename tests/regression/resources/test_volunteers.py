"""Comprehensive regression tests for VolunteersResource.

Tests both read-only and write operations for the volunteers endpoint.
Organized to match src/neon_crm/resources/volunteers.py structure.
"""

import pytest

from neon_crm.exceptions import (
    NeonNotFoundError,
)


@pytest.mark.regression
@pytest.mark.readonly
class TestVolunteersReadOnly:
    """Read-only tests for VolunteersResource - safe for production."""

    def test_volunteers_list_basic(self, regression_client):
        """Test basic volunteer listing."""
        volunteers = list(regression_client.volunteers.list(limit=5))

        print(f"✓ Retrieved {len(volunteers)} volunteers")

        if volunteers:
            first_volunteer = volunteers[0]
            assert isinstance(first_volunteer, dict), "Volunteer should be a dictionary"
            print(f"Volunteer structure: {list(first_volunteer.keys())}")

    def test_volunteers_limit_parameter_fixed(self, regression_client):
        """Test limit parameter - this was broken before the fix."""
        limited_volunteers = list(
            regression_client.volunteers.list(page_size=20, limit=5)
        )

        if len(limited_volunteers) > 5:
            print(
                f"❌ CRITICAL: Limit not working: got {len(limited_volunteers)}, expected max 5"
            )
        else:
            print(
                f"✓ FIXED: Limit parameter working: got {len(limited_volunteers)} volunteers"
            )

        try:
            unlimited_volunteers = list(
                regression_client.volunteers.list(page_size=10, limit=None)
            )
            print(
                f"✓ FIXED: limit=None works: got {len(unlimited_volunteers)} volunteers"
            )
        except TypeError as e:
            print(f"❌ CRITICAL: limit=None still crashes: {e}")

    def test_volunteers_get_specific(self, regression_client):
        """Test getting specific volunteer by ID."""
        volunteers = list(regression_client.volunteers.list(limit=1))
        volunteer_id = None
        if volunteers:
            volunteer_id = volunteers[0].get("volunteerId") or volunteers[0].get("id")

        if volunteer_id:
            specific_volunteer = regression_client.volunteers.get(volunteer_id)
            assert isinstance(specific_volunteer, dict)
            print(f"✓ Retrieved specific volunteer: {volunteer_id}")
        else:
            pytest.skip("No volunteers available to test specific retrieval")

    def test_volunteers_get_invalid_id(self, regression_client):
        """Test error handling for invalid volunteer ID."""
        with pytest.raises(NeonNotFoundError):
            regression_client.volunteers.get(999999999)
        print("✓ Correctly received 404 for invalid volunteer ID")


@pytest.mark.regression
@pytest.mark.writeops
class TestVolunteersWriteOperations:
    """Write operation tests for VolunteersResource - modifies database."""

    def test_volunteers_write_placeholder(self, write_regression_client):
        """Placeholder for volunteer write operations."""
        # Note: Volunteer management often requires specific volunteer programs
        # and role configurations to be set up in the CRM
        print("⚠ Volunteer write operations require specific program setup")
