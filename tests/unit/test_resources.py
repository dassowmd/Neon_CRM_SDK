"""Unit tests for all resource classes."""

import pytest

from neon_crm.resources.accounts import AccountsResource
from neon_crm.resources.custom_fields import CustomFieldsResource
from neon_crm.resources.donations import DonationsResource
from neon_crm.resources.events import EventsResource
from neon_crm.resources.grants import GrantsResource
from neon_crm.resources.households import HouseholdsResource
from neon_crm.resources.online_store import OnlineStoreResource
from neon_crm.resources.orders import OrdersResource
from neon_crm.resources.pledges import PledgesResource
from neon_crm.resources.properties import PropertiesResource
from neon_crm.resources.recurring_donations import RecurringDonationsResource
from neon_crm.resources.webhooks import WebhooksResource
from neon_crm.types import UserType


@pytest.mark.unit
class TestAccountsResource:
    """Test cases for AccountsResource."""

    def test_initialization(self, mock_client):
        """Test AccountsResource initialization."""
        resource = AccountsResource(mock_client)
        assert resource._endpoint == "/accounts"

    def test_list_with_filters(self, mock_client):
        """Test list method with various filters."""
        mock_client.get.return_value = {
            "accounts": [{"id": 1}],
            "pagination": {"currentPage": 1, "totalPages": 1},
        }

        resource = AccountsResource(mock_client)
        results = list(
            resource.list(
                email="test@example.com",
                first_name="John",
                user_type=UserType.INDIVIDUAL,
            )
        )

        assert len(results) == 1
        # Verify the parameters were passed correctly
        call_args = mock_client.get.call_args
        assert call_args[0][0] == "/accounts"
        params = call_args[1]["params"]
        assert params["email"] == "test@example.com"
        assert params["firstName"] == "John"
        assert params["userType"] == UserType.INDIVIDUAL

    def test_link_accounts(self, mock_client):
        """Test linking individual account to company."""
        mock_client.post.return_value = {"success": True}

        resource = AccountsResource(mock_client)
        result = resource.link(individual_id=123, company_id=456)

        assert result["success"] is True
        mock_client.post.assert_called_once_with(
            "/accounts/link", json_data={"individualId": 123, "companyId": 456}
        )

    def test_unlink_accounts(self, mock_client):
        """Test unlinking individual account from company."""
        mock_client.post.return_value = {"success": True}

        resource = AccountsResource(mock_client)
        result = resource.unlink(individual_id=123, company_id=456)

        assert result["success"] is True
        mock_client.post.assert_called_once_with(
            "/accounts/unlink", json_data={"individualId": 123, "companyId": 456}
        )

    def test_get_donations(self, mock_client):
        """Test getting donations for an account."""
        mock_client.get.return_value = {"donations": [{"id": 1, "amount": 100}]}

        resource = AccountsResource(mock_client)
        results = list(resource.get_donations(account_id=123))

        assert len(results) == 1
        assert results[0]["amount"] == 100
        mock_client.get.assert_called_once_with("/accounts/123/donations", params={})

    def test_get_memberships(self, mock_client):
        """Test getting memberships for an account."""
        mock_client.get.return_value = [{"id": 1, "type": "Premium"}]

        resource = AccountsResource(mock_client)
        results = list(resource.get_memberships(account_id=123))

        assert len(results) == 1
        assert results[0]["type"] == "Premium"

    def test_get_orders(self, mock_client):
        """Test getting orders for an account."""
        mock_client.get.return_value = [{"id": 1, "total": 50}]

        resource = AccountsResource(mock_client)
        results = list(resource.get_orders(account_id=123))

        assert len(results) == 1
        assert results[0]["total"] == 50

    def test_get_pledges(self, mock_client):
        """Test getting pledges for an account."""
        mock_client.get.return_value = [{"id": 1, "amount": 200}]

        resource = AccountsResource(mock_client)
        results = list(resource.get_pledges(account_id=123))

        assert len(results) == 1
        assert results[0]["amount"] == 200


