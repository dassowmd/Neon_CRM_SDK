"""Comprehensive unit tests for AccountsResource - the most commonly used resource."""

from unittest.mock import Mock, patch

import pytest

from neon_crm.resources.accounts import AccountsResource
from neon_crm.types import UserType
from neon_crm.governance import create_user_permissions, Role


class TestAccountsResourceBasics:
    """Test basic AccountsResource functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_client = Mock()
        self.mock_client.org_id = "test_org"
        self.mock_client.api_key = "test_key"
        self.mock_client.user_permissions = create_user_permissions(
            user_id="test_user", role=Role.ADMIN
        )
        self.mock_client.org_id = "test_org"
        self.mock_client.api_key = "test_key"
        # Set up permissions to allow all operations
        self.mock_client.user_permissions = create_user_permissions(
            user_id="test_user", role=Role.ADMIN
        )
        self.resource = AccountsResource(self.mock_client)

    def test_initialization(self):
        """Test AccountsResource initialization."""
        assert self.resource._client == self.mock_client
        assert self.resource._endpoint == "/accounts"

    def test_resource_inherits_searchable(self):
        """Test that AccountsResource is searchable."""
        from neon_crm.resources.base import SearchableResource

        assert isinstance(self.resource, SearchableResource)

    def test_list_with_user_type_enum(self):
        """Test listing accounts with UserType enum."""
        self.mock_client.get.return_value = {
            "accounts": [{"accountId": 123, "userType": "INDIVIDUAL"}],
            "pagination": {"currentPage": 0, "totalPages": 1},
        }

        result = list(self.resource.list(user_type=UserType.INDIVIDUAL))

        assert len(result) == 1
        assert result[0]["accountId"] == 123

        # Verify the API call
        call_args = self.mock_client.get.call_args
        params = call_args[1]["params"]
        assert params["userType"] == "INDIVIDUAL"

    def test_list_with_user_type_string(self):
        """Test listing accounts with user type as string."""
        self.mock_client.get.return_value = {
            "accounts": [{"accountId": 123, "userType": "COMPANY"}],
            "pagination": {"currentPage": 0, "totalPages": 1},
        }

        list(self.resource.list(user_type="COMPANY"))

        call_args = self.mock_client.get.call_args
        params = call_args[1]["params"]
        assert params["userType"] == "COMPANY"

    def test_list_without_user_type_validation(self):
        """Test that list requires user_type parameter."""
        with pytest.raises(ValueError) as exc_info:
            list(self.resource.list())

        assert "user_type is required" in str(exc_info.value)

    def test_list_with_invalid_user_type(self):
        """Test validation of invalid user type."""
        with pytest.raises(ValueError) as exc_info:
            list(self.resource.list(user_type="INVALID_TYPE"))

        assert "Invalid user_type" in str(exc_info.value)

    def test_list_with_additional_filters(self):
        """Test listing accounts with additional filters."""
        self.mock_client.get.return_value = {
            "accounts": [{"accountId": 123, "userType": "INDIVIDUAL"}],
            "pagination": {"currentPage": 0, "totalPages": 1},
        }

        list(
            self.resource.list(
                user_type=UserType.INDIVIDUAL,
                first_name="John",
                last_name="Doe",
                limit=5,
            )
        )

        call_args = self.mock_client.get.call_args
        params = call_args[1]["params"]
        assert params["userType"] == "INDIVIDUAL"
        assert params["firstName"] == "John"
        assert params["lastName"] == "Doe"

    def test_get_account(self):
        """Test getting a specific account."""
        self.mock_client.get.return_value = {
            "individualAccount": {
                "accountId": 123,
                "firstName": "John",
                "lastName": "Doe",
            }
        }

        result = self.resource.get(123)

        assert result["individualAccount"]["accountId"] == 123
        self.mock_client.get.assert_called_once_with("/accounts/123")

    def test_create_account(self):
        """Test creating an account."""
        account_data = {
            "individualAccount": {
                "firstName": "Jane",
                "lastName": "Smith",
                "email": "jane@example.com",
            }
        }

        self.mock_client.post.return_value = {"accountId": 456}

        result = self.resource.create(account_data)

        assert result["accountId"] == 456
        self.mock_client.post.assert_called_once_with(
            "/accounts", json_data=account_data
        )

    def test_update_account(self):
        """Test updating an account."""
        update_data = {"individualAccount": {"firstName": "Updated Name"}}

        self.mock_client.put.return_value = {"accountId": 123, "updated": True}

        result = self.resource.update(123, update_data)

        assert result["updated"] is True
        self.mock_client.put.assert_called_once_with(
            "/accounts/123", json_data=update_data
        )

    def test_patch_account(self):
        """Test patching an account."""
        patch_data = {"phone": "+1-555-0123"}

        self.mock_client.patch.return_value = {"accountId": 123, "patched": True}

        result = self.resource.patch(123, patch_data)

        assert result["patched"] is True
        self.mock_client.patch.assert_called_once_with(
            "/accounts/123", json_data=patch_data
        )

    def test_delete_account(self):
        """Test deleting an account."""
        self.mock_client.delete.return_value = {"status": "deleted"}

        result = self.resource.delete(123)

        assert result["status"] == "deleted"
        self.mock_client.delete.assert_called_once_with("/accounts/123")


class TestAccountsResourceRelationships:
    """Test AccountsResource relationship methods."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_client = Mock()
        self.mock_client.org_id = "test_org"
        self.mock_client.api_key = "test_key"
        self.mock_client.user_permissions = create_user_permissions(
            user_id="test_user", role=Role.ADMIN
        )
        self.resource = AccountsResource(self.mock_client)

    def test_get_donations(self):
        """Test getting donations for an account."""
        from neon_crm.resources.base import RelationshipResource

        donations_resource = self.resource.get_donations(123)

        assert isinstance(donations_resource, RelationshipResource)
        assert donations_resource.parent_id == 123
        assert donations_resource.relationship == "donations"
        assert donations_resource._endpoint == "/accounts/123/donations"

    def test_get_memberships(self):
        """Test getting memberships for an account."""
        memberships_resource = self.resource.get_memberships(456)

        assert memberships_resource.parent_id == 456
        assert memberships_resource.relationship == "memberships"

    def test_get_event_registrations(self):
        """Test getting event registrations for an account."""
        registrations_resource = self.resource.get_event_registrations(789)

        assert registrations_resource.parent_id == 789
        assert registrations_resource.relationship == "eventRegistrations"

    def test_get_orders(self):
        """Test getting orders for an account."""
        orders_resource = self.resource.get_orders(123)

        assert orders_resource.parent_id == 123
        assert orders_resource.relationship == "orders"

    def test_get_pledges(self):
        """Test getting pledges for an account."""
        pledges_resource = self.resource.get_pledges(123)

        assert pledges_resource.parent_id == 123
        assert pledges_resource.relationship == "pledges"

    def test_get_soft_credits(self):
        """Test getting soft credits for an account."""
        soft_credits_resource = self.resource.get_soft_credits(123)

        assert soft_credits_resource.parent_id == 123
        assert soft_credits_resource.relationship == "softCredits"

    def test_get_activities(self):
        """Test getting activities for an account."""
        activities_resource = self.resource.get_activities(123)

        assert activities_resource.parent_id == 123
        assert activities_resource.relationship == "activities"

    def test_get_addresses(self):
        """Test getting addresses for an account."""
        addresses_resource = self.resource.get_addresses(123)

        assert addresses_resource.parent_id == 123
        assert addresses_resource.relationship == "addresses"


