"""Unit tests for base resource classes."""

import pytest
from unittest.mock import MagicMock

from neon_crm.resources.base import (
    BaseResource,
    ListableResource,
    RelationshipResource,
    SearchableResource,
)
from neon_crm.types import SearchRequest
from neon_crm.governance import PermissionContext


@pytest.mark.unit
class TestBaseResource:
    """Test cases for BaseResource class."""

    def test_initialization(self, mock_client):
        """Test BaseResource initialization."""
        resource = BaseResource(mock_client, "/test")

        assert resource._client == mock_client
        assert resource._endpoint == "/test"

    def test_build_url_with_path(self, mock_client):
        """Test URL building with additional path."""
        resource = BaseResource(mock_client, "/test")

        url = resource._build_url("123")
        assert url == "/test/123"

        url = resource._build_url("/123")
        assert url == "/test/123"

    def test_build_url_without_path(self, mock_client):
        """Test URL building without additional path."""
        resource = BaseResource(mock_client, "/test")

        url = resource._build_url()
        assert url == "/test"

    def test_get_method(self, mock_client, mock_successful_response):
        """Test GET request method."""
        mock_client.get.return_value = {"id": 123, "name": "Test"}

        resource = BaseResource(mock_client, "/test")

        with PermissionContext(mock_client.user_permissions):
            result = resource.get(123)

        assert result == {"id": 123, "name": "Test"}
        mock_client.get.assert_called_once_with("/test/123")

    def test_create_method(self, mock_client):
        """Test CREATE request method."""
        test_data = {"name": "New Item"}
        mock_client.post.return_value = {"id": 456, "name": "New Item"}

        resource = BaseResource(mock_client, "/test")

        with PermissionContext(mock_client.user_permissions):
            result = resource.create(test_data)

        assert result == {"id": 456, "name": "New Item"}
        mock_client.post.assert_called_once_with("/test", json_data=test_data)

    def test_update_method_default_partial(self, mock_client):
        """Test UPDATE request method with default partial update."""
        test_data = {"name": "Updated Item"}
        mock_client.patch.return_value = {"id": 123, "name": "Updated Item"}

        resource = BaseResource(mock_client, "/test")

        with PermissionContext(mock_client.user_permissions):
            result = resource.update(123, test_data)

        assert result == {"id": 123, "name": "Updated Item"}
        mock_client.patch.assert_called_once_with("/test/123", json_data=test_data)

    def test_update_method_partial_explicit(self, mock_client):
        """Test UPDATE request method with explicit partial update."""
        test_data = {"name": "Updated Item"}
        mock_client.patch.return_value = {"id": 123, "name": "Updated Item"}

        resource = BaseResource(mock_client, "/test")

        with PermissionContext(mock_client.user_permissions):
            result = resource.update(123, test_data, update_type="partial")

        assert result == {"id": 123, "name": "Updated Item"}
        mock_client.patch.assert_called_once_with("/test/123", json_data=test_data)

    def test_update_method_full(self, mock_client):
        """Test UPDATE request method with full update."""
        test_data = {"name": "Updated Item"}
        mock_client.put.return_value = {"id": 123, "name": "Updated Item"}

        resource = BaseResource(mock_client, "/test")

        with PermissionContext(mock_client.user_permissions):
            result = resource.update(123, test_data, update_type="full")

        assert result == {"id": 123, "name": "Updated Item"}
        mock_client.put.assert_called_once_with("/test/123", json_data=test_data)

    def test_update_method_invalid_type(self, mock_client):
        """Test UPDATE request method with invalid update type."""
        test_data = {"name": "Updated Item"}

        resource = BaseResource(mock_client, "/test")

        with pytest.raises(ValueError, match="Invalid update_type 'invalid'"):
            resource.update(123, test_data, update_type="invalid")

    def test_put_method(self, mock_client):
        """Test direct PUT request method."""
        test_data = {"name": "Updated Item"}
        mock_client.put.return_value = {"id": 123, "name": "Updated Item"}

        resource = BaseResource(mock_client, "/test")

        with PermissionContext(mock_client.user_permissions):
            result = resource.put(123, test_data)

        assert result == {"id": 123, "name": "Updated Item"}
        mock_client.put.assert_called_once_with("/test/123", json_data=test_data)

    def test_patch_method(self, mock_client):
        """Test PATCH request method."""
        test_data = {"name": "Patched Item"}
        mock_client.patch.return_value = {"id": 123, "name": "Patched Item"}

        resource = BaseResource(mock_client, "/test")

        with PermissionContext(mock_client.user_permissions):
            result = resource.patch(123, test_data)

        assert result == {"id": 123, "name": "Patched Item"}
        mock_client.patch.assert_called_once_with("/test/123", json_data=test_data)

    def test_delete_method(self, mock_client):
        """Test DELETE request method."""
        mock_client.delete.return_value = {"success": True}

        resource = BaseResource(mock_client, "/test")

        with PermissionContext(mock_client.user_permissions):
            result = resource.delete(123)

        assert result == {"success": True}
        mock_client.delete.assert_called_once_with("/test/123")

    def test_list_method_with_endpoint_key(self, mock_client):
        """Test LIST method with endpoint-named key response."""
        mock_response = {
            "pagination": {"currentPage": 1, "totalPages": 1},
            "test": [{"id": 1}, {"id": 2}],
        }
        mock_client.get.return_value = mock_response

        resource = ListableResource(mock_client, "/test")
        results = list(resource.list(page_size=10))

        assert len(results) == 2
        assert results[0] == {"id": 1}
        assert results[1] == {"id": 2}

    def test_list_method_with_direct_list(self, mock_client):
        """Test LIST method with direct list response."""
        mock_response = [{"id": 1}, {"id": 2}]
        mock_client.get.return_value = mock_response

        resource = ListableResource(mock_client, "/test")
        results = list(resource.list())

        assert len(results) == 2
        assert results[0] == {"id": 1}
        assert results[1] == {"id": 2}

    def test_list_method_pagination(self, mock_client):
        """Test LIST method with pagination."""
        # Mock two pages of results (0-indexed)
        page1_response = {
            "pagination": {"currentPage": 0, "totalPages": 2},
            "test": [{"id": 1}, {"id": 2}],
        }
        page2_response = {
            "pagination": {"currentPage": 1, "totalPages": 2},
            "test": [{"id": 3}, {"id": 4}],
        }

        mock_client.get.side_effect = [page1_response, page2_response]

        resource = ListableResource(mock_client, "/test")

        with PermissionContext(mock_client.user_permissions):
            results = list(resource.list(page_size=2))

        assert len(results) == 4
        assert mock_client.get.call_count == 2


