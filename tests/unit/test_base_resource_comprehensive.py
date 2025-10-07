"""Comprehensive unit tests for BaseResource - the foundation of all SDK resources."""

from unittest.mock import Mock, patch

import pytest

from neon_crm.resources.base import (
    BaseResource,
    ListableResource,
    RelationshipResource,
    SearchableResource,
    CalculationResource,
    PropertiesResource,
    NestedResource,
)
from neon_crm.types import CustomFieldCategory
from neon_crm.governance import create_user_permissions, Role, PermissionContext


class TestBaseResource:
    """Comprehensive tests for BaseResource."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_client = Mock()
        self.mock_client.user_permissions = create_user_permissions(
            user_id="test_user", role=Role.ADMIN
        )
        self.resource = BaseResource(self.mock_client, "/test")

    def test_initialization(self):
        """Test BaseResource initialization."""
        assert self.resource._client == self.mock_client
        assert self.resource._endpoint == "/test"

    def test_initialization_strips_trailing_slash(self):
        """Test that trailing slash is stripped from endpoint."""
        resource = BaseResource(self.mock_client, "/test/")
        assert resource._endpoint == "/test"

    def test_build_url_without_path(self):
        """Test building URL without additional path."""
        url = self.resource._build_url()
        assert url == "/test"

    def test_build_url_with_path(self):
        """Test building URL with additional path."""
        url = self.resource._build_url("123")
        assert url == "/test/123"

    def test_build_url_with_leading_slash_path(self):
        """Test building URL with path that has leading slash."""
        url = self.resource._build_url("/123")
        assert url == "/test/123"

    def test_build_url_complex_path(self):
        """Test building URL with complex path."""
        url = self.resource._build_url("123/edit")
        assert url == "/test/123/edit"

    def test_get_method(self):
        """Test the get method."""
        self.mock_client.get.return_value = {"id": 123, "name": "Test"}

        with PermissionContext(self.mock_client.user_permissions):
            result = self.resource.get(123)

        assert result == {"id": 123, "name": "Test"}
        self.mock_client.get.assert_called_once_with("/test/123")

    def test_create_method(self):
        """Test the create method."""
        data = {"name": "New Item"}
        self.mock_client.post.return_value = {"id": 456, "name": "New Item"}

        with PermissionContext(self.mock_client.user_permissions):
            result = self.resource.create(data)

        assert result == {"id": 456, "name": "New Item"}
        self.mock_client.post.assert_called_once_with("/test", json_data=data)

    def test_update_method(self):
        """Test the update method (defaults to partial/patch)."""
        data = {"name": "Updated Item"}
        self.mock_client.patch.return_value = {"id": 123, "name": "Updated Item"}

        with PermissionContext(self.mock_client.user_permissions):
            result = self.resource.update(123, data)

        assert result == {"id": 123, "name": "Updated Item"}
        self.mock_client.patch.assert_called_once_with("/test/123", json_data=data)

    def test_patch_method(self):
        """Test the patch method."""
        data = {"name": "Patched Item"}
        self.mock_client.patch.return_value = {"id": 123, "name": "Patched Item"}

        with PermissionContext(self.mock_client.user_permissions):
            result = self.resource.patch(123, data)

        assert result == {"id": 123, "name": "Patched Item"}
        self.mock_client.patch.assert_called_once_with("/test/123", json_data=data)

    def test_delete_method(self):
        """Test the delete method."""
        self.mock_client.delete.return_value = {"status": "deleted"}

        with PermissionContext(self.mock_client.user_permissions):
            result = self.resource.delete(123)

        assert result == {"status": "deleted"}
        self.mock_client.delete.assert_called_once_with("/test/123")

    def test_get_resource_category_accounts(self):
        """Test _get_resource_category for accounts."""
        resource = BaseResource(self.mock_client, "/accounts")
        category = resource._get_resource_category()
        assert category == CustomFieldCategory.ACCOUNT

    def test_get_resource_category_donations(self):
        """Test _get_resource_category for donations."""
        resource = BaseResource(self.mock_client, "/donations")
        category = resource._get_resource_category()
        assert category == CustomFieldCategory.DONATION

    def test_get_resource_category_unknown(self):
        """Test _get_resource_category for unknown endpoint."""
        resource = BaseResource(self.mock_client, "/unknown")
        category = resource._get_resource_category()
        assert category is None

    def test_list_custom_fields(self):
        """Test listing custom fields for the resource."""
        resource = BaseResource(self.mock_client, "/accounts")
        mock_custom_fields = Mock()
        mock_custom_fields.list.return_value = iter([{"id": 1, "name": "Custom Field"}])
        self.mock_client.custom_fields = mock_custom_fields

        list(resource.list_custom_fields(limit=10, field_type="text"))

        mock_custom_fields.list.assert_called_once_with(
            current_page=0,
            page_size=50,
            limit=10,
            field_type="text",
            category=CustomFieldCategory.ACCOUNT,
        )

    def test_list_custom_fields_unsupported_endpoint(self):
        """Test listing custom fields for unsupported endpoint."""
        resource = BaseResource(self.mock_client, "/unsupported")

        with pytest.raises(ValueError) as exc_info:
            list(resource.list_custom_fields())

        assert "Custom fields not supported" in str(exc_info.value)

    def test_get_custom_field(self):
        """Test getting a specific custom field."""
        mock_custom_fields = Mock()
        mock_custom_fields.get.return_value = {"id": 123, "name": "Test Field"}
        self.mock_client.custom_fields = mock_custom_fields

        with PermissionContext(self.mock_client.user_permissions):
            result = self.resource.get_custom_field(123)

        assert result == {"id": 123, "name": "Test Field"}
        mock_custom_fields.get.assert_called_once_with(123)

    def test_find_custom_field_by_name(self):
        """Test finding custom field by name."""
        resource = BaseResource(self.mock_client, "/accounts")
        mock_custom_fields = Mock()
        mock_custom_fields.find_by_name_and_category.return_value = {
            "id": 123,
            "name": "Test Field",
        }
        self.mock_client.custom_fields = mock_custom_fields

        result = resource.find_custom_field_by_name("Test Field")

        assert result == {"id": 123, "name": "Test Field"}
        mock_custom_fields.find_by_name_and_category.assert_called_once_with(
            "Test Field", CustomFieldCategory.ACCOUNT
        )

    def test_find_custom_field_by_name_unsupported_endpoint(self):
        """Test finding custom field by name for unsupported endpoint."""
        resource = BaseResource(self.mock_client, "/unsupported")

        with pytest.raises(ValueError) as exc_info:
            resource.find_custom_field_by_name("Test Field")

        assert "Custom fields not supported" in str(exc_info.value)


class TestSearchableResource:
    """Test the SearchableResource class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_client = Mock()
        self.mock_client.user_permissions = create_user_permissions(
            user_id="test_user", role=Role.ADMIN
        )
        # Mock custom_fields to return None (no custom field match)
        self.mock_client.custom_fields = Mock()
        self.mock_client.custom_fields.find_field_by_name.return_value = None
        self.resource = SearchableResource(self.mock_client, "/accounts")

    def test_initialization(self):
        """Test SearchableResource initialization."""
        assert self.resource._client == self.mock_client
        assert self.resource._endpoint == "/accounts"

    def test_get_search_fields_with_cache(self):
        """Test getting search fields with cache."""
        self.mock_client._cache = Mock()
        cache_mock = Mock()
        cache_mock.cache_get_or_set.return_value = {"fields": ["test"]}
        self.mock_client._cache.search_fields = cache_mock
        self.mock_client._cache.create_cache_key.return_value = "cache_key"

        with PermissionContext(self.mock_client.user_permissions):
            result = self.resource.get_search_fields()

        assert result == {"fields": ["test"]}
        cache_mock.cache_get_or_set.assert_called_once()

    def test_get_search_fields_without_cache(self):
        """Test getting search fields without cache."""
        self.mock_client._cache = None
        self.mock_client.get.return_value = {"fields": ["test"]}

        with PermissionContext(self.mock_client.user_permissions):
            result = self.resource.get_search_fields()

        assert result == {"fields": ["test"]}
        self.mock_client.get.assert_called_once_with("/accounts/search/searchFields")

    def test_get_output_fields_with_cache(self):
        """Test getting output fields with cache."""
        self.mock_client._cache = Mock()
        cache_mock = Mock()
        cache_mock.cache_get_or_set.return_value = {"fields": ["test"]}
        self.mock_client._cache.output_fields = cache_mock
        self.mock_client._cache.create_cache_key.return_value = "cache_key"

        with PermissionContext(self.mock_client.user_permissions):
            result = self.resource.get_output_fields()

        assert result == {"fields": ["test"]}
        cache_mock.cache_get_or_set.assert_called_once()

    def test_get_output_fields_without_cache(self):
        """Test getting output fields without cache."""
        self.mock_client._cache = None
        self.mock_client.get.return_value = {"fields": ["test"]}

        with PermissionContext(self.mock_client.user_permissions):
            result = self.resource.get_output_fields()

        assert result == {"fields": ["test"]}
        self.mock_client.get.assert_called_once_with("/accounts/search/outputFields")


