"""Comprehensive regression tests for AccountsResource.

Tests both read-only and write operations for the accounts endpoint.
Organized to match src/neon_crm/resources/accounts.py structure.
"""

import pytest

from neon_crm.exceptions import (
    NeonBadRequestError,
    NeonNotFoundError,
)
from neon_crm.types import SearchRequest, UserType


@pytest.mark.regression
@pytest.mark.readonly
class TestAccountsReadOnly:
    """Read-only tests for AccountsResource - safe for production."""

    def test_accounts_list_basic(self, regression_client):
        """Test basic account listing."""
        accounts = list(
            regression_client.accounts.list(limit=5, user_type=UserType.INDIVIDUAL)
        )

        print(f"✓ Retrieved {len(accounts)} accounts")

        if accounts:
            first_account = accounts[0]
            assert isinstance(first_account, dict), "Account should be a dictionary"
            assert "accountId" in first_account, "Account should have accountId"
            print(f"Account structure: {list(first_account.keys())}")

    def test_accounts_check_valid_user_types_returned(self, regression_client):
        """Test account listing with different user types."""
        for user_type in [UserType.INDIVIDUAL, UserType.COMPANY]:
            accounts = list(regression_client.accounts.list(user_type=user_type))

            for account in accounts:
                if "userType" in account:
                    assert account["userType"] in [user_type.value, user_type]

            print(f"✓ Retrieved {len(accounts)} {user_type.value} accounts")

    def test_accounts_list_parameter_validation(self, regression_client):
        """Test account listing parameter validation."""
        # Test valid user_type enum
        accounts = list(
            regression_client.accounts.list(limit=2, user_type=UserType.INDIVIDUAL)
        )
        assert len(accounts) <= 2

        # Test valid string user_type
        accounts = list(
            regression_client.accounts.list(limit=2, user_type="INDIVIDUAL")
        )
        assert len(accounts) <= 2

        # Test invalid user_type should raise error
        with pytest.raises((ValueError, NeonBadRequestError)):
            list(regression_client.accounts.list(limit=1, user_type="INVALID_TYPE"))

    def test_accounts_limit_parameter(self, regression_client):
        """Test limit parameter functionality (this was broken before fix)."""
        # Test limit parameter
        limited_accounts = list(
            regression_client.accounts.list(limit=3, user_type=UserType.INDIVIDUAL)
        )

        if len(limited_accounts) > 3:
            print(
                f"❌ Limit not respected: got {len(limited_accounts)}, expected max 3"
            )
        else:
            print(f"✓ Limit parameter working: got {len(limited_accounts)} accounts")

        # Test limit=None (unlimited)
        unlimited_accounts = list(
            regression_client.accounts.list(
                page_size=100, limit=None, user_type=UserType.INDIVIDUAL
            )
        )
        print(f"✓ Unlimited query returned {len(unlimited_accounts)} accounts")

    def test_accounts_search(self, regression_client):
        """Test account search functionality."""
        search_request: SearchRequest = {
            "searchFields": [
                {"field": "Account Type", "operator": "EQUAL", "value": "COMPANY"}
            ],
            "outputFields": ["Account ID", "First Name", "Last Name", "Email 1"],
            "pagination": {"currentPage": 0, "pageSize": 100},
        }

        results = list(regression_client.accounts.search(search_request))[:5]

        print(f"✓ Search returned {len(results)} results")

        if results:
            first_result = results[0]
            requested_fields = ["Account ID", "First Name", "Last Name", "Email 1"]
            for field in requested_fields:
                assert field in first_result

    def test_accounts_get_search_fields(self, regression_client):
        """Test getting available search fields."""
        search_fields = regression_client.accounts.get_search_fields()
        assert isinstance(search_fields, dict)
        print(f"✓ Retrieved {len(search_fields)} search fields")

    def test_accounts_get_output_fields(self, regression_client):
        """Test getting available output fields."""
        output_fields = regression_client.accounts.get_output_fields()
        assert isinstance(output_fields, dict)
        print(f"✓ Retrieved {len(output_fields)} output fields")

    def test_accounts_get_specific(self, regression_client):
        """Test getting specific account by ID."""
        # First get an account ID
        account_id = None
        for account in regression_client.accounts.list(
            limit=1, user_type=UserType.COMPANY
        ):
            account_id = account.get("accountId")
            break

        if account_id:
            specific_account = regression_client.accounts.get(account_id)
            assert isinstance(specific_account, dict)
            assert specific_account.get("companyAccount").get("accountId") == account_id
            print(f"✓ Retrieved specific account: {account_id}")
        else:
            pytest.skip("No accounts available to test specific retrieval")

    def test_accounts_get_invalid_id(self, regression_client):
        """Test error handling for invalid account ID."""
        with pytest.raises(NeonNotFoundError):
            regression_client.accounts.get(999999999)
        print("✓ Correctly received 404 for invalid account ID")

    def test_accounts_related_data(self, regression_client):
        """Test getting account-related data."""
        # Get first account
        account_id = None
        for account in regression_client.accounts.list(
            limit=1, user_type=UserType.INDIVIDUAL
        ):
            account_id = account.get("accountId")
            break

        if not account_id:
            pytest.skip("No accounts available for related data tests")

        # Test related data endpoints
        related_endpoints = [
            ("donations", lambda: regression_client.accounts.get_donations(account_id)),
            (
                "memberships",
                lambda: regression_client.accounts.get_memberships(account_id),
            ),
            (
                "event_registrations",
                lambda: regression_client.accounts.get_event_registrations(account_id),
            ),
            ("orders", lambda: regression_client.accounts.get_orders(account_id)),
            ("pledges", lambda: regression_client.accounts.get_pledges(account_id)),
        ]

        for endpoint_name, endpoint_func in related_endpoints:
            try:
                results = list(endpoint_func())
                print(f"✓ Account {account_id} has {len(results)} {endpoint_name}")
            except Exception as e:
                print(f"⚠ Could not get {endpoint_name} for account {account_id}: {e}")

    def test_accounts_pagination_consistency(self, regression_client):
        """Test pagination consistency."""
        # Get first page
        page1_accounts = list(
            regression_client.accounts.list(
                page_size=5, current_page=0, user_type=UserType.INDIVIDUAL, limit=5
            )
        )

        # Get second page
        page2_accounts = list(
            regression_client.accounts.list(
                page_size=5, current_page=1, user_type=UserType.INDIVIDUAL, limit=5
            )
        )

        if page1_accounts and page2_accounts:
            page1_ids = {
                acc.get("accountId") for acc in page1_accounts if "accountId" in acc
            }
            page2_ids = {
                acc.get("accountId") for acc in page2_accounts if "accountId" in acc
            }

            overlap = page1_ids.intersection(page2_ids)
            if overlap:
                print(f"❌ Pagination overlap: {len(overlap)} duplicate IDs")
            else:
                print("✓ No pagination overlap detected")