class TestAccountsResourceLinking:
    """Test AccountsResource linking functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_client = Mock()
        self.mock_client.org_id = "test_org"
        self.mock_client.api_key = "test_key"
        self.mock_client.user_permissions = create_user_permissions(
            user_id="test_user", role=Role.ADMIN
        )
        self.resource = AccountsResource(self.mock_client)

    def test_link_accounts(self):
        """Test linking two accounts."""
        self.mock_client.post.return_value = {"status": "linked"}

        result = self.resource.link(123, 456)

        assert result["status"] == "linked"
        self.mock_client.post.assert_called_once_with(
            "/accounts/123/link/456", json_data={}
        )

    def test_unlink_accounts(self):
        """Test unlinking two accounts."""
        self.mock_client.delete.return_value = {"status": "unlinked"}

        result = self.resource.unlink(123, 456)

        assert result["status"] == "unlinked"
        self.mock_client.delete.assert_called_once_with("/accounts/123/link/456")

    def test_get_linked_accounts(self):
        """Test getting linked accounts."""
        self.mock_client.get.return_value = {
            "linkedAccounts": [
                {"accountId": 456, "linkType": "household"},
                {"accountId": 789, "linkType": "organization"},
            ]
        }

        result = self.resource.get_linked_accounts(123)

        assert len(result["linkedAccounts"]) == 2
        self.mock_client.get.assert_called_once_with("/accounts/123/link")


class TestAccountsResourceSearch:
    """Test AccountsResource search functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_client = Mock()
        self.mock_client.org_id = "test_org"
        self.mock_client.api_key = "test_key"
        self.mock_client.user_permissions = create_user_permissions(
            user_id="test_user", role=Role.ADMIN
        )
        self.resource = AccountsResource(self.mock_client)

    def test_search_accounts(self):
        """Test searching accounts."""
        search_request = {
            "searchFields": [
                {"field": "First Name", "operator": "EQUAL", "value": "John"}
            ],
            "outputFields": ["Account ID", "First Name", "Last Name"],
        }

        self.mock_client.post.return_value = {
            "searchResults": [
                {"Account ID": 123, "First Name": "John", "Last Name": "Doe"}
            ],
            "pagination": {"currentPage": 0, "totalPages": 1},
        }

        # Mock the validator to allow the search
        with patch.object(self.resource, "_validator") as mock_validator:
            mock_validator.validate_search_request.return_value = []

            result = list(self.resource.search(search_request))

            assert len(result) == 1
            assert result[0]["Account ID"] == 123

    def test_get_search_fields(self):
        """Test getting available search fields."""
        self.mock_client.get.return_value = {
            "standardFields": [
                {"fieldName": "First Name", "fieldType": "string"},
                {"fieldName": "Account ID", "fieldType": "number"},
            ],
            "customFields": [{"fieldName": "Custom Field 1", "fieldType": "text"}],
        }

        result = self.resource.get_search_fields()

        assert "standardFields" in result
        assert "customFields" in result
        self.mock_client.get.assert_called_once_with("/accounts/search/searchFields")

    def test_get_output_fields(self):
        """Test getting available output fields."""
        self.mock_client.get.return_value = {
            "standardFields": [{"fieldName": "First Name"}, {"fieldName": "Last Name"}]
        }

        result = self.resource.get_output_fields()

        assert "standardFields" in result
        self.mock_client.get.assert_called_once_with("/accounts/search/outputFields")