class TestRelationshipResource:
    """Test the RelationshipResource class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_client = Mock()
        self.mock_client.user_permissions = create_user_permissions(
            user_id="test_user", role=Role.ADMIN
        )
        self.resource = RelationshipResource(
            self.mock_client, "/accounts", 123, "donations"
        )

    def test_initialization(self):
        """Test RelationshipResource initialization."""
        assert self.resource._client == self.mock_client
        assert self.resource.parent_id == 123
        assert self.resource.relationship == "donations"
        assert self.resource._endpoint == "/accounts/123/donations"

    def test_get_method(self):
        """Test get method for relationship resource."""
        self.mock_client.get.return_value = {"id": 456, "amount": 100}

        with PermissionContext(self.mock_client.user_permissions):
            result = self.resource.get(456)

        assert result == {"id": 456, "amount": 100}
        self.mock_client.get.assert_called_once_with("/accounts/123/donations/456")

    def test_create_method(self):
        """Test create method for relationship resource."""
        data = {"amount": 100}
        self.mock_client.post.return_value = {"id": 456, "amount": 100}

        with PermissionContext(self.mock_client.user_permissions):
            result = self.resource.create(data)

        assert result == {"id": 456, "amount": 100}
        self.mock_client.post.assert_called_once_with(
            "/accounts/123/donations", json_data=data
        )

    def test_update_method(self):
        """Test update method for relationship resource (defaults to partial/patch)."""
        data = {"amount": 150}
        self.mock_client.patch.return_value = {"id": 456, "amount": 150}

        with PermissionContext(self.mock_client.user_permissions):
            result = self.resource.update(456, data)

        assert result == {"id": 456, "amount": 150}
        self.mock_client.patch.assert_called_once_with(
            "/accounts/123/donations/456", json_data=data
        )

    def test_patch_method(self):
        """Test patch method for relationship resource."""
        data = {"amount": 125}
        self.mock_client.patch.return_value = {"id": 456, "amount": 125}

        with PermissionContext(self.mock_client.user_permissions):
            result = self.resource.patch(456, data)

        assert result == {"id": 456, "amount": 125}
        self.mock_client.patch.assert_called_once_with(
            "/accounts/123/donations/456", json_data=data
        )

    def test_delete_method(self):
        """Test delete method for relationship resource."""
        self.mock_client.delete.return_value = {"status": "deleted"}

        with PermissionContext(self.mock_client.user_permissions):
            result = self.resource.delete(456)

        assert result == {"status": "deleted"}
        self.mock_client.delete.assert_called_once_with("/accounts/123/donations/456")


class TestListableResource:
    """Test the ListableResource class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_client = Mock()
        self.mock_client.user_permissions = create_user_permissions(
            user_id="test_user", role=Role.ADMIN
        )
        self.resource = ListableResource(self.mock_client, "/accounts")

    def test_initialization(self):
        """Test ListableResource initialization."""
        assert self.resource._client == self.mock_client
        assert self.resource._endpoint == "/accounts"

    def test_list_method_basic(self):
        """Test basic list method."""
        self.mock_client.get.return_value = {
            "accounts": [{"id": 1}, {"id": 2}],
            "pagination": {"currentPage": 0, "totalPages": 1},
        }

        result = list(self.resource.list())

        assert result == [{"id": 1}, {"id": 2}]
        self.mock_client.get.assert_called_once()

    def test_list_method_with_limit(self):
        """Test list method with limit parameter."""
        self.mock_client.get.return_value = {
            "accounts": [{"id": 1}, {"id": 2}, {"id": 3}],
            "pagination": {"currentPage": 0, "totalPages": 1},
        }

        result = list(self.resource.list(limit=2))

        assert len(result) == 2
        assert result == [{"id": 1}, {"id": 2}]

    def test_list_method_direct_list_response(self):
        """Test list method with direct list response."""
        self.mock_client.get.return_value = [{"id": 1}, {"id": 2}]

        result = list(self.resource.list())

        assert result == [{"id": 1}, {"id": 2}]

    def test_list_method_with_pagination(self):
        """Test list method with multiple pages."""
        responses = [
            {
                "accounts": [{"id": 1}, {"id": 2}],
                "pagination": {"currentPage": 0, "totalPages": 2},
            },
            {
                "accounts": [{"id": 3}, {"id": 4}],
                "pagination": {"currentPage": 1, "totalPages": 2},
            },
        ]
        self.mock_client.get.side_effect = responses

        result = list(self.resource.list())

        assert result == [{"id": 1}, {"id": 2}, {"id": 3}, {"id": 4}]
        assert self.mock_client.get.call_count == 2

    def test_list_method_with_kwargs(self):
        """Test list method with additional parameters."""
        self.mock_client.get.return_value = {
            "accounts": [{"id": 1}],
            "pagination": {"currentPage": 0, "totalPages": 1},
        }

        result = list(self.resource.list(status="active", type="individual"))

        assert result == [{"id": 1}]
        call_args = self.mock_client.get.call_args
        assert call_args[1]["params"]["status"] == "active"
        assert call_args[1]["params"]["type"] == "individual"


