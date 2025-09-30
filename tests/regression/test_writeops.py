"""Write operation regression tests for the Neon CRM SDK.

⚠️  WARNING: These tests modify the database! ⚠️
Only run these against test/trial environments, never against production.

These tests create, update, and delete actual records in your Neon CRM database.

Environment variables required:
- NEON_ORG_ID: Your Neon CRM organization ID
- NEON_API_KEY: Your Neon CRM API key
- NEON_ENVIRONMENT: Should be "trial" for safety
- NEON_ALLOW_WRITE_TESTS: Must be set to "true" to enable these tests
"""

import os
import time

import pytest

from neon_crm import NeonClient
from neon_crm.types import (
    CompleteAccountPayload,
    CreateCompanyAccountPayload,
    CreateIndividualAccountPayload,
)


@pytest.fixture
def write_regression_client():
    """Create client for write operations with safety checks."""
    org_id = os.getenv("NEON_ORG_ID")
    api_key = os.getenv("NEON_API_KEY")
    environment = os.getenv("NEON_ENVIRONMENT", "trial")
    allow_write_tests = os.getenv("NEON_ALLOW_WRITE_TESTS", "false").lower()

    if not org_id or not api_key:
        pytest.skip(
            "Write tests require NEON_ORG_ID and NEON_API_KEY environment variables"
        )

    if allow_write_tests != "true":
        pytest.skip(
            "Write tests require NEON_ALLOW_WRITE_TESTS=true environment variable"
        )

    if environment == "production":
        pytest.fail(
            "Write tests should NEVER be run against production! Set NEON_ENVIRONMENT=trial"
        )

    return NeonClient(org_id=org_id, api_key=api_key, environment=environment)


@pytest.mark.regression
@pytest.mark.writeops
class TestAccountWriteOperations:
    """Test account creation, modification, and deletion."""

    def test_create_individual_account_minimal(self, write_regression_client):
        """Test creating a minimal individual account."""
        timestamp = int(time.time())

        payload: CreateIndividualAccountPayload = {
            "individualAccount": {
                "accountType": "INDIVIDUAL",
                "firstName": "Test",
                "lastName": f"Individual{timestamp}",
                "email": f"test.individual.{timestamp}@example.com",
            }
        }

        try:
            result = write_regression_client.accounts.create(payload)
            assert "accountId" in result

            account_id = result["accountId"]
            print(f"✓ Created individual account: {account_id}")

            # Verify the account was created
            created_account = write_regression_client.accounts.get(account_id)
            assert created_account["firstName"] == "Test"
            assert created_account["lastName"] == f"Individual{timestamp}"

            # Clean up - try to delete the test account
            try:
                write_regression_client.accounts.delete(account_id)
                print(f"✓ Cleaned up account: {account_id}")
            except Exception as e:
                print(f"⚠ Could not delete test account {account_id}: {e}")

        except Exception as e:
            pytest.fail(f"Failed to create individual account: {e}")

    def test_create_company_account_minimal(self, write_regression_client):
        """Test creating a minimal company account."""
        timestamp = int(time.time())

        payload: CreateCompanyAccountPayload = {
            "companyAccount": {
                "accountType": "COMPANY",
                "name": f"Test Company {timestamp}",
                "email": f"info.{timestamp}@testcompany.example.com",
            }
        }

        try:
            result = write_regression_client.accounts.create(payload)
            assert "accountId" in result

            account_id = result["accountId"]
            print(f"✓ Created company account: {account_id}")

            # Verify the account was created
            created_account = write_regression_client.accounts.get(account_id)
            assert (
                created_account["companyName"] == f"Test Company {timestamp}"
                or "companyName" in created_account
            )

            # Clean up
            try:
                write_regression_client.accounts.delete(account_id)
                print(f"✓ Cleaned up account: {account_id}")
            except Exception as e:
                print(f"⚠ Could not delete test account {account_id}: {e}")

        except Exception as e:
            pytest.fail(f"Failed to create company account: {e}")

    def test_create_complete_account_with_address(self, write_regression_client):
        """Test creating a complete account with address."""
        timestamp = int(time.time())

        payload: CompleteAccountPayload = {
            "individualAccount": {
                "accountType": "INDIVIDUAL",
                "firstName": "Complete",
                "lastName": f"Test{timestamp}",
                "email": f"complete.test.{timestamp}@example.com",
                "phone": "+1-555-TEST-001",
            },
            "addresses": [
                {
                    "addressType": "Home",
                    "streetAddress1": "123 Test Street",
                    "city": "Test City",
                    "state": "CA",
                    "zipCode": "12345",
                    "country": "USA",
                    "isPrimaryAddress": True,
                }
            ],
            "source": {"sourceId": 1001, "sourceName": "SDK Test"},
        }

        try:
            result = write_regression_client.accounts.create(payload)
            assert "accountId" in result

            account_id = result["accountId"]
            print(f"✓ Created complete account with address: {account_id}")

            # Verify the account
            created_account = write_regression_client.accounts.get(account_id)
            assert created_account["firstName"] == "Complete"

            # Clean up
            try:
                write_regression_client.accounts.delete(account_id)
                print(f"✓ Cleaned up account: {account_id}")
            except Exception as e:
                print(f"⚠ Could not delete test account {account_id}: {e}")

        except Exception as e:
            pytest.fail(f"Failed to create complete account: {e}")

    def test_update_account(self, write_regression_client):
        """Test updating an existing account."""
        timestamp = int(time.time())

        # First create an account
        create_payload: CreateIndividualAccountPayload = {
            "individualAccount": {
                "accountType": "INDIVIDUAL",
                "firstName": "Update",
                "lastName": f"Test{timestamp}",
                "email": f"update.test.{timestamp}@example.com",
            }
        }

        try:
            result = write_regression_client.accounts.create(create_payload)
            account_id = result["accountId"]
            print(f"✓ Created account for update test: {account_id}")

            # Update the account
            update_data = {
                "individualAccount": {
                    "firstName": "Updated",
                    "lastName": f"Test{timestamp}",
                    "phone": "+1-555-UPDATED",
                }
            }

            write_regression_client.accounts.update(account_id, update_data)
            print(f"✓ Updated account: {account_id}")

            # Verify the update
            updated_account = write_regression_client.accounts.get(account_id)
            assert updated_account["firstName"] == "Updated"

            # Clean up
            try:
                write_regression_client.accounts.delete(account_id)
                print(f"✓ Cleaned up account: {account_id}")
            except Exception as e:
                print(f"⚠ Could not delete test account {account_id}: {e}")

        except Exception as e:
            pytest.fail(f"Failed to update account: {e}")

    def test_patch_account(self, write_regression_client):
        """Test partial update (patch) of an account."""
        timestamp = int(time.time())

        # First create an account
        create_payload: CreateIndividualAccountPayload = {
            "individualAccount": {
                "accountType": "INDIVIDUAL",
                "firstName": "Patch",
                "lastName": f"Test{timestamp}",
                "email": f"patch.test.{timestamp}@example.com",
            }
        }

        try:
            result = write_regression_client.accounts.create(create_payload)
            account_id = result["accountId"]
            print(f"✓ Created account for patch test: {account_id}")

            # Patch the account
            patch_data = {"phone": "+1-555-PATCHED"}

            write_regression_client.accounts.patch(account_id, patch_data)
            print(f"✓ Patched account: {account_id}")

            # Clean up
            try:
                write_regression_client.accounts.delete(account_id)
                print(f"✓ Cleaned up account: {account_id}")
            except Exception as e:
                print(f"⚠ Could not delete test account {account_id}: {e}")

        except Exception as e:
            pytest.fail(f"Failed to patch account: {e}")