class TestAccountsResourceValidation:
    """Test AccountsResource validation logic."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_client = Mock()
        self.mock_client.org_id = "test_org"
        self.mock_client.api_key = "test_key"
        self.mock_client.user_permissions = create_user_permissions(
            user_id="test_user", role=Role.ADMIN
        )
        self.resource = AccountsResource(self.mock_client)

    def test_validate_user_type_enum(self):
        """Test user type validation with enum."""
        # Should not raise
        validated = self.resource._validate_user_type(UserType.INDIVIDUAL)
        assert validated == "INDIVIDUAL"

    def test_validate_user_type_string_valid(self):
        """Test user type validation with valid string."""
        validated = self.resource._validate_user_type("COMPANY")
        assert validated == "COMPANY"

    def test_validate_user_type_string_case_insensitive(self):
        """Test user type validation is case insensitive."""
        validated = self.resource._validate_user_type("individual")
        assert validated == "INDIVIDUAL"

    def test_validate_user_type_invalid(self):
        """Test user type validation with invalid value."""
        with pytest.raises(ValueError) as exc_info:
            self.resource._validate_user_type("INVALID")

        assert "must be one of" in str(exc_info.value)
        assert "INDIVIDUAL" in str(exc_info.value)
        assert "COMPANY" in str(exc_info.value)

    def test_validate_user_type_none(self):
        """Test user type validation with None."""
        with pytest.raises(ValueError) as exc_info:
            self.resource._validate_user_type(None)

        assert "must be one of" in str(exc_info.value)

    def test_user_type_validation_in_list(self):
        """Test that user type validation is called in list method."""
        with pytest.raises(ValueError):
            list(self.resource.list(user_type="INVALID"))

    def test_user_type_validation_before_api_call(self):
        """Test that validation happens before API call."""
        # This should fail validation before making any API calls
        with pytest.raises(ValueError):
            list(self.resource.list(user_type="INVALID"))

        # Verify no API calls were made
        self.mock_client.get.assert_not_called()


class TestAccountsResourceCustomFields:
    """Test AccountsResource custom fields functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_client = Mock()
        self.mock_client.org_id = "test_org"
        self.mock_client.api_key = "test_key"
        self.mock_client.user_permissions = create_user_permissions(
            user_id="test_user", role=Role.ADMIN
        )
        self.resource = AccountsResource(self.mock_client)

    def test_list_custom_fields(self):
        """Test listing custom fields for accounts."""
        mock_custom_fields = Mock()
        mock_custom_fields.list.return_value = iter(
            [
                {"id": 1, "name": "Preferred Contact Method"},
                {"id": 2, "name": "Donation Preference"},
            ]
        )
        self.mock_client.custom_fields = mock_custom_fields

        list(self.resource.list_custom_fields(field_type="text"))

        mock_custom_fields.list.assert_called_once_with(
            current_page=0,
            page_size=50,
            limit=None,
            field_type="text",
            category="ACCOUNT",
        )

    def test_get_custom_field(self):
        """Test getting specific custom field."""
        mock_custom_fields = Mock()
        mock_custom_fields.get.return_value = {"id": 123, "name": "Test Field"}
        self.mock_client.custom_fields = mock_custom_fields

        result = self.resource.get_custom_field(123)

        assert result["id"] == 123
        mock_custom_fields.get.assert_called_once_with(123)

    def test_find_custom_field_by_name(self):
        """Test finding custom field by name."""
        mock_custom_fields = Mock()
        mock_custom_fields.find_by_name_and_category.return_value = {
            "id": 123,
            "name": "Email Preference",
        }
        self.mock_client.custom_fields = mock_custom_fields

        result = self.resource.find_custom_field_by_name("Email Preference")

        assert result["id"] == 123
        mock_custom_fields.find_by_name_and_category.assert_called_once_with(
            "Email Preference", "ACCOUNT"
        )


