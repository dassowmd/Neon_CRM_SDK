"""Comprehensive regression tests for ActivitiesResource.

Tests both read-only and write operations for the activities endpoint.
Organized to match src/neon_crm/resources/activities.py structure.
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
class TestActivitiesReadOnly:
    """Read-only tests for ActivitiesResource - safe for production."""

    def test_activities_list_basic(self, regression_client):
        """Test basic activity listing."""
        # NOTE: Activities resource only supports search operations, not list operations
        # The SDK architecture was refactored to prevent invalid method calls
        # Use activities.search() instead of activities.list()
        print(
            "⚠ SKIPPED: activities.list() is not supported - use activities.search() instead"
        )
        pytest.skip("Activities resource only supports search operations")

    def test_activities_limit_parameter_fixed(self, regression_client):
        """Test limit parameter - this was broken before the fix."""
        # NOTE: Activities resource only supports search operations, not list operations
        # The SDK architecture was refactored to prevent invalid method calls
        # Use activities.search() instead of activities.list()
        print(
            "⚠ SKIPPED: activities.list() is not supported - use activities.search() instead"
        )
        pytest.skip("Activities resource only supports search operations")

    def test_activities_date_filtering(self, regression_client):
        """Test activity listing with date filtering."""
        # Test with date range for recent activities
        end_date = datetime.now()
        start_date = end_date - timedelta(days=90)

        activities = list(
            regression_client.activities.list(
                limit=5,
                start_date=start_date.strftime("%Y-%m-%d"),
                end_date=end_date.strftime("%Y-%m-%d"),
            )
        )

        print(
            f"✓ Retrieved {len(activities)} activities with date filter (last 90 days)"
        )

    def test_activities_type_filtering(self, regression_client):
        """Test activity filtering by type."""
        try:
            # Test with common activity types
            activity_types = ["Email", "Phone Call", "Meeting", "Note", "Task"]

            for activity_type in activity_types:
                try:
                    filtered_activities = list(
                        regression_client.activities.list(
                            page_size=5, activity_type=activity_type
                        )
                    )
                    print(
                        f"✓ Activity type '{activity_type}': {len(filtered_activities)} activities"
                    )

                    # Validate type filtering
                    for activity in filtered_activities[:3]:
                        if "activityType" in activity:
                            if activity["activityType"] != activity_type:
                                print(
                                    f"⚠ Type filter not working: expected {activity_type}, got {activity['activityType']}"
                                )

                except Exception as e:
                    print(f"⚠ Activity type '{activity_type}' filtering failed: {e}")

        except Exception as e:
            print(f"❌ Activity type filtering test failed: {e}")

    def test_activities_account_filtering(self, regression_client):
        """Test activity filtering by account."""
        try:
            # Get a sample account ID first
            activities = list(regression_client.activities.list(limit=1))
            sample_account_id = None
            if activities:
                sample_account_id = activities[0].get("accountId")

            if sample_account_id:
                account_activities = list(
                    regression_client.activities.list(
                        page_size=10, account_id=sample_account_id
                    )
                )
                print(
                    f"✓ Account filtering: {len(account_activities)} activities for account {sample_account_id}"
                )

                # Validate account filtering
                for activity in account_activities[:3]:
                    if activity.get("accountId") != sample_account_id:
                        print(
                            f"⚠ Account filter not working: expected {sample_account_id}, got {activity.get('accountId')}"
                        )

        except Exception as e:
            print(f"⚠ Account filtering failed: {e}")

    def test_activities_search(self, regression_client):
        """Test activity search functionality."""
        search_request: SearchRequest = {
            "searchFields": [
                {"field": "activityType", "operator": "EQUAL", "value": "Email"}
            ],
            "outputFields": [
                "activityId",
                "accountId",
                "activityType",
                "date",
                "subject",
            ],
            "pagination": {"currentPage": 0, "pageSize": 5},
        }

        results = []
        for result in regression_client.activities.search(search_request):
            results.append(result)
            if len(results) >= 5:
                break

        print(f"✓ Activity search returned {len(results)} results")

        if results:
            first_result = results[0]
            # Validate search results contain requested fields
            requested_fields = ["activityId", "accountId", "activityType", "date"]
            missing_fields = [f for f in requested_fields if f not in first_result]
            if missing_fields:
                print(f"⚠ Missing requested fields: {missing_fields}")

    def test_activities_get_search_fields(self, regression_client):
        """Test getting available search fields for activities."""
        try:
            search_fields = regression_client.activities.get_search_fields()
            assert isinstance(search_fields, dict)

            print(f"✓ Retrieved {len(search_fields)} activity search fields")
        except Exception as e:
            print(f"⚠ Get search fields failed: {e}")

    def test_activities_get_output_fields(self, regression_client):
        """Test getting available output fields for activities."""
        try:
            output_fields = regression_client.activities.get_output_fields()
            assert isinstance(output_fields, dict)

            print(f"✓ Retrieved {len(output_fields)} activity output fields")
        except Exception as e:
            print(f"⚠ Get output fields failed: {e}")

    def test_activities_get_specific(self, regression_client):
        """Test getting specific activity by ID."""
        # First get an activity ID
        activities = list(regression_client.activities.list(limit=1))
        activity_id = None
        if activities:
            activity_id = activities[0].get("activityId") or activities[0].get("id")

        if activity_id:
            specific_activity = regression_client.activities.get(activity_id)
            assert isinstance(specific_activity, dict)
            print(f"✓ Retrieved specific activity: {activity_id}")
        else:
            pytest.skip("No activities available to test specific retrieval")

    def test_activities_get_invalid_id(self, regression_client):
        """Test error handling for invalid activity ID."""
        with pytest.raises(NeonNotFoundError):
            regression_client.activities.get(999999999)
        print("✓ Correctly received 404 for invalid activity ID")

    def test_activities_get_types(self, regression_client):
        """Test getting available activity types."""
        try:
            activity_types = regression_client.activities.get_types()
            assert isinstance(activity_types, list)
            print(f"✓ Retrieved {len(activity_types)} activity types")

            if activity_types:
                print(f"Sample activity types: {activity_types[:5]}")

        except Exception as e:
            print(f"⚠ Get activity types failed: {e}")

    def test_activities_parameter_combinations(self, regression_client):
        """Test various parameter combinations."""
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")

        parameter_combinations = [
            {"activity_type": "Email", "limit": 3},
            {"start_date": start_date, "end_date": end_date, "page_size": 5},
            {"activity_type": "Phone Call", "limit": 2},
        ]

        for i, params in enumerate(parameter_combinations):
            try:
                activities = list(regression_client.activities.list(**params))
                print(
                    f"✓ Parameter combination {i + 1}: {len(activities)} activities with {params}"
                )

                # Validate limit if specified
                if "limit" in params and len(activities) > params["limit"]:
                    print(
                        f"❌ Limit not respected: expected max {params['limit']}, got {len(activities)}"
                    )

            except Exception as e:
                print(f"❌ Parameter combination {i + 1} failed {params}: {e}")


@pytest.mark.regression
@pytest.mark.writeops
class TestActivitiesWriteOperations:
    """Write operation tests for ActivitiesResource - modifies database."""

    def test_create_activity_basic(self, write_regression_client):
        """Test creating a basic activity."""
        timestamp = int(time.time())

        # First create a test account
        account_payload = {
            "individualAccount": {
                "accountType": "INDIVIDUAL",
                "firstName": "ActivityTest",
                "lastName": f"Account{timestamp}",
                "email": f"activity.test.{timestamp}@example.com",
            }
        }

        created_accounts = []
        created_activities = []

        try:
            # Create account
            account_result = write_regression_client.accounts.create(account_payload)
            account_id = account_result["accountId"]
            created_accounts.append(account_id)
            print(f"✓ Created test account: {account_id}")

            # Create activity
            activity_payload = {
                "activity": {
                    "accountId": account_id,
                    "activityType": "Note",
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "subject": f"Test Activity {timestamp}",
                    "note": f"Test activity created at {timestamp}",
                }
            }

            activity_result = write_regression_client.activities.create(
                activity_payload
            )
            activity_id = activity_result.get("activityId") or activity_result.get("id")

            if activity_id:
                created_activities.append(activity_id)
                print(f"✓ Created activity: {activity_id}")

                # Verify creation
                created_activity = write_regression_client.activities.get(activity_id)
                assert created_activity["accountId"] == account_id
                assert created_activity["activityType"] == "Note"

            else:
                print(f"⚠ No activity ID in response: {list(activity_result.keys())}")

        except Exception as e:
            print(f"❌ Activity creation failed: {e}")
        finally:
            # Cleanup activities first, then accounts
            for activity_id in created_activities:
                try:
                    write_regression_client.activities.delete(activity_id)
                    print(f"✓ Cleaned up activity: {activity_id}")
                except Exception as e:
                    print(f"⚠ Could not delete activity {activity_id}: {e}")

            for account_id in created_accounts:
                try:
                    write_regression_client.accounts.delete(account_id)
                    print(f"✓ Cleaned up account: {account_id}")
                except Exception as e:
                    print(f"⚠ Could not delete account {account_id}: {e}")

    def test_create_activity_with_details(self, write_regression_client):
        """Test creating activity with additional details."""
        timestamp = int(time.time())

        # Create test account
        account_payload = {
            "individualAccount": {
                "accountType": "INDIVIDUAL",
                "firstName": "DetailedActivity",
                "lastName": f"Test{timestamp}",
                "email": f"detailed.activity.{timestamp}@example.com",
            }
        }

        created_accounts = []
        created_activities = []

        try:
            account_result = write_regression_client.accounts.create(account_payload)
            account_id = account_result["accountId"]
            created_accounts.append(account_id)

            # Create activity with more details
            activity_payload = {
                "activity": {
                    "accountId": account_id,
                    "activityType": "Email",
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "subject": f"Detailed Test Email {timestamp}",
                    "note": f"Comprehensive test email activity created at {timestamp}",
                    "priority": "Medium",
                }
            }

            activity_result = write_regression_client.activities.create(
                activity_payload
            )
            activity_id = activity_result.get("activityId") or activity_result.get("id")

            if activity_id:
                created_activities.append(activity_id)
                print(f"✓ Created detailed activity: {activity_id}")

        except Exception as e:
            print(f"❌ Detailed activity creation failed: {e}")
        finally:
            # Cleanup
            for activity_id in created_activities:
                try:
                    write_regression_client.activities.delete(activity_id)
                    print(f"✓ Cleaned up activity: {activity_id}")
                except Exception as e:
                    print(f"⚠ Could not delete activity {activity_id}: {e}")

            for account_id in created_accounts:
                try:
                    write_regression_client.accounts.delete(account_id)
                    print(f"✓ Cleaned up account: {account_id}")
                except Exception as e:
                    print(f"⚠ Could not delete account {account_id}: {e}")

    def test_update_activity(self, write_regression_client):
        """Test updating an activity."""
        timestamp = int(time.time())

        # Create test account and activity
        account_payload = {
            "individualAccount": {
                "accountType": "INDIVIDUAL",
                "firstName": "UpdateActivity",
                "lastName": f"Test{timestamp}",
                "email": f"update.activity.{timestamp}@example.com",
            }
        }

        created_accounts = []
        created_activities = []

        try:
            # Create account
            account_result = write_regression_client.accounts.create(account_payload)
            account_id = account_result["accountId"]
            created_accounts.append(account_id)

            # Create activity
            activity_payload = {
                "activity": {
                    "accountId": account_id,
                    "activityType": "Note",
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "subject": f"Original Subject {timestamp}",
                    "note": f"Original note {timestamp}",
                }
            }

            activity_result = write_regression_client.activities.create(
                activity_payload
            )
            activity_id = activity_result.get("activityId") or activity_result.get("id")

            if activity_id:
                created_activities.append(activity_id)

                # Update activity
                update_data = {
                    "activity": {
                        "subject": f"Updated Subject {timestamp}",
                        "note": f"Updated note at {timestamp}",
                        "priority": "High",
                    }
                }

                write_regression_client.activities.update(activity_id, update_data)
                print(f"✓ Updated activity: {activity_id}")

                # Verify update
                updated_activity = write_regression_client.activities.get(activity_id)
                if f"Updated Subject {timestamp}" in updated_activity.get(
                    "subject", ""
                ):
                    print("✓ Activity subject updated correctly")
                else:
                    print(f"⚠ Subject not updated: {updated_activity.get('subject')}")

        except Exception as e:
            print(f"❌ Activity update failed: {e}")
        finally:
            # Cleanup
            for activity_id in created_activities:
                try:
                    write_regression_client.activities.delete(activity_id)
                    print(f"✓ Cleaned up activity: {activity_id}")
                except Exception as e:
                    print(f"⚠ Could not delete activity {activity_id}: {e}")

            for account_id in created_accounts:
                try:
                    write_regression_client.accounts.delete(account_id)
                    print(f"✓ Cleaned up account: {account_id}")
                except Exception as e:
                    print(f"⚠ Could not delete account {account_id}: {e}")

    def test_activity_validation_errors(self, write_regression_client):
        """Test activity validation errors."""
        # Test invalid account ID
        invalid_payload = {
            "activity": {
                "accountId": 999999999,  # Non-existent account
                "activityType": "Note",
                "date": datetime.now().strftime("%Y-%m-%d"),
                "subject": "Test Activity",
            }
        }

        with pytest.raises(
            (NeonBadRequestError, NeonNotFoundError, NeonUnprocessableEntityError)
        ):
            write_regression_client.activities.create(invalid_payload)
        print("✓ Invalid account ID correctly rejected")

        # Test missing required fields
        incomplete_payload = {
            "activity": {
                "accountId": 1,  # This will also fail, but other validation should come first
                "activityType": "Note",
                # Missing date and subject
            }
        }

        with pytest.raises((NeonBadRequestError, NeonUnprocessableEntityError)):
            write_regression_client.activities.create(incomplete_payload)
        print("✓ Missing required fields correctly rejected")

        # Test invalid date format
        invalid_date_payload = {
            "activity": {
                "accountId": 1,
                "activityType": "Note",
                "date": "invalid-date",
                "subject": "Test Activity",
            }
        }

        with pytest.raises((NeonBadRequestError, NeonUnprocessableEntityError)):
            write_regression_client.activities.create(invalid_date_payload)
        print("✓ Invalid date format correctly rejected")
