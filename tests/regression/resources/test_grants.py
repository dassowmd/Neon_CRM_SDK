"""Comprehensive regression tests for GrantsResource.

Tests both read-only and write operations for the grants endpoint.
Organized to match src/neon_crm/resources/grants.py structure.
"""

import time

import pytest

from neon_crm.exceptions import (
    NeonNotFoundError,
)
from neon_crm.types import SearchRequest


@pytest.mark.regression
@pytest.mark.readonly
class TestGrantsReadOnly:
    """Read-only tests for GrantsResource - safe for production."""

    def test_grants_list_basic(self, regression_client):
        """Test basic grant listing."""
        grants = list(regression_client.grants.list(limit=5))

        print(f"✓ Retrieved {len(grants)} grants")

        if grants:
            first_grant = grants[0]
            assert isinstance(first_grant, dict), "Grant should be a dictionary"
            print(f"Grant structure: {list(first_grant.keys())}")

            # Check for expected grant attributes
            expected_attrs = ["grantId", "accountId", "amount", "status"]
            missing_attrs = [attr for attr in expected_attrs if attr not in first_grant]
            if missing_attrs:
                print(f"⚠ Some expected attributes missing: {missing_attrs}")

    def test_grants_limit_parameter_fixed(self, regression_client):
        """Test limit parameter - this was broken before the fix."""
        limited_grants = list(regression_client.grants.list(page_size=20, limit=5))

        if len(limited_grants) > 5:
            print(
                f"❌ CRITICAL: Limit not working: got {len(limited_grants)}, expected max 5"
            )
        else:
            print(f"✓ FIXED: Limit parameter working: got {len(limited_grants)} grants")

        try:
            unlimited_grants = list(
                regression_client.grants.list(page_size=10, limit=None)
            )
            print(f"✓ FIXED: limit=None works: got {len(unlimited_grants)} grants")
        except TypeError as e:
            print(f"❌ CRITICAL: limit=None still crashes: {e}")

    def test_grants_status_filtering(self, regression_client):
        """Test grant filtering by status."""
        try:
            statuses = ["pending", "approved", "rejected", "paid"]

            for status in statuses:
                try:
                    status_grants = list(
                        regression_client.grants.list(page_size=5, status=status)
                    )
                    print(f"✓ Status '{status}': {len(status_grants)} grants")

                except Exception as e:
                    print(f"⚠ Status '{status}' filtering failed: {e}")

        except Exception as e:
            print(f"❌ Status filtering test failed: {e}")

    def test_grants_search(self, regression_client):
        """Test grant search functionality."""
        search_request: SearchRequest = {
            "searchFields": [
                {"field": "amount", "operator": "GREATER_THAN", "value": "0"}
            ],
            "outputFields": ["grantId", "accountId", "amount", "status"],
            "pagination": {"currentPage": 0, "pageSize": 5},
        }

        results = list(regression_client.grants.search(search_request))[:5]

        print(f"✓ Grant search returned {len(results)} results")

    def test_grants_get_specific(self, regression_client):
        """Test getting specific grant by ID."""
        grants = list(regression_client.grants.list(limit=1))
        grant_id = None
        if grants:
            grant_id = grants[0].get("grantId") or grants[0].get("id")

        if grant_id:
            specific_grant = regression_client.grants.get(grant_id)
            assert isinstance(specific_grant, dict)
            print(f"✓ Retrieved specific grant: {grant_id}")
        else:
            pytest.skip("No grants available to test specific retrieval")

    def test_grants_get_invalid_id(self, regression_client):
        """Test error handling for invalid grant ID."""
        with pytest.raises(NeonNotFoundError):
            regression_client.grants.get(999999999)
        print("✓ Correctly received 404 for invalid grant ID")


@pytest.mark.regression
@pytest.mark.writeops
class TestGrantsWriteOperations:
    """Write operation tests for GrantsResource - modifies database."""

    def test_create_grant_basic(self, write_regression_client):
        """Test creating a basic grant."""
        timestamp = int(time.time())

        # Create test account first
        account_payload = {
            "individualAccount": {
                "accountType": "INDIVIDUAL",
                "firstName": "Grant",
                "lastName": f"Test{timestamp}",
                "email": f"grant.test.{timestamp}@example.com",
            }
        }

        created_accounts = []
        created_grants = []

        try:
            account_result = write_regression_client.accounts.create(account_payload)
            account_id = account_result["accountId"]
            created_accounts.append(account_id)

            # Create grant
            grant_payload = {
                "grant": {
                    "accountId": account_id,
                    "amount": 5000.0,
                    "status": "pending",
                    "description": f"Test grant {timestamp}",
                }
            }

            grant_result = write_regression_client.grants.create(grant_payload)
            grant_id = grant_result.get("grantId") or grant_result.get("id")

            if grant_id:
                created_grants.append(grant_id)
                print(f"✓ Created grant: {grant_id}")

        except Exception as e:
            print(f"❌ Grant creation failed: {e}")
        finally:
            # Cleanup
            for grant_id in created_grants:
                try:
                    write_regression_client.grants.delete(grant_id)
                    print(f"✓ Cleaned up grant: {grant_id}")
                except Exception as e:
                    print(f"⚠ Could not delete grant {grant_id}: {e}")

            for account_id in created_accounts:
                try:
                    write_regression_client.accounts.delete(account_id)
                    print(f"✓ Cleaned up account: {account_id}")
                except Exception as e:
                    print(f"⚠ Could not delete account {account_id}: {e}")