class TestAccountsResourceIntegration:
    """Integration-style tests for AccountsResource."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_client = Mock()
        self.mock_client.org_id = "test_org"
        self.mock_client.api_key = "test_key"
        self.mock_client.user_permissions = create_user_permissions(
            user_id="test_user", role=Role.ADMIN
        )
        self.resource = AccountsResource(self.mock_client)

    def test_end_to_end_account_creation(self):
        """Test complete account creation workflow."""
        # Setup successful responses
        self.mock_client.post.return_value = {"accountId": 123}
        self.mock_client.get.return_value = {
            "individualAccount": {
                "accountId": 123,
                "firstName": "John",
                "lastName": "Doe",
            }
        }

        # Create account
        account_data = {
            "individualAccount": {
                "firstName": "John",
                "lastName": "Doe",
                "email": "john@example.com",
            }
        }

        create_result = self.resource.create(account_data)
        account_id = create_result["accountId"]

        # Get the created account
        account = self.resource.get(account_id)

        assert account["individualAccount"]["accountId"] == 123
        assert account["individualAccount"]["firstName"] == "John"

    def test_account_with_relationships(self):
        """Test account with its relationships."""
        account_id = 123

        # Get various relationship resources
        donations = self.resource.get_donations(account_id)
        memberships = self.resource.get_memberships(account_id)
        activities = self.resource.get_activities(account_id)

        # Verify they all point to the same account
        assert donations.parent_id == account_id
        assert memberships.parent_id == account_id
        assert activities.parent_id == account_id

        # Verify they have correct endpoints
        assert donations._endpoint == "/accounts/123/donations"
        assert memberships._endpoint == "/accounts/123/memberships"
        assert activities._endpoint == "/accounts/123/activities"

    def test_search_and_retrieve_workflow(self):
        """Test searching for accounts then retrieving specific ones."""
        # Mock search results
        self.mock_client.post.return_value = {
            "searchResults": [
                {"Account ID": 123, "First Name": "John"},
                {"Account ID": 456, "First Name": "Jane"},
            ],
            "pagination": {"currentPage": 0, "totalPages": 1},
        }

        # Mock individual account retrieval
        self.mock_client.get.return_value = {
            "individualAccount": {
                "accountId": 123,
                "firstName": "John",
                "lastName": "Doe",
            }
        }

        # Search for accounts
        search_request = {
            "searchFields": [
                {"field": "First Name", "operator": "CONTAIN", "value": "J"}
            ],
            "outputFields": ["Account ID", "First Name"],
        }

        with patch.object(self.resource, "_validator") as mock_validator:
            mock_validator.validate_search_request.return_value = []
            search_results = list(self.resource.search(search_request))

        # Get detailed info for first result
        account_id = search_results[0]["Account ID"]
        detailed_account = self.resource.get(account_id)

        assert len(search_results) == 2
        assert detailed_account["individualAccount"]["accountId"] == 123