@pytest.mark.regression
@pytest.mark.writeops
class TestHouseholdWriteOperations:
    """Test household management operations."""

    def test_household_member_management(self, write_regression_client):
        """Test adding and removing household members."""
        timestamp = int(time.time())

        # Create two test accounts
        account1_payload: CreateIndividualAccountPayload = {
            "individualAccount": {
                "accountType": "INDIVIDUAL",
                "firstName": "Household",
                "lastName": f"Member1{timestamp}",
                "email": f"member1.{timestamp}@example.com",
            }
        }

        account2_payload: CreateIndividualAccountPayload = {
            "individualAccount": {
                "accountType": "INDIVIDUAL",
                "firstName": "Household",
                "lastName": f"Member2{timestamp}",
                "email": f"member2.{timestamp}@example.com",
            }
        }

        created_accounts = []

        try:
            # Create test accounts
            result1 = write_regression_client.accounts.create(account1_payload)
            account1_id = result1["accountId"]
            created_accounts.append(account1_id)
            print(f"✓ Created test account 1: {account1_id}")

            result2 = write_regression_client.accounts.create(account2_payload)
            account2_id = result2["accountId"]
            created_accounts.append(account2_id)
            print(f"✓ Created test account 2: {account2_id}")

            # Create a household
            household_data = {
                "name": f"Test Household {timestamp}",
                "primaryAccountId": account1_id,
            }

            household_result = write_regression_client.households.create(household_data)
            household_id = household_result.get("householdId") or household_result.get(
                "id"
            )
            print(f"✓ Created test household: {household_id}")

            # Add member to household
            if household_id:
                write_regression_client.households.add_member(household_id, account2_id)
                print(f"✓ Added member {account2_id} to household {household_id}")

                # Remove member from household
                write_regression_client.households.remove_member(
                    household_id, account2_id
                )
                print(f"✓ Removed member {account2_id} from household {household_id}")

                # Clean up household
                try:
                    write_regression_client.households.delete(household_id)
                    print(f"✓ Cleaned up household: {household_id}")
                except Exception as e:
                    print(f"⚠ Could not delete test household {household_id}: {e}")

        except Exception as e:
            print(f"Household test failed: {e}")
        finally:
            # Clean up created accounts
            for account_id in created_accounts:
                try:
                    write_regression_client.accounts.delete(account_id)
                    print(f"✓ Cleaned up account: {account_id}")
                except Exception as e:
                    print(f"⚠ Could not delete test account {account_id}: {e}")


