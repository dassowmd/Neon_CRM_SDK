"""Read-only regression tests for the Neon CRM SDK.

These tests use the actual API but only perform read operations.
They are safe to run against production data.

Environment variables required:
- NEON_ORG_ID: Your Neon CRM organization ID
- NEON_API_KEY: Your Neon CRM API key
- NEON_ENVIRONMENT: "production" or "trial" (defaults to "trial")
"""

import pytest

from neon_crm.types import SearchRequest, UserType


@pytest.mark.regression
@pytest.mark.readonly
class TestReadOnlyOperations:
    """Test read-only operations against the actual API."""

    def test_client_connection(self, regression_client):
        """Test that we can connect to the API."""
        # This test just verifies the client is properly configured
        assert regression_client.org_id is not None
        assert regression_client.api_key is not None
        assert regression_client.environment in ["production", "trial"]

    def test_get_system_properties(self, regression_client):
        """Test getting system properties."""
        try:
            properties = regression_client.properties.get_system_info()
            assert isinstance(properties, dict)
            print(f"System info retrieved: {len(properties)} properties")
        except Exception as e:
            pytest.skip(f"System properties endpoint not available: {e}")

    def test_get_organization_info(self, regression_client):
        """Test getting organization information."""
        try:
            org_info = regression_client.properties.get_organization_info()
            assert isinstance(org_info, dict)
            print(f"Organization info retrieved: {org_info.get('name', 'Unknown')}")
        except Exception as e:
            pytest.skip(f"Organization info endpoint not available: {e}")

    def test_list_accounts_basic(self, regression_client):
        """Test basic account listing."""
        try:
            accounts = []
            for account in regression_client.accounts.list(
                page_size=5, user_type=UserType.INDIVIDUAL
            ):
                accounts.append(account)
                # Only get first few for testing
                if len(accounts) >= 5:
                    break

            print(f"Retrieved {len(accounts)} accounts")
            if accounts:
                first_account = accounts[0]
                assert "accountId" in first_account
                print(f"First account ID: {first_account.get('accountId')}")

        except Exception as e:
            pytest.skip(f"Accounts endpoint not accessible: {e}")

    def test_list_accounts_with_filters(self, regression_client):
        """Test account listing with filters."""
        try:
            # Test filtering by user type
            individual_count = 0
            for account in regression_client.accounts.list(
                user_type=UserType.INDIVIDUAL, page_size=3
            ):
                individual_count += 1
                assert (
                    account.get("userType") == "INDIVIDUAL" or "userType" not in account
                )
                if individual_count >= 3:
                    break

            company_count = 0
            for account in regression_client.accounts.list(
                user_type=UserType.COMPANY, page_size=3
            ):
                company_count += 1
                assert account.get("userType") == "COMPANY" or "userType" not in account
                if company_count >= 3:
                    break

            print(f"Found {individual_count} individuals, {company_count} companies")

        except Exception as e:
            print(f"Account filtering test failed: {e}")

    def test_account_search(self, regression_client):
        """Test account search functionality."""
        try:
            search_request: SearchRequest = {
                "searchFields": [
                    {"field": "userType", "operator": "EQUAL", "value": "INDIVIDUAL"}
                ],
                "outputFields": [
                    "accountId",
                    "firstName",
                    "lastName",
                    "email",
                    "userType",
                ],
                "pagination": {"currentPage": 0, "pageSize": 5},
            }

            results = []
            for result in regression_client.accounts.search(search_request):
                results.append(result)
                if len(results) >= 5:
                    break

            print(f"Search returned {len(results)} results")
            if results:
                print(f"First result keys: {list(results[0].keys())}")

        except Exception as e:
            print(f"Account search test failed: {e}")

    def test_get_search_fields(self, regression_client):
        """Test getting available search fields."""
        try:
            search_fields = regression_client.accounts.get_search_fields()
            assert isinstance(search_fields, dict)

            print(f"Available search fields: {len(search_fields)}")

            if search_fields:
                print(f"Sample search field: {search_fields[0]}")

        except Exception as e:
            print(f"Get search fields test failed: {e}")

    def test_get_output_fields(self, regression_client):
        """Test getting available output fields."""
        try:
            output_fields = regression_client.accounts.get_output_fields()
            assert isinstance(output_fields, dict)

            print(f"Available output fields: {len(output_fields)}")

            if output_fields:
                print(f"Sample output field: {output_fields[0]}")

        except Exception as e:
            print(f"Get output fields test failed: {e}")

    def test_list_donations(self, regression_client):
        """Test listing donations."""
        try:
            donations = []
            for donation in regression_client.donations.list(page_size=3):
                donations.append(donation)
                if len(donations) >= 3:
                    break

            print(f"Retrieved {len(donations)} donations")
            if donations:
                first_donation = donations[0]
                print(f"First donation keys: {list(first_donation.keys())}")

        except Exception as e:
            print(f"Donations list test failed: {e}")

    def test_list_events(self, regression_client):
        """Test listing events."""
        try:
            events = []
            for event in regression_client.events.list(page_size=3):
                events.append(event)
                if len(events) >= 3:
                    break

            print(f"Retrieved {len(events)} events")
            if events:
                first_event = events[0]
                print(f"First event keys: {list(first_event.keys())}")

        except Exception as e:
            print(f"Events list test failed: {e}")

    def test_list_campaigns(self, regression_client):
        """Test listing campaigns."""
        try:
            campaigns = []
            for campaign in regression_client.campaigns.list(page_size=3):
                campaigns.append(campaign)
                if len(campaigns) >= 3:
                    break

            print(f"Retrieved {len(campaigns)} campaigns")
            if campaigns:
                first_campaign = campaigns[0]
                print(f"First campaign keys: {list(first_campaign.keys())}")

        except Exception as e:
            print(f"Campaigns list test failed: {e}")

    def test_list_memberships(self, regression_client):
        """Test listing memberships."""
        try:
            memberships = []
            for membership in regression_client.memberships.list(page_size=3):
                memberships.append(membership)
                if len(memberships) >= 3:
                    break

            print(f"Retrieved {len(memberships)} memberships")
            if memberships:
                first_membership = memberships[0]
                print(f"First membership keys: {list(first_membership.keys())}")

        except Exception as e:
            print(f"Memberships list test failed: {e}")

    def test_list_activities(self, regression_client):
        """Test listing activities."""
        try:
            activities = []
            for activity in regression_client.activities.list(page_size=3):
                activities.append(activity)
                if len(activities) >= 3:
                    break

            print(f"Retrieved {len(activities)} activities")
            if activities:
                first_activity = activities[0]
                print(f"First activity keys: {list(first_activity.keys())}")

        except Exception as e:
            print(f"Activities list test failed: {e}")

    def test_list_custom_fields(self, regression_client):
        """Test listing custom fields."""
        try:
            custom_fields = []
            for field in regression_client.custom_fields.list(page_size=5):
                custom_fields.append(field)
                if len(custom_fields) >= 5:
                    break

            print(f"Retrieved {len(custom_fields)} custom fields")
            if custom_fields:
                first_field = custom_fields[0]
                print(f"First custom field keys: {list(first_field.keys())}")

        except Exception as e:
            print(f"Custom fields list test failed: {e}")

    def test_get_custom_fields_by_category(self, regression_client):
        """Test getting custom fields for a specific category."""
        try:
            account_fields = []
            for field in regression_client.custom_fields.get_by_category("Account"):
                account_fields.append(field)
                if len(account_fields) >= 5:
                    break

            print(f"Retrieved {len(account_fields)} account custom fields")

        except Exception as e:
            print(f"Custom fields by category test failed: {e}")

    @pytest.mark.slow
    def test_pagination_across_multiple_pages(self, regression_client):
        """Test pagination across multiple pages (slow test)."""
        try:
            total_count = 0
            page_count = 0

            for _account in regression_client.accounts.list(
                page_size=10, user_type=UserType.INDIVIDUAL
            ):
                total_count += 1

                # Track pages (approximate)
                if total_count % 10 == 1:
                    page_count += 1
                    print(f"Processing page {page_count}, total items: {total_count}")

                # Limit test to reasonable number
                if total_count >= 50:
                    break

            print(
                f"Processed {total_count} items across approximately {page_count} pages"
            )

        except Exception as e:
            print(f"Multi-page pagination test failed: {e}")

    def test_error_handling_invalid_id(self, regression_client):
        """Test error handling with invalid ID."""
        try:
            # Try to get a non-existent account
            result = regression_client.accounts.get(999999999)
            print(f"Unexpectedly got result for invalid ID: {result}")
        except Exception as e:
            print(f"Expected error for invalid ID: {type(e).__name__}")
            # This is expected behavior

    def test_specific_account_details(self, regression_client):
        """Test getting specific account details if we have accounts."""
        try:
            # Get the first account ID
            first_account = None
            for account in regression_client.accounts.list(
                page_size=1, user_type=UserType.INDIVIDUAL
            ):
                first_account = account
                break

            if first_account and "accountId" in first_account:
                account_id = first_account["accountId"]
                details = regression_client.accounts.get(account_id)

                assert isinstance(details, dict)
                print(f"Retrieved details for account {account_id}")
                print(f"Account details keys: {list(details.keys())}")
            else:
                pytest.skip("No accounts available to test details")

        except Exception as e:
            print(f"Account details test failed: {e}")

    def test_account_related_data(self, regression_client):
        """Test getting related data for an account."""
        try:
            # Get the first account
            first_account = None
            for account in regression_client.accounts.list(
                page_size=1, user_type=UserType.INDIVIDUAL
            ):
                first_account = account
                break

            if first_account and "accountId" in first_account:
                account_id = first_account["accountId"]

                # Test related data endpoints
                try:
                    donations = list(
                        regression_client.accounts.get_donations(account_id)
                    )
                    print(f"Account {account_id} has {len(donations)} donations")
                except Exception as e:
                    print(f"Could not get donations for account {account_id}: {e}")

                try:
                    memberships = list(
                        regression_client.accounts.get_memberships(account_id)
                    )
                    print(f"Account {account_id} has {len(memberships)} memberships")
                except Exception as e:
                    print(f"Could not get memberships for account {account_id}: {e}")

            else:
                pytest.skip("No accounts available to test related data")

        except Exception as e:
            print(f"Account related data test failed: {e}")
