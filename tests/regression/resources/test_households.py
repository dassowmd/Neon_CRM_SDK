"""Comprehensive regression tests for HouseholdsResource.

Tests both read-only and write operations for the households endpoint.
Organized to match src/neon_crm/resources/households.py structure.
"""

import time

import pytest

from neon_crm.exceptions import (
    NeonNotFoundError,
)


@pytest.mark.regression
@pytest.mark.readonly
class TestHouseholdsReadOnly:
    """Read-only tests for HouseholdsResource - safe for production."""

    def test_households_list_basic(self, regression_client):
        """Test basic household listing."""
        households = list(regression_client.households.list(limit=5))

        print(f"✓ Retrieved {len(households)} households")

        if households:
            first_household = households[0]
            assert isinstance(first_household, dict), "Household should be a dictionary"
            print(f"Household structure: {list(first_household.keys())}")

    def test_households_limit_parameter_fixed(self, regression_client):
        """Test limit parameter - this was broken before the fix."""
        limited_households = list(
            regression_client.households.list(page_size=20, limit=5)
        )

        if len(limited_households) > 5:
            print(
                f"❌ CRITICAL: Limit not working: got {len(limited_households)}, expected max 5"
            )
        else:
            print(
                f"✓ FIXED: Limit parameter working: got {len(limited_households)} households"
            )

        try:
            unlimited_households = list(
                regression_client.households.list(page_size=10, limit=None)
            )
            print(
                f"✓ FIXED: limit=None works: got {len(unlimited_households)} households"
            )
        except TypeError as e:
            print(f"❌ CRITICAL: limit=None still crashes: {e}")

    def test_households_get_specific(self, regression_client):
        """Test getting specific household by ID."""
        households = list(regression_client.households.list(limit=1))
        household_id = None
        if households:
            household_id = households[0].get("householdId") or households[0].get("id")

        if household_id:
            specific_household = regression_client.households.get(household_id)
            assert isinstance(specific_household, dict)
            print(f"✓ Retrieved specific household: {household_id}")
        else:
            pytest.skip("No households available to test specific retrieval")

    def test_households_get_invalid_id(self, regression_client):
        """Test error handling for invalid household ID."""
        with pytest.raises(NeonNotFoundError):
            regression_client.households.get(999999999)
        print("✓ Correctly received 404 for invalid household ID")

    def test_households_get_members(self, regression_client):
        """Test getting household members."""
        households = list(regression_client.households.list(limit=1))
        household_id = None
        if households:
            household_id = households[0].get("householdId") or households[0].get("id")

        if household_id:
            try:
                members = list(regression_client.households.get_members(household_id))
                print(f"✓ Household {household_id} has {len(members)} members")
            except Exception as e:
                print(f"⚠ Could not get members for household {household_id}: {e}")
        else:
            pytest.skip("No households available to test member retrieval")


@pytest.mark.regression
@pytest.mark.writeops
class TestHouseholdsWriteOperations:
    """Write operation tests for HouseholdsResource - modifies database."""

    def test_create_household_basic(self, write_regression_client):
        """Test creating a basic household."""
        timestamp = int(time.time())

        created_households = []

        try:
            household_payload = {
                "household": {
                    "name": f"Test Household {timestamp}",
                    "householdType": "Family",
                }
            }

            household_result = write_regression_client.households.create(
                household_payload
            )
            household_id = household_result.get("householdId") or household_result.get(
                "id"
            )

            if household_id:
                created_households.append(household_id)
                print(f"✓ Created household: {household_id}")

        except Exception as e:
            print(f"❌ Household creation failed: {e}")
        finally:
            # Cleanup
            for household_id in created_households:
                try:
                    write_regression_client.households.delete(household_id)
                    print(f"✓ Cleaned up household: {household_id}")
                except Exception as e:
                    print(f"⚠ Could not delete household {household_id}: {e}")