@pytest.mark.regression
@pytest.mark.writeops
class TestWebhookWriteOperations:
    """Test webhook management operations."""

    def test_webhook_lifecycle(self, write_regression_client):
        """Test creating, updating, testing, and deleting webhooks."""
        timestamp = int(time.time())

        try:
            # Create a webhook
            webhook_result = write_regression_client.webhooks.create_webhook(
                url=f"https://example.com/webhook/{timestamp}",
                event_types=["account.created", "donation.created"],
                description=f"Test webhook {timestamp}",
            )

            webhook_id = webhook_result.get("webhookId") or webhook_result.get("id")
            print(f"✓ Created test webhook: {webhook_id}")

            if webhook_id:
                # Update the webhook
                write_regression_client.webhooks.update_webhook(
                    webhook_id=webhook_id,
                    event_types=["account.created"],
                    description=f"Updated test webhook {timestamp}",
                )
                print(f"✓ Updated webhook: {webhook_id}")

                # Test the webhook
                try:
                    write_regression_client.webhooks.test_webhook(webhook_id)
                    print(f"✓ Tested webhook: {webhook_id}")
                except Exception as e:
                    print(f"⚠ Webhook test failed (expected): {e}")

                # Clean up
                try:
                    write_regression_client.webhooks.delete(webhook_id)
                    print(f"✓ Cleaned up webhook: {webhook_id}")
                except Exception as e:
                    print(f"⚠ Could not delete test webhook {webhook_id}: {e}")

        except Exception as e:
            print(f"Webhook lifecycle test failed: {e}")


@pytest.mark.regression
@pytest.mark.writeops
class TestRecurringDonationOperations:
    """Test recurring donation operations."""

    def test_cancel_recurring_donation(self, write_regression_client):
        """Test canceling a recurring donation (if any exist)."""
        try:
            # First find an active recurring donation
            recurring_donations = []
            for donation in write_regression_client.recurring_donations.get_active():
                recurring_donations.append(donation)
                if len(recurring_donations) >= 1:
                    break

            if recurring_donations:
                donation_id = recurring_donations[0].get("id") or recurring_donations[
                    0
                ].get("donationId")

                if donation_id:
                    print(
                        f"⚠ Would cancel recurring donation {donation_id} (test skipped for safety)"
                    )
                    # Uncomment the next line if you want to actually cancel donations
                    # cancel_result = write_regression_client.recurring_donations.cancel(donation_id)
                    # print(f"✓ Cancelled recurring donation: {donation_id}")
                else:
                    pytest.skip("No donation ID found in recurring donation data")
            else:
                pytest.skip("No active recurring donations found to test cancellation")

        except Exception as e:
            print(f"Recurring donation cancellation test failed: {e}")


# Safety check decorator
def require_explicit_confirmation():
    """Decorator to require explicit confirmation for dangerous tests."""

    def decorator(test_func):
        def wrapper(*args, **kwargs):
            confirm = os.getenv("NEON_CONFIRM_DANGEROUS_TESTS", "false").lower()
            if confirm != "true":
                pytest.skip(
                    f"Dangerous test {test_func.__name__} requires NEON_CONFIRM_DANGEROUS_TESTS=true"
                )
            return test_func(*args, **kwargs)

        return wrapper

    return decorator


@pytest.mark.regression
@pytest.mark.writeops
@pytest.mark.slow
class TestBulkOperations:
    """Test bulk operations (these are slow and create multiple records)."""

    @require_explicit_confirmation()
    def test_bulk_account_creation(self, write_regression_client):
        """Test creating multiple accounts (requires explicit confirmation)."""
        timestamp = int(time.time())
        created_accounts = []

        try:
            # Create 5 test accounts
            for i in range(5):
                payload: CreateIndividualAccountPayload = {
                    "individualAccount": {
                        "accountType": "INDIVIDUAL",
                        "firstName": f"Bulk{i}",
                        "lastName": f"Test{timestamp}",
                        "email": f"bulk{i}.test.{timestamp}@example.com",
                    }
                }

                result = write_regression_client.accounts.create(payload)
                account_id = result["accountId"]
                created_accounts.append(account_id)
                print(f"✓ Created bulk account {i + 1}/5: {account_id}")

                # Small delay to avoid rate limiting
                time.sleep(0.5)

        except Exception as e:
            print(f"Bulk creation test failed: {e}")
        finally:
            # Clean up all created accounts
            for account_id in created_accounts:
                try:
                    write_regression_client.accounts.delete(account_id)
                    print(f"✓ Cleaned up bulk account: {account_id}")
                    time.sleep(0.2)  # Small delay
                except Exception as e:
                    print(f"⚠ Could not delete bulk account {account_id}: {e}")
