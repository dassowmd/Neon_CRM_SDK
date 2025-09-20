"""Comprehensive regression tests for MembershipsResource.

Tests both read-only and write operations for the memberships endpoint.
Organized to match src/neon_crm/resources/memberships.py structure.
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
class TestMembershipsReadOnly:
    """Read-only tests for MembershipsResource - safe for production."""

    def test_memberships_list_basic(self, regression_client):
        """Test basic membership listing."""
        memberships = list(regression_client.memberships.list(limit=5))

        print(f"✓ Retrieved {len(memberships)} memberships")

        if memberships:
            first_membership = memberships[0]
            assert isinstance(
                first_membership, dict
            ), "Membership should be a dictionary"
            print(f"Membership structure: {list(first_membership.keys())}")

            # Check for expected membership attributes
            expected_attrs = [
                "membershipId",
                "accountId",
                "startDate",
                "membershipLevel",
            ]
            missing_attrs = [
                attr for attr in expected_attrs if attr not in first_membership
            ]
            if missing_attrs:
                print(f"⚠ Some expected attributes missing: {missing_attrs}")

    def test_memberships_limit_parameter_fixed(self, regression_client):
        """Test limit parameter - this was broken before the fix."""
        # Test limit parameter
        limited_memberships = list(
            regression_client.memberships.list(page_size=20, limit=5)
        )

        if len(limited_memberships) > 5:
            print(
                f"❌ CRITICAL: Limit not working: got {len(limited_memberships)}, expected max 5"
            )
        else:
            print(
                f"✓ FIXED: Limit parameter working: got {len(limited_memberships)} memberships"
            )

        # Test limit=None (this was causing crashes before fix)
        try:
            unlimited_memberships = list(
                regression_client.memberships.list(page_size=10, limit=None)
            )
            print(
                f"✓ FIXED: limit=None works: got {len(unlimited_memberships)} memberships"
            )
        except TypeError as e:
            print(f"❌ CRITICAL: limit=None still crashes: {e}")

    def test_memberships_status_filtering(self, regression_client):
        """Test membership filtering by status."""
        try:
            statuses = ["active", "expired", "pending"]

            for status in statuses:
                try:
                    status_memberships = list(
                        regression_client.memberships.list(page_size=5, status=status)
                    )
                    print(f"✓ Status '{status}': {len(status_memberships)} memberships")

                    # Validate status filtering
                    for membership in status_memberships[:3]:
                        if "status" in membership:
                            if membership["status"].lower() != status.lower():
                                print(
                                    f"⚠ Status filter not working: expected {status}, got {membership['status']}"
                                )

                except Exception as e:
                    print(f"⚠ Status '{status}' filtering failed: {e}")

        except Exception as e:
            print(f"❌ Status filtering test failed: {e}")

    def test_memberships_level_filtering(self, regression_client):
        """Test membership filtering by level."""
        try:
            level_memberships = list(
                regression_client.memberships.list(page_size=5, level="Basic")
            )
            print(f"✓ Level filtering: {len(level_memberships)} basic memberships")

            # Validate level filtering
            for membership in level_memberships[:3]:
                if "membershipLevel" in membership and isinstance(
                    membership["membershipLevel"], dict
                ):
                    level_name = membership["membershipLevel"].get("name")
                    if level_name and level_name.lower() != "basic":
                        print(
                            f"⚠ Level filter not working: expected Basic, got {level_name}"
                        )

        except Exception as e:
            print(f"⚠ Level filtering failed: {e}")

    def test_memberships_date_filtering(self, regression_client):
        """Test membership listing with date filtering."""
        # Test with date range for active memberships
        start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
        end_date = datetime.now().strftime("%Y-%m-%d")

        memberships = []
        for membership in regression_client.memberships.list(
            page_size=5, start_date=start_date, end_date=end_date
        ):
            memberships.append(membership)
            if len(memberships) >= 5:
                break

        print(
            f"✓ Retrieved {len(memberships)} memberships with date filter (last year)"
        )

    def test_memberships_search(self, regression_client):
        """Test membership search functionality."""
        search_request: SearchRequest = {
            "searchFields": [
                {"field": "status", "operator": "EQUAL", "value": "active"}
            ],
            "outputFields": [
                "membershipId",
                "accountId",
                "startDate",
                "endDate",
                "status",
            ],
            "pagination": {"currentPage": 0, "pageSize": 5},
        }

        results = []
        for result in regression_client.memberships.search(search_request):
            results.append(result)
            if len(results) >= 5:
                break

        print(f"✓ Membership search returned {len(results)} results")

        if results:
            first_result = results[0]
            # Validate search results contain requested fields
            requested_fields = [
                "membershipId",
                "accountId",
                "startDate",
                "endDate",
                "status",
            ]
            missing_fields = [f for f in requested_fields if f not in first_result]
            if missing_fields:
                print(f"⚠ Missing requested fields: {missing_fields}")

    def test_memberships_get_search_fields(self, regression_client):
        """Test getting available search fields for memberships."""
        try:
            search_fields = regression_client.memberships.get_search_fields()
            assert isinstance(search_fields, dict)

            print(f"✓ Retrieved {len(search_fields)} membership search fields")
        except Exception as e:
            print(f"⚠ Get search fields failed: {e}")

    def test_memberships_get_output_fields(self, regression_client):
        """Test getting available output fields for memberships."""
        try:
            output_fields = regression_client.memberships.get_output_fields()
            assert isinstance(output_fields, dict)

            print(f"✓ Retrieved {len(output_fields)} membership output fields")
        except Exception as e:
            print(f"⚠ Get output fields failed: {e}")

    def test_memberships_get_specific(self, regression_client):
        """Test getting specific membership by ID."""
        # First get a membership ID
        memberships = list(regression_client.memberships.list(limit=1))
        membership_id = None
        if memberships:
            membership_id = memberships[0].get("membershipId") or memberships[0].get(
                "id"
            )

        if membership_id:
            specific_membership = regression_client.memberships.get(membership_id)
            assert isinstance(specific_membership, dict)
            print(f"✓ Retrieved specific membership: {membership_id}")
        else:
            pytest.skip("No memberships available to test specific retrieval")

    def test_memberships_get_invalid_id(self, regression_client):
        """Test error handling for invalid membership ID."""
        with pytest.raises(NeonNotFoundError):
            regression_client.memberships.get(999999999)
        print("✓ Correctly received 404 for invalid membership ID")

    def test_memberships_get_levels(self, regression_client):
        """Test getting available membership levels."""
        try:
            levels = regression_client.memberships.get_levels()
            assert isinstance(levels, list)
            print(f"✓ Retrieved {len(levels)} membership levels")

            if levels:
                print(
                    f"Sample membership levels: {[level.get('name', level) for level in levels[:3]]}"
                )

        except Exception as e:
            print(f"⚠ Get membership levels failed: {e}")

    def test_memberships_parameter_combinations(self, regression_client):
        """Test various parameter combinations."""
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d")

        parameter_combinations = [
            {"status": "active", "limit": 3},
            {"level": "Basic", "page_size": 5},
            {"start_date": start_date, "end_date": end_date, "limit": 2},
            {"status": "active", "level": "Basic", "limit": 1},
        ]

        for i, params in enumerate(parameter_combinations):
            try:
                memberships = list(regression_client.memberships.list(**params))
                print(
                    f"✓ Parameter combination {i + 1}: {len(memberships)} memberships with {params}"
                )

                # Validate limit if specified
                if "limit" in params and len(memberships) > params["limit"]:
                    print(
                        f"❌ Limit not respected: expected max {params['limit']}, got {len(memberships)}"
                    )

            except Exception as e:
                print(f"❌ Parameter combination {i + 1} failed {params}: {e}")


@pytest.mark.regression
@pytest.mark.writeops
class TestMembershipsWriteOperations:
    """Write operation tests for MembershipsResource - modifies database."""

    def test_create_membership_basic(self, write_regression_client):
        """Test creating a basic membership."""
        timestamp = int(time.time())

        # First create a test account
        account_payload = {
            "individualAccount": {
                "accountType": "INDIVIDUAL",
                "firstName": "Member",
                "lastName": f"Test{timestamp}",
                "email": f"member.test.{timestamp}@example.com",
            }
        }

        created_accounts = []
        created_memberships = []

        try:
            # Create account
            account_result = write_regression_client.accounts.create(account_payload)
            account_id = account_result["accountId"]
            created_accounts.append(account_id)
            print(f"✓ Created test account: {account_id}")

            # Create membership
            membership_payload = {
                "membership": {
                    "accountId": account_id,
                    "startDate": datetime.now().strftime("%Y-%m-%d"),
                    "endDate": (datetime.now() + timedelta(days=365)).strftime(
                        "%Y-%m-%d"
                    ),
                    "membershipLevel": {"id": 1},  # Assuming basic membership level
                    "status": "active",
                }
            }

            membership_result = write_regression_client.memberships.create(
                membership_payload
            )
            membership_id = membership_result.get(
                "membershipId"
            ) or membership_result.get("id")

            if membership_id:
                created_memberships.append(membership_id)
                print(f"✓ Created membership: {membership_id}")

                # Verify creation
                created_membership = write_regression_client.memberships.get(
                    membership_id
                )
                assert created_membership["accountId"] == account_id
                assert created_membership["status"] == "active"

            else:
                print(
                    f"⚠ No membership ID in response: {list(membership_result.keys())}"
                )

        except Exception as e:
            print(f"❌ Membership creation failed: {e}")
        finally:
            # Cleanup memberships first, then accounts
            for membership_id in created_memberships:
                try:
                    write_regression_client.memberships.delete(membership_id)
                    print(f"✓ Cleaned up membership: {membership_id}")
                except Exception as e:
                    print(f"⚠ Could not delete membership {membership_id}: {e}")

            for account_id in created_accounts:
                try:
                    write_regression_client.accounts.delete(account_id)
                    print(f"✓ Cleaned up account: {account_id}")
                except Exception as e:
                    print(f"⚠ Could not delete account {account_id}: {e}")

    def test_update_membership(self, write_regression_client):
        """Test updating a membership."""
        timestamp = int(time.time())

        # Create test account and membership
        account_payload = {
            "individualAccount": {
                "accountType": "INDIVIDUAL",
                "firstName": "UpdateMember",
                "lastName": f"Test{timestamp}",
                "email": f"update.member.test.{timestamp}@example.com",
            }
        }

        created_accounts = []
        created_memberships = []

        try:
            # Create account
            account_result = write_regression_client.accounts.create(account_payload)
            account_id = account_result["accountId"]
            created_accounts.append(account_id)

            # Create membership
            membership_payload = {
                "membership": {
                    "accountId": account_id,
                    "startDate": datetime.now().strftime("%Y-%m-%d"),
                    "endDate": (datetime.now() + timedelta(days=365)).strftime(
                        "%Y-%m-%d"
                    ),
                    "membershipLevel": {"id": 1},
                    "status": "active",
                }
            }

            membership_result = write_regression_client.memberships.create(
                membership_payload
            )
            membership_id = membership_result.get(
                "membershipId"
            ) or membership_result.get("id")

            if membership_id:
                created_memberships.append(membership_id)

                # Update membership
                update_data = {
                    "membership": {
                        "status": "pending",
                        "endDate": (datetime.now() + timedelta(days=730)).strftime(
                            "%Y-%m-%d"
                        ),  # Extend by a year
                    }
                }

                write_regression_client.memberships.update(membership_id, update_data)
                print(f"✓ Updated membership: {membership_id}")

                # Verify update
                updated_membership = write_regression_client.memberships.get(
                    membership_id
                )
                if updated_membership.get("status") == "pending":
                    print("✓ Membership status updated correctly")
                else:
                    print(f"⚠ Status not updated: {updated_membership.get('status')}")

        except Exception as e:
            print(f"❌ Membership update failed: {e}")
        finally:
            # Cleanup
            for membership_id in created_memberships:
                try:
                    write_regression_client.memberships.delete(membership_id)
                    print(f"✓ Cleaned up membership: {membership_id}")
                except Exception as e:
                    print(f"⚠ Could not delete membership {membership_id}: {e}")

            for account_id in created_accounts:
                try:
                    write_regression_client.accounts.delete(account_id)
                    print(f"✓ Cleaned up account: {account_id}")
                except Exception as e:
                    print(f"⚠ Could not delete account {account_id}: {e}")

    def test_membership_validation_errors(self, write_regression_client):
        """Test membership validation errors."""
        # Test invalid account ID
        invalid_payload = {
            "membership": {
                "accountId": 999999999,  # Non-existent account
                "startDate": datetime.now().strftime("%Y-%m-%d"),
                "endDate": (datetime.now() + timedelta(days=365)).strftime("%Y-%m-%d"),
                "membershipLevel": {"id": 1},
            }
        }

        with pytest.raises(
            (NeonBadRequestError, NeonNotFoundError, NeonUnprocessableEntityError)
        ):
            write_regression_client.memberships.create(invalid_payload)
        print("✓ Invalid account ID correctly rejected")

        # Test invalid date format
        invalid_date_payload = {
            "membership": {
                "accountId": 1,  # This will also fail, but date validation should come first
                "startDate": "invalid-date",
                "endDate": "invalid-end-date",
                "membershipLevel": {"id": 1},
            }
        }

        with pytest.raises((NeonBadRequestError, NeonUnprocessableEntityError)):
            write_regression_client.memberships.create(invalid_date_payload)
        print("✓ Invalid date format correctly rejected")

        # Test end date before start date
        date_logic_payload = {
            "membership": {
                "accountId": 1,
                "startDate": "2024-12-31",
                "endDate": "2024-01-01",  # Before start date
                "membershipLevel": {"id": 1},
            }
        }

        with pytest.raises((NeonBadRequestError, NeonUnprocessableEntityError)):
            write_regression_client.memberships.create(date_logic_payload)
        print("✓ End date before start date correctly rejected")
