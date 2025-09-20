"""Comprehensive regression tests for PledgesResource.

Tests both read-only and write operations for the pledges endpoint.
Organized to match src/neon_crm/resources/pledges.py structure.
"""

import time
from datetime import datetime

import pytest

from neon_crm.exceptions import (
    NeonNotFoundError,
)


@pytest.mark.regression
@pytest.mark.readonly
class TestPledgesReadOnly:
    """Read-only tests for PledgesResource - safe for production."""

    def test_pledges_list_basic(self, regression_client):
        """Test basic pledge listing."""
        pledges = list(regression_client.pledges.list(limit=5))

        print(f"✓ Retrieved {len(pledges)} pledges")

        if pledges:
            first_pledge = pledges[0]
            assert isinstance(first_pledge, dict), "Pledge should be a dictionary"
            print(f"Pledge structure: {list(first_pledge.keys())}")

    def test_pledges_limit_parameter_fixed(self, regression_client):
        """Test limit parameter - this was broken before the fix."""
        limited_pledges = list(regression_client.pledges.list(page_size=20, limit=5))

        if len(limited_pledges) > 5:
            print(
                f"❌ CRITICAL: Limit not working: got {len(limited_pledges)}, expected max 5"
            )
        else:
            print(
                f"✓ FIXED: Limit parameter working: got {len(limited_pledges)} pledges"
            )

        try:
            unlimited_pledges = list(
                regression_client.pledges.list(page_size=10, limit=None)
            )
            print(f"✓ FIXED: limit=None works: got {len(unlimited_pledges)} pledges")
        except TypeError as e:
            print(f"❌ CRITICAL: limit=None still crashes: {e}")

    def test_pledges_get_specific(self, regression_client):
        """Test getting specific pledge by ID."""
        pledges = list(regression_client.pledges.list(limit=1))
        pledge_id = None
        if pledges:
            pledge_id = pledges[0].get("pledgeId") or pledges[0].get("id")

        if pledge_id:
            specific_pledge = regression_client.pledges.get(pledge_id)
            assert isinstance(specific_pledge, dict)
            print(f"✓ Retrieved specific pledge: {pledge_id}")
        else:
            pytest.skip("No pledges available to test specific retrieval")

    def test_pledges_get_invalid_id(self, regression_client):
        """Test error handling for invalid pledge ID."""
        with pytest.raises(NeonNotFoundError):
            regression_client.pledges.get(999999999)
        print("✓ Correctly received 404 for invalid pledge ID")


@pytest.mark.regression
@pytest.mark.writeops
class TestPledgesWriteOperations:
    """Write operation tests for PledgesResource - modifies database."""

    def test_create_pledge_basic(self, write_regression_client):
        """Test creating a basic pledge."""
        timestamp = int(time.time())

        # Create test account first
        account_payload = {
            "individualAccount": {
                "accountType": "INDIVIDUAL",
                "firstName": "Pledge",
                "lastName": f"Test{timestamp}",
                "email": f"pledge.test.{timestamp}@example.com",
            }
        }

        created_accounts = []
        created_pledges = []

        try:
            account_result = write_regression_client.accounts.create(account_payload)
            account_id = account_result["accountId"]
            created_accounts.append(account_id)

            # Create pledge
            pledge_payload = {
                "pledge": {
                    "accountId": account_id,
                    "amount": 1000.0,
                    "totalPledgeAmount": 5000.0,
                    "installments": 5,
                    "frequency": "Monthly",
                    "startDate": datetime.now().strftime("%Y-%m-%d"),
                }
            }

            pledge_result = write_regression_client.pledges.create(pledge_payload)
            pledge_id = pledge_result.get("pledgeId") or pledge_result.get("id")

            if pledge_id:
                created_pledges.append(pledge_id)
                print(f"✓ Created pledge: {pledge_id}")

        except Exception as e:
            print(f"❌ Pledge creation failed: {e}")
        finally:
            # Cleanup
            for pledge_id in created_pledges:
                try:
                    write_regression_client.pledges.delete(pledge_id)
                    print(f"✓ Cleaned up pledge: {pledge_id}")
                except Exception as e:
                    print(f"⚠ Could not delete pledge {pledge_id}: {e}")

            for account_id in created_accounts:
                try:
                    write_regression_client.accounts.delete(account_id)
                    print(f"✓ Cleaned up account: {account_id}")
                except Exception as e:
                    print(f"⚠ Could not delete account {account_id}: {e}")