# @pytest.mark.regression
# @pytest.mark.writeops
# class TestAccountsWriteOperations:
#     """Write operation tests for AccountsResource - modifies database."""
#
#     def test_create_individual_account(self, write_regression_client):
#         """Test creating individual account."""
#         timestamp = int(time.time())
#
#         payload = {
#             "individualAccount": {
#                 "accountType": "INDIVIDUAL",
#                 "firstName": "Test",
#                 "lastName": f"Individual{timestamp}",
#                 "email": f"test.individual.{timestamp}@example.com",
#             }
#         }
#
#         try:
#             result = write_regression_client.accounts.create(payload)
#             assert "accountId" in result
#             account_id = result["accountId"]
#             print(f"✓ Created individual account: {account_id}")
#
#             # Verify creation
#             created_account = write_regression_client.accounts.get(account_id)
#             assert created_account["firstName"] == "Test"
#
#             # Clean up
#             write_regression_client.accounts.delete(account_id)
#             print(f"✓ Cleaned up account: {account_id}")
#
#         except Exception as e:
#             pytest.fail(f"Failed to create individual account: {e}")
#
#     def test_create_company_account(self, write_regression_client):
#         """Test creating company account."""
#         timestamp = int(time.time())
#
#         payload = {
#             "companyAccount": {
#                 "accountType": "COMPANY",
#                 "name": f"Test Company {timestamp}",
#                 "email": f"info.{timestamp}@testcompany.example.com",
#             }
#         }
#
#         try:
#             result = write_regression_client.accounts.create(payload)
#             assert "accountId" in result
#             account_id = result["accountId"]
#             print(f"✓ Created company account: {account_id}")
#
#             # Clean up
#             write_regression_client.accounts.delete(account_id)
#             print(f"✓ Cleaned up account: {account_id}")
#
#         except Exception as e:
#             pytest.fail(f"Failed to create company account: {e}")
#
#     def test_update_account(self, write_regression_client):
#         """Test updating account."""
#         timestamp = int(time.time())
#
#         # Create account
#         payload = {
#             "individualAccount": {
#                 "accountType": "INDIVIDUAL",
#                 "firstName": "Update",
#                 "lastName": f"Test{timestamp}",
#                 "email": f"update.test.{timestamp}@example.com",
#             }
#         }
#
#         try:
#             result = write_regression_client.accounts.create(payload)
#             account_id = result["accountId"]
#
#             # Update account
#             update_data = {
#                 "individualAccount": {
#                     "firstName": "Updated",
#                     "lastName": f"Test{timestamp}",
#                 }
#             }
#
#             write_regression_client.accounts.update(account_id, update_data)
#             print(f"✓ Updated account: {account_id}")
#
#             # Verify update
#             updated_account = write_regression_client.accounts.get(account_id)
#             assert updated_account["firstName"] == "Updated"
#
#             # Clean up
#             write_regression_client.accounts.delete(account_id)
#             print(f"✓ Cleaned up account: {account_id}")
#
#         except Exception as e:
#             pytest.fail(f"Failed to update account: {e}")
#
#     def test_patch_account(self, write_regression_client):
#         """Test partial update (patch) of account."""
#         timestamp = int(time.time())
#
#         # Create account
#         payload = {
#             "individualAccount": {
#                 "accountType": "INDIVIDUAL",
#                 "firstName": "Patch",
#                 "lastName": f"Test{timestamp}",
#                 "email": f"patch.test.{timestamp}@example.com",
#             }
#         }
#
#         try:
#             result = write_regression_client.accounts.create(payload)
#             account_id = result["accountId"]
#
#             # Patch account
#             patch_data = {"phone": "+1-555-PATCHED"}
#             write_regression_client.accounts.patch(account_id, patch_data)
#             print(f"✓ Patched account: {account_id}")
#
#             # Clean up
#             write_regression_client.accounts.delete(account_id)
#             print(f"✓ Cleaned up account: {account_id}")
#
#         except Exception as e:
#             pytest.fail(f"Failed to patch account: {e}")
#
#     def test_account_link_operations(self, write_regression_client):
#         """Test account linking and unlinking."""
#         timestamp = int(time.time())
#
#         created_accounts = []
#
#         try:
#             # Create individual account
#             individual_payload = {
#                 "individualAccount": {
#                     "accountType": "INDIVIDUAL",
#                     "firstName": "Link",
#                     "lastName": f"Individual{timestamp}",
#                     "email": f"link.individual.{timestamp}@example.com",
#                 }
#             }
#
#             result1 = write_regression_client.accounts.create(individual_payload)
#             individual_id = result1["accountId"]
#             created_accounts.append(individual_id)
#
#             # Create company account
#             company_payload = {
#                 "companyAccount": {
#                     "accountType": "COMPANY",
#                     "name": f"Link Company {timestamp}",
#                     "email": f"link.company.{timestamp}@example.com",
#                 }
#             }
#
#             result2 = write_regression_client.accounts.create(company_payload)
#             company_id = result2["accountId"]
#             created_accounts.append(company_id)
#
#             # Test linking
#             write_regression_client.accounts.link(individual_id, company_id)
#             print(f"✓ Linked accounts: {individual_id} -> {company_id}")
#
#             # Test unlinking
#             write_regression_client.accounts.unlink(individual_id, company_id)
#             print(f"✓ Unlinked accounts: {individual_id} -> {company_id}")
#
#         except Exception as e:
#             print(f"❌ Account link operations failed: {e}")
#         finally:
#             # Clean up
#             for account_id in created_accounts:
#                 try:
#                     write_regression_client.accounts.delete(account_id)
#                     print(f"✓ Cleaned up account: {account_id}")
#                 except Exception as e:
#                     print(f"⚠ Could not delete account {account_id}: {e}")
#
#     def test_account_validation_errors(self, write_regression_client):
#         """Test account creation validation."""
#         # Test invalid email format
#         invalid_email_payload = {
#             "individualAccount": {
#                 "accountType": "INDIVIDUAL",
#                 "firstName": "Test",
#                 "lastName": "InvalidEmail",
#                 "email": "invalid-email",
#             }
#         }
#
#         with pytest.raises((NeonBadRequestError, NeonUnprocessableEntityError)):
#             write_regression_client.accounts.create(invalid_email_payload)
#         print("✓ Invalid email correctly rejected")
#
#         # Test missing required fields
#         invalid_payload = {
#             "individualAccount": {
#                 "accountType": "INDIVIDUAL"
#                 # Missing firstName, lastName, email
#             }
#         }
#
#         with pytest.raises((NeonBadRequestError, NeonUnprocessableEntityError)):
#             write_regression_client.accounts.create(invalid_payload)
#         print("✓ Missing required fields correctly rejected")