@pytest.mark.unit
class TestDonationsResource:
    """Test cases for DonationsResource."""

    def test_initialization(self, mock_client):
        """Test DonationsResource initialization."""
        resource = DonationsResource(mock_client)
        assert resource._endpoint == "/donations"

    def test_list_with_filters(self, mock_client):
        """Test list method with donation-specific filters."""
        mock_client.get.return_value = {
            "donations": [{"id": 1}],
            "pagination": {"currentPage": 1, "totalPages": 1},
        }

        resource = DonationsResource(mock_client)
        results = list(
            resource.list(
                campaign_id=123,
                fund_id=456,
                start_date="2024-01-01",
                end_date="2024-12-31",
            )
        )

        assert len(results) == 1
        call_args = mock_client.get.call_args
        params = call_args[1]["params"]
        assert params["campaignId"] == 123
        assert params["fundId"] == 456
        assert params["startDate"] == "2024-01-01"
        assert params["endDate"] == "2024-12-31"


@pytest.mark.unit
class TestEventsResource:
    """Test cases for EventsResource."""

    def test_list_with_filters(self, mock_client):
        """Test list method with event-specific filters."""
        mock_client.get.return_value = {
            "events": [{"id": 1}],
            "pagination": {"currentPage": 1, "totalPages": 1},
        }

        resource = EventsResource(mock_client)
        results = list(
            resource.list(
                event_status="published", category_id=123, start_date="2024-01-01"
            )
        )

        assert len(results) == 1
        call_args = mock_client.get.call_args
        params = call_args[1]["params"]
        assert params["eventStatus"] == "published"
        assert params["categoryId"] == 123


@pytest.mark.unit
class TestOrdersResource:
    """Test cases for OrdersResource."""

    def test_list_with_filters(self, mock_client):
        """Test list method with order-specific filters."""
        mock_client.get.return_value = {
            "orders": [{"id": 1}],
            "pagination": {"currentPage": 1, "totalPages": 1},
        }

        resource = OrdersResource(mock_client)
        results = list(resource.list(order_status="completed", start_date="2024-01-01"))

        assert len(results) == 1
        call_args = mock_client.get.call_args
        params = call_args[1]["params"]
        assert params["orderStatus"] == "completed"
        assert params["startDate"] == "2024-01-01"


@pytest.mark.unit
class TestPledgesResource:
    """Test cases for PledgesResource."""

    def test_list_with_filters(self, mock_client):
        """Test list method with pledge-specific filters."""
        mock_client.get.return_value = {
            "pledges": [{"id": 1}],
            "pagination": {"currentPage": 1, "totalPages": 1},
        }

        resource = PledgesResource(mock_client)
        results = list(
            resource.list(pledge_status="active", campaign_id=123, fund_id=456)
        )

        assert len(results) == 1
        call_args = mock_client.get.call_args
        params = call_args[1]["params"]
        assert params["pledgeStatus"] == "active"
        assert params["campaignId"] == 123


@pytest.mark.unit
class TestHouseholdsResource:
    """Test cases for HouseholdsResource."""

    def test_add_member(self, mock_client):
        """Test adding a member to a household."""
        mock_client.post.return_value = {"success": True}

        resource = HouseholdsResource(mock_client)
        result = resource.add_member(household_id=123, account_id=456)

        assert result["success"] is True
        mock_client.post.assert_called_once_with(
            "/households/123/members", json_data={"accountId": 456}
        )

    def test_remove_member(self, mock_client):
        """Test removing a member from a household."""
        mock_client.delete.return_value = {"success": True}

        resource = HouseholdsResource(mock_client)
        result = resource.remove_member(household_id=123, account_id=456)

        assert result["success"] is True
        mock_client.delete.assert_called_once_with("/households/123/members/456")


@pytest.mark.unit
class TestGrantsResource:
    """Test cases for GrantsResource."""

    def test_get_by_funder(self, mock_client):
        """Test getting grants by funder."""
        mock_client.get.return_value = {
            "grants": [{"id": 1}],
            "pagination": {"currentPage": 1, "totalPages": 1},
        }

        resource = GrantsResource(mock_client)
        results = list(resource.get_by_funder("Gates Foundation"))

        assert len(results) == 1
        call_args = mock_client.get.call_args
        params = call_args[1]["params"]
        assert params["funderName"] == "Gates Foundation"

    def test_get_active(self, mock_client):
        """Test getting active grants."""
        mock_client.get.return_value = {
            "grants": [{"id": 1}],
            "pagination": {"currentPage": 1, "totalPages": 1},
        }

        resource = GrantsResource(mock_client)
        results = list(resource.get_active())

        assert len(results) == 1
        call_args = mock_client.get.call_args
        params = call_args[1]["params"]
        assert params["grantStatus"] == "active"


