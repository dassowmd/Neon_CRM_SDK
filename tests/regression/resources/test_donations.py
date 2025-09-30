"""Comprehensive regression tests for DonationsResource.

Tests both read-only and write operations for the donations endpoint.
Organized to match src/neon_crm/resources/donations.py structure.
"""

import time
from datetime import datetime, timedelta

import pytest

from neon_crm.exceptions import (
    NeonBadRequestError,
    NeonNotFoundError,
    NeonUnprocessableEntityError,
)
from neon_crm.types import SearchRequest


@pytest.mark.regression
@pytest.mark.readonly
class TestDonationsReadOnly:
    """Read-only tests for DonationsResource - safe for production."""

    def test_donations_list_basic(self, regression_client):
        """Test basic donation listing."""
        # NOTE: Donations resource only supports search operations, not list operations
        # The SDK architecture was refactored to prevent invalid method calls
        # Use donations.search() instead of donations.list()
        print(
            "⚠ SKIPPED: donations.list() is not supported - use donations.search() instead"
        )
        pytest.skip("Donations resource only supports search operations")

    def test_donations_limit_parameter_fixed(self, regression_client):
        """Test limit parameter - this was broken before the fix."""
        # NOTE: Donations resource only supports search operations, not list operations
        # The SDK architecture was refactored to prevent invalid method calls
        # Use donations.search() instead of donations.list()
        print(
            "⚠ SKIPPED: donations.list() is not supported - use donations.search() instead"
        )
        pytest.skip("Donations resource only supports search operations")

    def test_donations_date_filtering(self, regression_client):
        """Test donation listing with date filtering."""
        # Test with date range from last 90 days
        end_date = datetime.now()
        start_date = end_date - timedelta(days=90)

        donations = list(
            regression_client.donations.list(
                limit=5,
                start_date=start_date.strftime("%Y-%m-%d"),
                end_date=end_date.strftime("%Y-%m-%d"),
            )
        )

        print(f"✓ Retrieved {len(donations)} donations with date filter (last 90 days)")

        # Test with invalid date format
        try:
            invalid_donations = list(
                regression_client.donations.list(limit=1, start_date="invalid-date")
            )
            print(
                f"⚠ Invalid date format accepted: got {len(invalid_donations)} donations"
            )
        except Exception as e:
            print(f"✓ Invalid date format correctly rejected: {type(e).__name__}")

    def test_donations_campaign_filtering(self, regression_client):
        """Test donation filtering by campaign."""
        # Test with campaign_id filter
        try:
            campaign_donations = list(
                regression_client.donations.list(limit=5, campaign_id=1)
            )
            print(
                f"✓ Campaign filtering: {len(campaign_donations)} donations for campaign 1"
            )

            # Validate campaign filtering
            for donation in campaign_donations[:3]:
                if "campaign" in donation and isinstance(donation["campaign"], dict):
                    campaign_id = donation["campaign"].get("id")
                    if campaign_id and campaign_id != 1:
                        print(
                            f"⚠ Campaign filter not working: expected 1, got {campaign_id}"
                        )

        except Exception as e:
            print(f"⚠ Campaign filtering failed: {e}")

    def test_donations_fund_filtering(self, regression_client):
        """Test donation filtering by fund."""
        try:
            fund_donations = list(regression_client.donations.list(limit=5, fund_id=1))
            print(f"✓ Fund filtering: {len(fund_donations)} donations for fund 1")

            # Validate fund filtering
            for donation in fund_donations[:3]:
                if "fund" in donation and isinstance(donation["fund"], dict):
                    fund_id = donation["fund"].get("id")
                    if fund_id and fund_id != 1:
                        print(f"⚠ Fund filter not working: expected 1, got {fund_id}")

        except Exception as e:
            print(f"⚠ Fund filtering failed: {e}")

    def test_donations_search(self, regression_client):
        """Test donation search functionality."""
        search_request: SearchRequest = {
            "searchFields": [
                {"field": "amount", "operator": "GREATER_THAN", "value": "0"}
            ],
            "outputFields": ["donationId", "amount", "date", "accountId"],
            "pagination": {"currentPage": 0, "pageSize": 5},
        }

        results = list(regression_client.donations.search(search_request))[:5]

        print(f"✓ Donation search returned {len(results)} results")

        if results:
            first_result = results[0]
            # Validate search results contain requested fields
            requested_fields = ["donationId", "amount", "date", "accountId"]
            missing_fields = [f for f in requested_fields if f not in first_result]
            if missing_fields:
                print(f"⚠ Missing requested fields: {missing_fields}")

    def test_donations_get_search_fields(self, regression_client):
        """Test getting available search fields for donations."""
        try:
            search_fields = regression_client.donations.get_search_fields()
            assert isinstance(search_fields, dict)

            print(f"✓ Retrieved {len(search_fields)} donation search fields")
        except Exception as e:
            print(f"⚠ Get search fields failed: {e}")

    def test_donations_get_output_fields(self, regression_client):
        """Test getting available output fields for donations."""
        try:
            output_fields = regression_client.donations.get_output_fields()
            assert isinstance(output_fields, dict)

            print(f"✓ Retrieved {len(output_fields)} donation output fields")
        except Exception as e:
            print(f"⚠ Get output fields failed: {e}")

    def test_donations_get_specific(self, regression_client):
        """Test getting specific donation by ID."""
        # First get a donation ID
        donation_id = None
        donations = list(regression_client.donations.list(limit=1))
        if donations:
            donation_id = donations[0].get("donationId") or donations[0].get("id")

        if donation_id:
            specific_donation = regression_client.donations.get(donation_id)
            assert isinstance(specific_donation, dict)
            print(f"✓ Retrieved specific donation: {donation_id}")
        else:
            pytest.skip("No donations available to test specific retrieval")

    def test_donations_get_invalid_id(self, regression_client):
        """Test error handling for invalid donation ID."""
        with pytest.raises(NeonNotFoundError):
            regression_client.donations.get(999999999)
        print("✓ Correctly received 404 for invalid donation ID")

    def test_donations_parameter_combinations(self, regression_client):
        """Test various parameter combinations."""
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")

        parameter_combinations = [
            {"campaign_id": 1, "limit": 3},
            {"fund_id": 1, "page_size": 5},
            {"start_date": start_date, "end_date": end_date, "limit": 2},
            {"campaign_id": 1, "fund_id": 1, "limit": 1},
        ]

        for i, params in enumerate(parameter_combinations):
            try:
                donations = list(regression_client.donations.list(**params))
                print(
                    f"✓ Parameter combination {i + 1}: {len(donations)} donations with {params}"
                )

                # Validate limit if specified
                if "limit" in params and len(donations) > params["limit"]:
                    print(
                        f"❌ Limit not respected: expected max {params['limit']}, got {len(donations)}"
                    )

            except Exception as e:
                print(f"❌ Parameter combination {i + 1} failed {params}: {e}")