class TestCalculationResource:
    """Test the CalculationResource class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_client = Mock()
        self.mock_client.user_permissions = create_user_permissions(
            user_id="test_user", role=Role.ADMIN
        )
        self.resource = CalculationResource(self.mock_client, "/memberships")

    def test_initialization(self):
        """Test CalculationResource initialization."""
        assert self.resource._client == self.mock_client
        assert self.resource._endpoint == "/memberships"

    def test_calculate_method_basic(self):
        """Test basic calculate method."""
        calculation_data = {"membershipTypeId": 1, "termId": 2}
        self.mock_client.post.return_value = {"totalCost": 100.0}

        with PermissionContext(self.mock_client.user_permissions):
            result = self.resource.calculate(calculation_data)

        assert result == {"totalCost": 100.0}
        self.mock_client.post.assert_called_once_with(
            "/memberships/calculate", json_data=calculation_data
        )

    def test_calculate_method_with_type(self):
        """Test calculate method with calculation type."""
        calculation_data = {"membershipTypeId": 1, "termId": 2}
        self.mock_client.post.return_value = {
            "startDate": "2024-01-01",
            "endDate": "2024-12-31",
        }

        with PermissionContext(self.mock_client.user_permissions):
            result = self.resource.calculate(calculation_data, "Dates")

        assert result == {"startDate": "2024-01-01", "endDate": "2024-12-31"}
        self.mock_client.post.assert_called_once_with(
            "/memberships/calculateDates", json_data=calculation_data
        )

    def test_calculate_method_fee_type(self):
        """Test calculate method with Fee type."""
        calculation_data = {"membershipTypeId": 1, "discountCode": "SAVE10"}
        self.mock_client.post.return_value = {
            "baseFee": 100.0,
            "discount": 10.0,
            "totalFee": 90.0,
        }

        with PermissionContext(self.mock_client.user_permissions):
            result = self.resource.calculate(calculation_data, "Fee")

        assert result == {"baseFee": 100.0, "discount": 10.0, "totalFee": 90.0}
        self.mock_client.post.assert_called_once_with(
            "/memberships/calculateFee", json_data=calculation_data
        )


class TestPropertiesResource:
    """Test the PropertiesResource class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_client = Mock()
        self.mock_client.user_permissions = create_user_permissions(
            user_id="test_user", role=Role.ADMIN
        )
        self.resource = PropertiesResource(self.mock_client)

    def test_initialization(self):
        """Test PropertiesResource initialization."""
        assert self.resource._client == self.mock_client
        assert self.resource._endpoint == "/properties"

    def test_initialization_custom_endpoint(self):
        """Test PropertiesResource initialization with custom endpoint."""
        resource = PropertiesResource(self.mock_client, "/custom/properties")
        assert resource._endpoint == "/custom/properties"

    def test_get_property_method(self):
        """Test get_property method."""
        self.mock_client.get.return_value = [
            {"id": 1, "name": "US"},
            {"id": 2, "name": "CA"},
        ]

        with PermissionContext(self.mock_client.user_permissions):
            result = self.resource.get_property("countries")

        assert result == [{"id": 1, "name": "US"}, {"id": 2, "name": "CA"}]
        self.mock_client.get.assert_called_once_with("/properties/countries")

    def test_get_countries_method(self):
        """Test get_countries convenience method."""
        self.mock_client.get.return_value = [{"id": 1, "name": "United States"}]

        with PermissionContext(self.mock_client.user_permissions):
            result = self.resource.get_countries()

        assert result == [{"id": 1, "name": "United States"}]
        self.mock_client.get.assert_called_once_with("/properties/countries")

    def test_get_genders_method(self):
        """Test get_genders convenience method."""
        self.mock_client.get.return_value = [
            {"id": 1, "name": "Male"},
            {"id": 2, "name": "Female"},
        ]

        with PermissionContext(self.mock_client.user_permissions):
            result = self.resource.get_genders()

        assert result == [{"id": 1, "name": "Male"}, {"id": 2, "name": "Female"}]
        self.mock_client.get.assert_called_once_with("/properties/genders")

    def test_get_system_users_method(self):
        """Test get_system_users convenience method."""
        self.mock_client.get.return_value = [{"id": 1, "name": "Admin User"}]

        with PermissionContext(self.mock_client.user_permissions):
            result = self.resource.get_system_users()

        assert result == [{"id": 1, "name": "Admin User"}]
        self.mock_client.get.assert_called_once_with("/properties/systemUsers")

    def test_get_current_system_user_method(self):
        """Test get_current_system_user convenience method."""
        self.mock_client.get.return_value = {
            "id": 1,
            "name": "Current User",
            "email": "user@example.com",
        }

        with PermissionContext(self.mock_client.user_permissions):
            result = self.resource.get_current_system_user()

        assert result == {"id": 1, "name": "Current User", "email": "user@example.com"}
        self.mock_client.get.assert_called_once_with("/properties/currentSystemUser")

    def test_get_organization_profile_method(self):
        """Test get_organization_profile convenience method."""
        self.mock_client.get.return_value = {"name": "Test Org", "id": 123}

        with PermissionContext(self.mock_client.user_permissions):
            result = self.resource.get_organization_profile()

        assert result == {"name": "Test Org", "id": 123}
        self.mock_client.get.assert_called_once_with("/properties/organizationProfile")