@pytest.mark.unit
class TestSearchableResource:
    """Test cases for SearchableResource class."""

    def test_search_method(self, mock_client):
        """Test search functionality."""
        search_request: SearchRequest = {
            "searchFields": [{"field": "name", "operator": "EQUAL", "value": "test"}],
            "outputFields": ["id", "name"],
        }

        mock_response = {
            "pagination": {"currentPage": 1, "totalPages": 1},
            "searchResults": [{"id": 1, "name": "test"}],
        }
        mock_client.post.return_value = mock_response

        resource = SearchableResource(mock_client, "/test")
        results = list(resource.search(search_request))

        assert len(results) == 1
        assert results[0] == {"id": 1, "name": "test"}
        mock_client.post.assert_called_once()

    def test_get_search_fields(self, mock_client):
        """Test get_search_fields method."""
        mock_response = {
            "standardFields": [
                {"fieldName": "name", "operators": ["EQUAL"]},
                {"fieldName": "id", "operators": ["EQUAL"]},
            ]
        }
        mock_client.get.return_value = mock_response
        # Mock cache to None to bypass caching
        mock_client._cache = None

        resource = SearchableResource(mock_client, "/test")
        fields = resource.get_search_fields()

        assert isinstance(fields, dict)
        assert "standardFields" in fields
        assert len(fields["standardFields"]) == 2
        mock_client.get.assert_called_once_with("/test/search/searchFields")

    def test_get_output_fields(self, mock_client):
        """Test get_output_fields method."""
        mock_response = {
            "standardFields": [
                {"fieldName": "id", "dataType": "integer"},
                {"fieldName": "name", "dataType": "string"},
            ]
        }
        mock_client.get.return_value = mock_response
        # Mock cache to None to bypass caching
        mock_client._cache = None

        resource = SearchableResource(mock_client, "/test")
        fields = resource.get_output_fields()

        assert isinstance(fields, dict)
        assert "standardFields" in fields
        assert len(fields["standardFields"]) == 2
        mock_client.get.assert_called_once_with("/test/search/outputFields")

    def test_convert_field_names_to_ids_search_fields(self, mock_client):
        """Test conversion of custom field names to IDs in search fields."""
        # Mock the resource category mapping
        resource = SearchableResource(mock_client, "/accounts")

        # Mock custom fields resource
        mock_custom_fields = MagicMock()

        def mock_find_by_name(field_name, category):
            if field_name == "My Custom Field":
                return {
                    "id": 123,
                    "name": "My Custom Field",
                    "displayName": "My Custom Field",
                }
            return None  # Return None for standard fields like "firstName"

        mock_custom_fields.find_by_name_and_category.side_effect = mock_find_by_name
        mock_client.custom_fields = mock_custom_fields

        search_request: SearchRequest = {
            "searchFields": [
                {"field": "My Custom Field", "operator": "EQUAL", "value": "test"},
                {
                    "field": "firstName",
                    "operator": "EQUAL",
                    "value": "John",
                },  # Standard field
                {
                    "field": "456",
                    "operator": "EQUAL",
                    "value": "existing",
                },  # Already an ID
            ],
            "outputFields": ["id", "firstName"],
        }

        result = resource._convert_field_names_to_ids(search_request)

        # Verify custom field name was converted to string ID
        assert result["searchFields"][0]["field"] == "123"
        assert result["searchFields"][0]["operator"] == "EQUAL"
        assert result["searchFields"][0]["value"] == "test"

        # Verify standard field unchanged
        assert result["searchFields"][1]["field"] == "firstName"

        # Verify existing ID unchanged
        assert result["searchFields"][2]["field"] == "456"

        # Verify custom field lookup was called for the custom field
        calls = mock_client.custom_fields.find_by_name_and_category.call_args_list
        assert any(
            call[0] == ("My Custom Field", resource._get_resource_category())
            for call in calls
        )

    def test_convert_field_names_to_ids_output_fields(self, mock_client):
        """Test conversion of custom field names to IDs in output fields."""
        resource = SearchableResource(mock_client, "/accounts")

        # Mock custom fields resource
        mock_custom_fields = MagicMock()

        def mock_find_by_name(field_name, category):
            if field_name == "Another Custom Field":
                return {
                    "id": 789,
                    "name": "Another Custom Field",
                    "displayName": "Another Custom Field",
                }
            return None  # Return None for standard fields

        mock_custom_fields.find_by_name_and_category.side_effect = mock_find_by_name
        mock_client.custom_fields = mock_custom_fields

        search_request: SearchRequest = {
            "searchFields": [],
            "outputFields": ["id", "Another Custom Field", "firstName", 999, "123"],
        }

        result = resource._convert_field_names_to_ids(search_request)

        # Check output fields conversion
        expected_output = ["id", 789, "firstName", 999, "123"]
        assert result["outputFields"] == expected_output

    def test_convert_field_names_to_ids_field_not_found(self, mock_client):
        """Test behavior when custom field name is not found."""
        resource = SearchableResource(mock_client, "/accounts")

        # Mock custom fields resource
        mock_custom_fields = MagicMock()
        mock_custom_fields.find_by_name_and_category.return_value = None
        mock_client.custom_fields = mock_custom_fields

        search_request: SearchRequest = {
            "searchFields": [
                {"field": "Nonexistent Field", "operator": "EQUAL", "value": "test"}
            ],
            "outputFields": ["Nonexistent Output Field"],
        }

        result = resource._convert_field_names_to_ids(search_request)

        # Verify fields remain unchanged when not found
        assert result["searchFields"][0]["field"] == "Nonexistent Field"
        assert result["outputFields"][0] == "Nonexistent Output Field"

    def test_convert_field_names_to_ids_no_category(self, mock_client):
        """Test behavior when resource has no custom field category mapping."""
        # Use a resource that doesn't have a category mapping
        resource = SearchableResource(mock_client, "/unknown")

        search_request: SearchRequest = {
            "searchFields": [
                {"field": "Some Field", "operator": "EQUAL", "value": "test"}
            ],
            "outputFields": ["Some Output Field"],
        }

        result = resource._convert_field_names_to_ids(search_request)

        # Verify fields remain unchanged when no category mapping
        assert result["searchFields"][0]["field"] == "Some Field"
        assert result["outputFields"][0] == "Some Output Field"

        # Verify no custom field lookup was attempted (no custom_fields attribute set)

    def test_convert_field_names_to_ids_integration(self, mock_client):
        """Test full integration of field name conversion in search preparation."""
        resource = SearchableResource(mock_client, "/accounts")

        # Mock custom fields resource
        mock_custom_fields = MagicMock()

        def mock_find_by_name(field_name, category):
            if field_name == "Integration Test Field":
                return {
                    "id": 555,
                    "name": "Integration Test Field",
                    "displayName": "Integration Test Field",
                }
            return None  # Return None for standard fields

        mock_custom_fields.find_by_name_and_category.side_effect = mock_find_by_name
        mock_client.custom_fields = mock_custom_fields

        # Mock get_output_fields to prevent wildcard expansion
        mock_client.get.return_value = {
            "standardFields": ["id", "firstName"],
            "customFields": [],
        }
        resource._client._cache = None

        search_request: SearchRequest = {
            "searchFields": [
                {"field": "Integration Test Field", "operator": "EQUAL", "value": 42}
            ],
            "outputFields": ["Integration Test Field", "firstName"],
        }

        result = resource._prepare_search_request(search_request)

        # Verify custom field name was converted and value was converted to string
        assert result["searchFields"][0]["field"] == "555"
        assert (
            result["searchFields"][0]["value"] == "42"
        )  # Should be string after type conversion

        # Verify output field was converted to integer
        assert 555 in result["outputFields"]
        assert "firstName" in result["outputFields"]

    def test_convert_field_names_with_spaces_and_special_chars(self, mock_client):
        """Test that field names with spaces and special characters are processed correctly."""
        resource = SearchableResource(mock_client, "/accounts")

        # Mock custom fields resource
        mock_custom_fields = MagicMock()

        def mock_find_by_name(field_name, category):
            field_mapping = {
                "V-Volunteer Skills": {"id": 100, "name": "V-Volunteer Skills"},
                "Volunteer Status - Current": {
                    "id": 200,
                    "name": "Volunteer Status - Current",
                },
                "Custom Notes": {"id": 300, "name": "Custom Notes"},
            }
            return field_mapping.get(field_name)

        mock_custom_fields.find_by_name_and_category.side_effect = mock_find_by_name
        mock_client.custom_fields = mock_custom_fields

        search_request: SearchRequest = {
            "searchFields": [
                {
                    "field": "V-Volunteer Skills",
                    "operator": "EQUAL",
                    "value": "canvassing",
                },
                {
                    "field": "firstName",
                    "operator": "EQUAL",
                    "value": "John",
                },  # Standard field
                {
                    "field": "123",
                    "operator": "EQUAL",
                    "value": "existing",
                },  # Existing ID
            ],
            "outputFields": [
                "Volunteer Status - Current",
                "Custom Notes",
                "lastName",
                456,
            ],
        }

        result = resource._convert_field_names_to_ids(search_request)

        # Verify custom field names with spaces/special chars were converted
        assert result["searchFields"][0]["field"] == "100"
        assert (
            result["searchFields"][1]["field"] == "firstName"
        )  # Standard field unchanged
        assert result["searchFields"][2]["field"] == "123"  # Existing ID unchanged

        # Verify output fields
        expected_output = [200, 300, "lastName", 456]
        assert result["outputFields"] == expected_output

    def test_standard_field_check_avoids_custom_field_lookup(self, mock_client):
        """Test that standard fields are detected and don't trigger custom field lookups."""
        resource = SearchableResource(mock_client, "/accounts")

        # Mock get_output_fields to return standard fields
        mock_client.get.return_value = {
            "standardFields": ["firstName", "lastName", "email"],
            "customFields": [],
        }

        # Disable cache to ensure get_output_fields is called
        resource._client._cache = None

        # Mock custom fields resource (should not be called for standard fields)
        mock_custom_fields = MagicMock()
        mock_client.custom_fields = mock_custom_fields

        search_request: SearchRequest = {
            "searchFields": [
                {
                    "field": "firstName",
                    "operator": "EQUAL",
                    "value": "John",
                },  # Standard field
                {
                    "field": "lastName",
                    "operator": "EQUAL",
                    "value": "Doe",
                },  # Standard field
            ],
            "outputFields": ["firstName", "email"],  # Standard fields
        }

        result = resource._convert_field_names_to_ids(search_request)

        # Verify standard fields remain unchanged
        assert result["searchFields"][0]["field"] == "firstName"
        assert result["searchFields"][1]["field"] == "lastName"
        assert result["outputFields"] == ["firstName", "email"]

        # Verify custom field lookup was NOT called for standard fields
        mock_custom_fields.find_by_name_and_category.assert_not_called()


@pytest.mark.unit
class TestRelationshipResource:
    """Test cases for RelationshipResource class."""

    def test_initialization(self, mock_client):
        """Test RelationshipResource initialization."""
        resource = RelationshipResource(mock_client, "/accounts", 123, "contacts")

        assert resource._client == mock_client
        assert resource.parent_id == 123
        assert resource.relationship == "contacts"
        assert resource._endpoint == "/accounts/123/contacts"

    def test_crud_operations(self, mock_client):
        """Test CRUD operations for relationship resource."""
        resource = RelationshipResource(mock_client, "/accounts", 123, "contacts")

        with PermissionContext(mock_client.user_permissions):
            # Test create
            test_data = {"firstName": "John", "lastName": "Doe"}
            mock_client.post.return_value = {"id": 456, **test_data}

            result = resource.create(test_data)
            assert result["firstName"] == "John"

            # Test get
            mock_client.get.return_value = {"id": 456, "firstName": "John"}
            result = resource.get(456)
            assert result["id"] == 456
