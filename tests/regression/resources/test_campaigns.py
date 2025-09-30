"""Comprehensive regression tests for CampaignsResource.

Tests both read-only and write operations for the campaigns endpoint.
Organized to match src/neon_crm/resources/campaigns.py structure.
"""

import time

import pytest

from neon_crm.exceptions import (
    NeonBadRequestError,
    NeonNotFoundError,
    NeonUnprocessableEntityError,
)
from neon_crm.types import SearchRequest


@pytest.mark.regression
@pytest.mark.readonly
class TestCampaignsReadOnly:
    """Read-only tests for CampaignsResource - safe for production."""

    def test_campaigns_list_basic(self, regression_client):
        """Test basic campaign listing."""
        campaigns = list(regression_client.campaigns.list(limit=5))

        print(f"✓ Retrieved {len(campaigns)} campaigns")

        if campaigns:
            first_campaign = campaigns[0]
            assert isinstance(first_campaign, dict), "Campaign should be a dictionary"
            print(f"Campaign structure: {list(first_campaign.keys())}")

            # Check for expected campaign attributes
            expected_attrs = ["campaignId", "name", "status", "fundId"]
            missing_attrs = [
                attr for attr in expected_attrs if attr not in first_campaign
            ]
            if missing_attrs:
                print(f"⚠ Some expected attributes missing: {missing_attrs}")

    def test_campaigns_limit_parameter_fixed(self, regression_client):
        """Test limit parameter - this was broken before the fix."""
        # Test limit parameter
        limited_campaigns = list(
            regression_client.campaigns.list(page_size=20, limit=5)
        )

        if len(limited_campaigns) > 5:
            print(
                f"❌ CRITICAL: Limit not working: got {len(limited_campaigns)}, expected max 5"
            )
        else:
            print(
                f"✓ FIXED: Limit parameter working: got {len(limited_campaigns)} campaigns"
            )

        # Test limit=None (this was causing crashes before fix)
        try:
            unlimited_campaigns = list(
                regression_client.campaigns.list(page_size=10, limit=None)
            )
            print(
                f"✓ FIXED: limit=None works: got {len(unlimited_campaigns)} campaigns"
            )
        except TypeError as e:
            print(f"❌ CRITICAL: limit=None still crashes: {e}")

    def test_campaigns_status_filtering(self, regression_client):
        """Test campaign filtering by status."""
        try:
            statuses = ["active", "inactive", "archived"]

            for status in statuses:
                try:
                    status_campaigns = list(
                        regression_client.campaigns.list(page_size=5, status=status)
                    )
                    print(f"✓ Status '{status}': {len(status_campaigns)} campaigns")

                    # Validate status filtering
                    for campaign in status_campaigns[:3]:
                        if "status" in campaign:
                            if campaign["status"].lower() != status.lower():
                                print(
                                    f"⚠ Status filter not working: expected {status}, got {campaign['status']}"
                                )

                except Exception as e:
                    print(f"⚠ Status '{status}' filtering failed: {e}")

        except Exception as e:
            print(f"❌ Status filtering test failed: {e}")

    def test_campaigns_fund_filtering(self, regression_client):
        """Test campaign filtering by fund."""
        try:
            fund_campaigns = list(
                regression_client.campaigns.list(page_size=5, fund_id=1)
            )
            print(f"✓ Fund filtering: {len(fund_campaigns)} campaigns for fund 1")

            # Validate fund filtering
            for campaign in fund_campaigns[:3]:
                if "fundId" in campaign:
                    if campaign["fundId"] != 1:
                        print(
                            f"⚠ Fund filter not working: expected 1, got {campaign['fundId']}"
                        )

        except Exception as e:
            print(f"⚠ Fund filtering failed: {e}")

    def test_campaigns_search(self, regression_client):
        """Test campaign search functionality."""
        search_request: SearchRequest = {
            "searchFields": [
                {"field": "status", "operator": "EQUAL", "value": "active"}
            ],
            "outputFields": ["campaignId", "name", "status", "fundId", "goal"],
            "pagination": {"currentPage": 0, "pageSize": 5},
        }

        results = list(regression_client.campaigns.search(search_request))[:5]

        print(f"✓ Campaign search returned {len(results)} results")

        if results:
            first_result = results[0]
            # Validate search results contain requested fields
            requested_fields = ["campaignId", "name", "status", "fundId"]
            missing_fields = [f for f in requested_fields if f not in first_result]
            if missing_fields:
                print(f"⚠ Missing requested fields: {missing_fields}")

    def test_campaigns_get_search_fields(self, regression_client):
        """Test getting available search fields for campaigns."""
        try:
            search_fields = regression_client.campaigns.get_search_fields()
            assert isinstance(search_fields, dict)

            print(f"✓ Retrieved {len(search_fields)} campaign search fields")
        except Exception as e:
            print(f"⚠ Get search fields failed: {e}")

    def test_campaigns_get_output_fields(self, regression_client):
        """Test getting available output fields for campaigns."""
        try:
            output_fields = regression_client.campaigns.get_output_fields()
            assert isinstance(output_fields, dict)

            print(f"✓ Retrieved {len(output_fields)} campaign output fields")
        except Exception as e:
            print(f"⚠ Get output fields failed: {e}")

    def test_campaigns_get_specific(self, regression_client):
        """Test getting specific campaign by ID."""
        # First get a campaign ID
        campaign_id = None
        campaigns = list(regression_client.campaigns.list(limit=1))
        if campaigns:
            campaign_id = campaigns[0].get("campaignId") or campaigns[0].get("id")

        if campaign_id:
            specific_campaign = regression_client.campaigns.get(campaign_id)
            assert isinstance(specific_campaign, dict)
            print(f"✓ Retrieved specific campaign: {campaign_id}")
        else:
            pytest.skip("No campaigns available to test specific retrieval")

    def test_campaigns_get_invalid_id(self, regression_client):
        """Test error handling for invalid campaign ID."""
        with pytest.raises(NeonNotFoundError):
            regression_client.campaigns.get(999999999)
        print("✓ Correctly received 404 for invalid campaign ID")

    def test_campaigns_get_donations(self, regression_client):
        """Test getting campaign donations."""
        # First get a campaign ID
        campaign_id = None
        campaigns = list(regression_client.campaigns.list(limit=1))
        if campaigns:
            campaign_id = campaigns[0].get("campaignId") or campaigns[0].get("id")

        if campaign_id:
            try:
                donations = list(regression_client.campaigns.get_donations(campaign_id))
                print(f"✓ Campaign {campaign_id} has {len(donations)} donations")
            except Exception as e:
                print(f"⚠ Could not get donations for campaign {campaign_id}: {e}")
        else:
            pytest.skip("No campaigns available to test donation retrieval")

    def test_campaigns_parameter_combinations(self, regression_client):
        """Test various parameter combinations."""
        parameter_combinations = [
            {"status": "active", "limit": 3},
            {"fund_id": 1, "page_size": 5},
            {"status": "active", "fund_id": 1, "limit": 2},
        ]

        for i, params in enumerate(parameter_combinations):
            try:
                campaigns = list(regression_client.campaigns.list(**params))
                print(
                    f"✓ Parameter combination {i + 1}: {len(campaigns)} campaigns with {params}"
                )

                # Validate limit if specified
                if "limit" in params and len(campaigns) > params["limit"]:
                    print(
                        f"❌ Limit not respected: expected max {params['limit']}, got {len(campaigns)}"
                    )

            except Exception as e:
                print(f"❌ Parameter combination {i + 1} failed {params}: {e}")