class TestNestedResource:
    """Test the NestedResource class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_client = Mock()
        self.mock_client.user_permissions = create_user_permissions(
            user_id="test_user", role=Role.ADMIN
        )
        self.resource = NestedResource(self.mock_client, "/accounts", 123, "contacts")

    def test_initialization_without_child_id(self):
        """Test NestedResource initialization without child ID."""
        assert self.resource._client == self.mock_client
        assert self.resource._parent_endpoint == "/accounts"
        assert self.resource.parent_id == 123
        assert self.resource.child_resource == "contacts"
        assert self.resource.child_id is None
        assert self.resource._endpoint == "/accounts/123/contacts"

    def test_initialization_with_child_id(self):
        """Test NestedResource initialization with child ID."""
        resource = NestedResource(self.mock_client, "/accounts", 123, "contacts", 456)
        assert resource.child_id == 456
        assert resource._endpoint == "/accounts/123/contacts/456"

    def test_list_method_list_response(self):
        """Test list method with direct list response."""
        self.mock_client.get.return_value = [{"id": 1}, {"id": 2}]

        result = list(self.resource.list())

        assert result == [{"id": 1}, {"id": 2}]
        self.mock_client.get.assert_called_once_with(
            "/accounts/123/contacts", params={}
        )

    def test_list_method_nested_response(self):
        """Test list method with nested response structure."""
        self.mock_client.get.return_value = {"contacts": [{"id": 1}, {"id": 2}]}

        result = list(self.resource.list())

        assert result == [{"id": 1}, {"id": 2}]

    def test_list_method_single_item_response(self):
        """Test list method with single item response."""
        self.mock_client.get.return_value = {"id": 1, "name": "Contact"}

        result = list(self.resource.list())

        assert result == [{"id": 1, "name": "Contact"}]

    def test_list_method_with_child_id_raises_error(self):
        """Test that list method raises error when child_id is set."""
        resource = NestedResource(self.mock_client, "/accounts", 123, "contacts", 456)

        with pytest.raises(ValueError, match="Cannot list when child_id is specified"):
            list(resource.list())

    def test_get_child_method(self):
        """Test get_child method."""
        self.mock_client.get.return_value = {"id": 456, "name": "Contact"}

        with PermissionContext(self.mock_client.user_permissions):
            result = self.resource.get_child(456)

        assert result == {"id": 456, "name": "Contact"}
        self.mock_client.get.assert_called_once_with("/accounts/123/contacts/456")

    def test_create_child_method(self):
        """Test create_child method."""
        data = {"name": "New Contact", "email": "test@example.com"}
        self.mock_client.post.return_value = {
            "id": 456,
            "name": "New Contact",
            "email": "test@example.com",
        }

        with PermissionContext(self.mock_client.user_permissions):
            result = self.resource.create_child(data)

        assert result == {"id": 456, "name": "New Contact", "email": "test@example.com"}
        self.mock_client.post.assert_called_once_with(
            "/accounts/123/contacts", json_data=data
        )

    def test_update_child_method(self):
        """Test update_child method."""
        data = {"name": "Updated Contact"}
        self.mock_client.put.return_value = {"id": 456, "name": "Updated Contact"}

        with PermissionContext(self.mock_client.user_permissions):
            result = self.resource.update_child(456, data)

        assert result == {"id": 456, "name": "Updated Contact"}
        self.mock_client.put.assert_called_once_with(
            "/accounts/123/contacts/456", json_data=data
        )

    def test_patch_child_method(self):
        """Test patch_child method."""
        data = {"email": "updated@example.com"}
        self.mock_client.patch.return_value = {
            "id": 456,
            "email": "updated@example.com",
        }

        with PermissionContext(self.mock_client.user_permissions):
            result = self.resource.patch_child(456, data)

        assert result == {"id": 456, "email": "updated@example.com"}
        self.mock_client.patch.assert_called_once_with(
            "/accounts/123/contacts/456", json_data=data
        )

    def test_delete_child_method(self):
        """Test delete_child method."""
        self.mock_client.delete.return_value = {"status": "deleted"}

        with PermissionContext(self.mock_client.user_permissions):
            result = self.resource.delete_child(456)

        assert result == {"status": "deleted"}
        self.mock_client.delete.assert_called_once_with("/accounts/123/contacts/456")