@pytest.mark.unit
class TestCustomFieldsResource:
    """Test cases for CustomFieldsResource."""

    def test_get_by_category(self, mock_client):
        """Test getting custom fields by category."""
        mock_client.get.return_value = {
            "customFields": [{"id": 1}],
            "pagination": {"currentPage": 1, "totalPages": 1},
        }

        resource = CustomFieldsResource(mock_client)
        results = list(resource.get_by_category("Account"))

        assert len(results) == 1
        call_args = mock_client.get.call_args
        params = call_args[1]["params"]
        assert params["category"] == "Account"


@pytest.mark.unit
class TestRecurringDonationsResource:
    """Test cases for RecurringDonationsResource."""

    def test_cancel(self, mock_client):
        """Test canceling a recurring donation."""
        mock_client.post.return_value = {"success": True}

        resource = RecurringDonationsResource(mock_client)
        result = resource.cancel(donation_id=123)

        assert result["success"] is True
        mock_client.post.assert_called_once_with("/recurring/123/cancel")

    def test_get_by_frequency(self, mock_client):
        """Test getting recurring donations by frequency."""
        mock_client.get.return_value = {
            "recurringDonations": [{"id": 1}],
            "pagination": {"currentPage": 1, "totalPages": 1},
        }

        resource = RecurringDonationsResource(mock_client)
        results = list(resource.get_by_frequency("monthly"))

        assert len(results) == 1
        call_args = mock_client.get.call_args
        params = call_args[1]["params"]
        assert params["frequency"] == "monthly"


@pytest.mark.unit
class TestWebhooksResource:
    """Test cases for WebhooksResource."""

    def test_create_webhook(self, mock_client):
        """Test creating a webhook."""
        mock_client.post.return_value = {
            "id": 123,
            "url": "https://example.com/webhook",
        }

        resource = WebhooksResource(mock_client)
        result = resource.create_webhook(
            url="https://example.com/webhook",
            event_types=["donation.created"],
            secret="test_secret",
        )

        assert result["id"] == 123
        call_args = mock_client.post.call_args
        data = call_args[1]["json_data"]
        assert data["url"] == "https://example.com/webhook"
        assert data["eventTypes"] == ["donation.created"]
        assert data["secret"] == "test_secret"

    def test_test_webhook(self, mock_client):
        """Test testing a webhook."""
        mock_client.post.return_value = {"success": True}

        resource = WebhooksResource(mock_client)
        result = resource.test_webhook(webhook_id=123)

        assert result["success"] is True
        mock_client.post.assert_called_once_with("/webhooks/123/test")

    def test_get_event_types(self, mock_client):
        """Test getting available event types."""
        mock_client.get.return_value = [{"type": "donation.created"}]

        resource = WebhooksResource(mock_client)
        result = resource.get_event_types()

        assert len(result) == 1
        assert result[0]["type"] == "donation.created"


@pytest.mark.unit
class TestOnlineStoreResource:
    """Test cases for OnlineStoreResource."""

    def test_list_products(self, mock_client):
        """Test listing products."""
        mock_client.get.return_value = {"products": [{"id": 1, "name": "T-Shirt"}]}

        resource = OnlineStoreResource(mock_client)
        results = list(resource.list_products(product_status="active"))

        assert len(results) == 1
        assert results[0]["name"] == "T-Shirt"
        mock_client.get.assert_called_once_with(
            "/onlineStore/products", params={"productStatus": "active"}
        )

    def test_list_transactions(self, mock_client):
        """Test listing transactions."""
        mock_client.get.return_value = [{"id": 1, "amount": 25.00}]

        resource = OnlineStoreResource(mock_client)
        results = list(resource.list_transactions(start_date="2024-01-01"))

        assert len(results) == 1
        assert results[0]["amount"] == 25.00


@pytest.mark.unit
class TestPropertiesResource:
    """Test cases for PropertiesResource."""

    def test_get_system_users(self, mock_client):
        """Test getting system users."""
        mock_client.get.return_value = {"users": [{"id": 1, "name": "Admin"}]}

        resource = PropertiesResource(mock_client)
        result = resource.get_system_users()

        assert "users" in result
        mock_client.get.assert_called_once_with("/properties/system/users")

    def test_get_organization_profile(self, mock_client):
        """Test getting organization profile."""
        mock_client.get.return_value = {"name": "Test Org", "id": "12345"}

        resource = PropertiesResource(mock_client)
        result = resource.get_organization_profile()

        assert result["name"] == "Test Org"
        mock_client.get.assert_called_once_with("/properties/organization")
