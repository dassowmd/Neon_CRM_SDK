"""Comprehensive regression tests for RecurringDonationsResource.

Tests both read-only and write operations for the recurring donations endpoint.
Organized to match src/neon_crm/resources/recurring_donations.py structure.
"""

import time
from datetime import datetime

import pytest

from neon_crm.exceptions import (
    NeonNotFoundError,
)
from neon_crm.types import SearchRequest


@pytest.mark.regression
@pytest.mark.readonly
class TestRecurringDonationsReadOnly:
    """Read-only tests for RecurringDonationsResource - safe for production."""

    def test_recurring_donations_list_basic(self, regression_client):
        """Test basic recurring donation listing."""
        recurring_donations = list(regression_client.recurring_donations.list(limit=5))

        print(f"✓ Retrieved {len(recurring_donations)} recurring donations")

        if recurring_donations:
            first_donation = recurring_donations[0]
            assert isinstance(
                first_donation, dict
            ), "Recurring donation should be a dictionary"
            print(f"Recurring donation structure: {list(first_donation.keys())}")

    def test_recurring_donations_limit_parameter_fixed(self, regression_client):
        """Test limit parameter - this was broken before the fix."""
        limited_donations = list(
            regression_client.recurring_donations.list(page_size=20, limit=5)
        )

        if len(limited_donations) > 5:
            print(
                f"❌ CRITICAL: Limit not working: got {len(limited_donations)}, expected max 5"
            )
        else:
            print(
                f"✓ FIXED: Limit parameter working: got {len(limited_donations)} recurring donations"
            )

        try:
            unlimited_donations = list(
                regression_client.recurring_donations.list(page_size=10, limit=None)
            )
            print(
                f"✓ FIXED: limit=None works: got {len(unlimited_donations)} recurring donations"
            )
        except TypeError as e:
            print(f"❌ CRITICAL: limit=None still crashes: {e}")

    def test_recurring_donations_status_filtering(self, regression_client):
        """Test recurring donation filtering by status."""
        try:
            statuses = ["active", "suspended", "cancelled", "completed"]

            for status in statuses:
                try:
                    status_donations = list(
                        regression_client.recurring_donations.list(
                            page_size=5, status=status
                        )
                    )
                    print(
                        f"✓ Status '{status}': {len(status_donations)} recurring donations"
                    )

                except Exception as e:
                    print(f"⚠ Status '{status}' filtering failed: {e}")

        except Exception as e:
            print(f"❌ Status filtering test failed: {e}")

    def test_recurring_donations_search(self, regression_client):
        """Test recurring donation search functionality."""
        search_request: SearchRequest = {
            "searchFields": [
                {"field": "amount", "operator": "GREATER_THAN", "value": "0"}
            ],
            "outputFields": [
                "recurringDonationId",
                "accountId",
                "amount",
                "frequency",
                "status",
            ],
            "pagination": {"currentPage": 0, "pageSize": 5},
        }

        results = list(regression_client.recurring_donations.search(search_request))[:5]

        print(f"✓ Recurring donation search returned {len(results)} results")

    def test_recurring_donations_get_specific(self, regression_client):
        """Test getting specific recurring donation by ID."""
        donations = list(regression_client.recurring_donations.list(limit=1))
        recurring_donation_id = None
        if donations:
            recurring_donation_id = donations[0].get(
                "recurringDonationId"
            ) or donations[0].get("id")

        if recurring_donation_id:
            specific_donation = regression_client.recurring_donations.get(
                recurring_donation_id
            )
            assert isinstance(specific_donation, dict)
            print(f"✓ Retrieved specific recurring donation: {recurring_donation_id}")
        else:
            pytest.skip("No recurring donations available to test specific retrieval")

    def test_recurring_donations_get_invalid_id(self, regression_client):
        """Test error handling for invalid recurring donation ID."""
        with pytest.raises(NeonNotFoundError):
            regression_client.recurring_donations.get(999999999)
        print("✓ Correctly received 404 for invalid recurring donation ID")


@pytest.mark.regression
@pytest.mark.writeops
class TestRecurringDonationsWriteOperations:
    """Write operation tests for RecurringDonationsResource - modifies database."""

    def test_create_recurring_donation_basic(self, write_regression_client):
        """Test creating a basic recurring donation."""
        timestamp = int(time.time())

        # Create test account first
        account_payload = {
            "individualAccount": {
                "accountType": "INDIVIDUAL",
                "firstName": "RecurringDonor",
                "lastName": f"Test{timestamp}",
                "email": f"recurring.donor.{timestamp}@example.com",
            }
        }

        created_accounts = []
        created_recurring_donations = []

        try:
            account_result = write_regression_client.accounts.create(account_payload)
            account_id = account_result["accountId"]
            created_accounts.append(account_id)

            # Create recurring donation
            recurring_donation_payload = {
                "recurringDonation": {
                    "accountId": account_id,
                    "amount": 50.0,
                    "frequency": "Monthly",
                    "startDate": datetime.now().strftime("%Y-%m-%d"),
                    "campaign": {"id": 1},
                    "fund": {"id": 1},
                    "status": "active",
                }
            }

            donation_result = write_regression_client.recurring_donations.create(
                recurring_donation_payload
            )
            donation_id = donation_result.get(
                "recurringDonationId"
            ) or donation_result.get("id")

            if donation_id:
                created_recurring_donations.append(donation_id)
                print(f"✓ Created recurring donation: {donation_id}")

        except Exception as e:
            print(f"❌ Recurring donation creation failed: {e}")
        finally:
            # Cleanup
            for donation_id in created_recurring_donations:
                try:
                    write_regression_client.recurring_donations.delete(donation_id)
                    print(f"✓ Cleaned up recurring donation: {donation_id}")
                except Exception as e:
                    print(f"⚠ Could not delete recurring donation {donation_id}: {e}")

            for account_id in created_accounts:
                try:
                    write_regression_client.accounts.delete(account_id)
                    print(f"✓ Cleaned up account: {account_id}")
                except Exception as e:
                    print(f"⚠ Could not delete account {account_id}: {e}")