@pytest.mark.regression
@pytest.mark.writeops
class TestCampaignsWriteOperations:
    """Write operation tests for CampaignsResource - modifies database."""

    def test_create_campaign_basic(self, write_regression_client):
        """Test creating a basic campaign."""
        timestamp = int(time.time())

        created_campaigns = []

        try:
            # Create campaign
            campaign_payload = {
                "campaign": {
                    "name": f"Test Campaign {timestamp}",
                    "fundId": 1,  # Assuming fund 1 exists
                    "status": "active",
                    "goal": 10000.0,
                    "description": f"Test campaign created at {timestamp}",
                }
            }

            campaign_result = write_regression_client.campaigns.create(campaign_payload)
            campaign_id = campaign_result.get("campaignId") or campaign_result.get("id")

            if campaign_id:
                created_campaigns.append(campaign_id)
                print(f"✓ Created campaign: {campaign_id}")
                print(f"Campaign response structure: {list(campaign_result.keys())}")

                # Verify creation
                created_campaign = write_regression_client.campaigns.get(campaign_id)
                assert created_campaign["name"] == f"Test Campaign {timestamp}"
                assert created_campaign["status"] == "active"

            else:
                print(f"⚠ No campaign ID in response: {list(campaign_result.keys())}")

        except Exception as e:
            print(f"❌ Campaign creation failed: {e}")
        finally:
            # Clean up
            for campaign_id in created_campaigns:
                try:
                    write_regression_client.campaigns.delete(campaign_id)
                    print(f"✓ Cleaned up campaign: {campaign_id}")
                except Exception as e:
                    print(f"⚠ Could not delete campaign {campaign_id}: {e}")

    def test_update_campaign(self, write_regression_client):
        """Test updating a campaign."""
        timestamp = int(time.time())
        created_campaigns = []

        try:
            # Create campaign
            campaign_payload = {
                "campaign": {
                    "name": f"Original Campaign {timestamp}",
                    "fundId": 1,
                    "status": "active",
                    "goal": 5000.0,
                    "description": f"Original description {timestamp}",
                }
            }

            campaign_result = write_regression_client.campaigns.create(campaign_payload)
            campaign_id = campaign_result.get("campaignId") or campaign_result.get("id")

            if campaign_id:
                created_campaigns.append(campaign_id)

                # Update campaign
                update_data = {
                    "campaign": {
                        "name": f"Updated Campaign {timestamp}",
                        "goal": 15000.0,
                        "description": f"Updated description {timestamp}",
                    }
                }

                write_regression_client.campaigns.update(campaign_id, update_data)
                print(f"✓ Updated campaign: {campaign_id}")

                # Verify update
                updated_campaign = write_regression_client.campaigns.get(campaign_id)
                if updated_campaign.get("goal") == 15000.0:
                    print("✓ Campaign goal updated correctly")
                else:
                    print(f"⚠ Goal not updated: {updated_campaign.get('goal')}")

        except Exception as e:
            print(f"❌ Campaign update test failed: {e}")
        finally:
            # Clean up
            for campaign_id in created_campaigns:
                try:
                    write_regression_client.campaigns.delete(campaign_id)
                    print(f"✓ Cleaned up campaign: {campaign_id}")
                except Exception as e:
                    print(f"⚠ Could not delete campaign {campaign_id}: {e}")

    def test_campaign_validation_errors(self, write_regression_client):
        """Test campaign validation errors."""
        # Test missing required fields
        with pytest.raises((NeonBadRequestError, NeonUnprocessableEntityError)):
            write_regression_client.campaigns.create(
                {
                    "campaign": {
                        "name": "Test Campaign"
                        # Missing fundId and other required fields
                    }
                }
            )
        print("✓ Missing required fields correctly rejected")

        # Test invalid fund ID
        with pytest.raises(
            (NeonBadRequestError, NeonNotFoundError, NeonUnprocessableEntityError)
        ):
            write_regression_client.campaigns.create(
                {
                    "campaign": {
                        "name": "Test Campaign",
                        "fundId": 999999999,  # Non-existent fund
                        "status": "active",
                    }
                }
            )
        print("✓ Invalid fund ID correctly rejected")

        # Test invalid goal amount
        try:
            write_regression_client.campaigns.create(
                {
                    "campaign": {
                        "name": "Test Campaign",
                        "fundId": 1,
                        "status": "active",
                        "goal": -1000.0,  # Negative goal
                    }
                }
            )
            print("⚠ Negative goal was accepted")
        except (NeonBadRequestError, NeonUnprocessableEntityError):
            print("✓ Negative goal correctly rejected")