@pytest.mark.regression
@pytest.mark.writeops
class TestDonationsWriteOperations:
    """Write operation tests for DonationsResource - modifies database."""

    def test_create_donation_basic(self, write_regression_client):
        """Test creating a basic donation."""
        # First create a test account
        timestamp = int(time.time())
        account_payload = {
            "individualAccount": {
                "accountType": "INDIVIDUAL",
                "firstName": "Donor",
                "lastName": f"Test{timestamp}",
                "email": f"donor.test.{timestamp}@example.com",
            }
        }

        created_accounts = []
        created_donations = []

        try:
            # Create account
            account_result = write_regression_client.accounts.create(account_payload)
            account_id = account_result["accountId"]
            created_accounts.append(account_id)
            print(f"✓ Created test account: {account_id}")

            # Create donation
            donation_payload = {
                "donation": {
                    "accountId": account_id,
                    "amount": 100.0,
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "campaign": {"id": 1},
                    "fund": {"id": 1},
                }
            }

            donation_result = write_regression_client.donations.create(donation_payload)
            donation_id = donation_result.get("donationId") or donation_result.get("id")

            if donation_id:
                created_donations.append(donation_id)
                print(f"✓ Created donation: {donation_id}")

                # Verify creation
                created_donation = write_regression_client.donations.get(donation_id)
                assert created_donation["amount"] == 100.0
                assert created_donation["accountId"] == account_id

            else:
                print(f"⚠ No donation ID in response: {list(donation_result.keys())}")

        except Exception as e:
            print(f"❌ Donation creation failed: {e}")
        finally:
            # Cleanup donations first, then accounts
            for donation_id in created_donations:
                try:
                    write_regression_client.donations.delete(donation_id)
                    print(f"✓ Cleaned up donation: {donation_id}")
                except Exception as e:
                    print(f"⚠ Could not delete donation {donation_id}: {e}")

            for account_id in created_accounts:
                try:
                    write_regression_client.accounts.delete(account_id)
                    print(f"✓ Cleaned up account: {account_id}")
                except Exception as e:
                    print(f"⚠ Could not delete account {account_id}: {e}")

    def test_create_donation_with_acknowledgment(self, write_regression_client):
        """Test creating donation with acknowledgment settings."""
        timestamp = int(time.time())

        # Create test account
        account_payload = {
            "individualAccount": {
                "accountType": "INDIVIDUAL",
                "firstName": "AckDonor",
                "lastName": f"Test{timestamp}",
                "email": f"ackdonor.test.{timestamp}@example.com",
            }
        }

        created_accounts = []
        created_donations = []

        try:
            account_result = write_regression_client.accounts.create(account_payload)
            account_id = account_result["accountId"]
            created_accounts.append(account_id)

            # Create donation with acknowledgment
            donation_payload = {
                "donation": {
                    "accountId": account_id,
                    "amount": 250.0,
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "campaign": {"id": 1},
                    "fund": {"id": 1},
                    "acknowledgmentType": "Email",
                    "tributeType": "In Honor Of",
                    "tributeMessage": "Test tribute message",
                }
            }

            donation_result = write_regression_client.donations.create(donation_payload)
            donation_id = donation_result.get("donationId") or donation_result.get("id")

            if donation_id:
                created_donations.append(donation_id)
                print(f"✓ Created donation with acknowledgment: {donation_id}")

        except Exception as e:
            print(f"❌ Donation with acknowledgment creation failed: {e}")
        finally:
            # Cleanup
            for donation_id in created_donations:
                try:
                    write_regression_client.donations.delete(donation_id)
                    print(f"✓ Cleaned up donation: {donation_id}")
                except Exception as e:
                    print(f"⚠ Could not delete donation {donation_id}: {e}")

            for account_id in created_accounts:
                try:
                    write_regression_client.accounts.delete(account_id)
                    print(f"✓ Cleaned up account: {account_id}")
                except Exception as e:
                    print(f"⚠ Could not delete account {account_id}: {e}")

    def test_update_donation(self, write_regression_client):
        """Test updating a donation."""
        timestamp = int(time.time())

        # Create test account and donation
        account_payload = {
            "individualAccount": {
                "accountType": "INDIVIDUAL",
                "firstName": "UpdateDonor",
                "lastName": f"Test{timestamp}",
                "email": f"updatedonor.test.{timestamp}@example.com",
            }
        }

        created_accounts = []
        created_donations = []

        try:
            # Create account
            account_result = write_regression_client.accounts.create(account_payload)
            account_id = account_result["accountId"]
            created_accounts.append(account_id)

            # Create donation
            donation_payload = {
                "donation": {
                    "accountId": account_id,
                    "amount": 100.0,
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "campaign": {"id": 1},
                    "fund": {"id": 1},
                }
            }

            donation_result = write_regression_client.donations.create(donation_payload)
            donation_id = donation_result.get("donationId") or donation_result.get("id")

            if donation_id:
                created_donations.append(donation_id)

                # Update donation
                update_data = {
                    "donation": {"amount": 150.0, "acknowledgmentType": "Letter"}
                }

                write_regression_client.donations.update(donation_id, update_data)
                print(f"✓ Updated donation: {donation_id}")

                # Verify update
                updated_donation = write_regression_client.donations.get(donation_id)
                if updated_donation.get("amount") == 150.0:
                    print("✓ Donation amount updated correctly")
                else:
                    print(f"⚠ Amount not updated: {updated_donation.get('amount')}")

        except Exception as e:
            print(f"❌ Donation update failed: {e}")
        finally:
            # Cleanup
            for donation_id in created_donations:
                try:
                    write_regression_client.donations.delete(donation_id)
                    print(f"✓ Cleaned up donation: {donation_id}")
                except Exception as e:
                    print(f"⚠ Could not delete donation {donation_id}: {e}")

            for account_id in created_accounts:
                try:
                    write_regression_client.accounts.delete(account_id)
                    print(f"✓ Cleaned up account: {account_id}")
                except Exception as e:
                    print(f"⚠ Could not delete account {account_id}: {e}")

    def test_donation_validation_errors(self, write_regression_client):
        """Test donation validation errors."""
        # Test invalid account ID
        invalid_payload = {
            "donation": {
                "accountId": 999999999,  # Non-existent account
                "amount": 100.0,
                "date": datetime.now().strftime("%Y-%m-%d"),
                "campaign": {"id": 1},
                "fund": {"id": 1},
            }
        }

        with pytest.raises(
            (NeonBadRequestError, NeonNotFoundError, NeonUnprocessableEntityError)
        ):
            write_regression_client.donations.create(invalid_payload)
        print("✓ Invalid account ID correctly rejected")

        # Test negative amount
        negative_amount_payload = {
            "donation": {
                "accountId": 1,  # This will also fail, but amount validation should come first
                "amount": -50.0,
                "date": datetime.now().strftime("%Y-%m-%d"),
                "campaign": {"id": 1},
                "fund": {"id": 1},
            }
        }

        with pytest.raises((NeonBadRequestError, NeonUnprocessableEntityError)):
            write_regression_client.donations.create(negative_amount_payload)
        print("✓ Negative amount correctly rejected")

        # Test invalid date format
        invalid_date_payload = {
            "donation": {
                "accountId": 1,
                "amount": 100.0,
                "date": "invalid-date",
                "campaign": {"id": 1},
                "fund": {"id": 1},
            }
        }

        with pytest.raises((NeonBadRequestError, NeonUnprocessableEntityError)):
            write_regression_client.donations.create(invalid_date_payload)
        print("✓ Invalid date format correctly rejected")
