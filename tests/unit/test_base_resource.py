"""Unit tests for base resource classes."""

import pytest

from neon_crm.resources.base import (
    BaseResource,
    ListableResource,
    RelationshipResource,
    SearchableResource,
)
from neon_crm.types import SearchRequest


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
        result = resource.get(123)

        assert result == {"id": 123, "name": "Test"}
        mock_client.get.assert_called_once_with("/test/123")

    def test_create_method(self, mock_client):
        """Test CREATE request method."""
        test_data = {"name": "New Item"}
        mock_client.post.return_value = {"id": 456, "name": "New Item"}

        resource = BaseResource(mock_client, "/test")
        result = resource.create(test_data)

        assert result == {"id": 456, "name": "New Item"}
        mock_client.post.assert_called_once_with("/test", json_data=test_data)

    def test_update_method(self, mock_client):
        """Test UPDATE request method."""
        test_data = {"name": "Updated Item"}
        mock_client.put.return_value = {"id": 123, "name": "Updated Item"}

        resource = BaseResource(mock_client, "/test")
        result = resource.update(123, test_data)

        assert result == {"id": 123, "name": "Updated Item"}
        mock_client.put.assert_called_once_with("/test/123", json_data=test_data)

    def test_patch_method(self, mock_client):
        """Test PATCH request method."""
        test_data = {"name": "Patched Item"}
        mock_client.patch.return_value = {"id": 123, "name": "Patched Item"}

        resource = BaseResource(mock_client, "/test")
        result = resource.patch(123, test_data)

        assert result == {"id": 123, "name": "Patched Item"}
        mock_client.patch.assert_called_once_with("/test/123", json_data=test_data)

    def test_delete_method(self, mock_client):
        """Test DELETE request method."""
        mock_client.delete.return_value = {"success": True}

        resource = BaseResource(mock_client, "/test")
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
        # Mock two pages of results
        page1_response = {
            "pagination": {"currentPage": 1, "totalPages": 2},
            "test": [{"id": 1}, {"id": 2}],
        }
        page2_response = {
            "pagination": {"currentPage": 2, "totalPages": 2},
            "test": [{"id": 3}, {"id": 4}],
        }

        mock_client.get.side_effect = [page1_response, page2_response]

        resource = ListableResource(mock_client, "/test")
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

        # Test create
        test_data = {"firstName": "John", "lastName": "Doe"}
        mock_client.post.return_value = {"id": 456, **test_data}

        result = resource.create(test_data)
        assert result["firstName"] == "John"

        # Test get
        mock_client.get.return_value = {"id": 456, "firstName": "John"}
        result = resource.get(456)
        assert result["id"] == 456
