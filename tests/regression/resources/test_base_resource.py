"""Tests for BaseResource functionality.

These tests validate the core functionality that all resources inherit,
particularly the fixes for the limit parameter issues.
"""

from unittest.mock import Mock

import pytest

from neon_crm.resources.base import BaseResource


class TestBaseResourceLimitFixes:
    """Test the critical limit parameter fixes in BaseResource."""

    def test_limit_none_handling_fixed(self):
        """Test that limit=None no longer crashes (critical fix)."""
        # Create a mock client
        mock_client = Mock()

        # Mock response that would be returned by the API
        mock_response = {
            "searchResults": [
                {"id": 1, "name": "Item 1"},
                {"id": 2, "name": "Item 2"},
                {"id": 3, "name": "Item 3"},
            ],
            "pagination": {
                "currentPage": 0,
                "pageSize": 50,
                "totalPages": 1,
                "totalResults": 3,
            },
        }

        mock_client.get.return_value = mock_response

        # Create a BaseResource instance
        resource = BaseResource(mock_client, "/test")

        # This should NOT crash with limit=None (was crashing before fix)
        try:
            results = list(resource.list(limit=None))
            print(f"✓ FIXED: limit=None works without crash, got {len(results)} items")
            assert len(results) == 3, "Should return all items when limit=None"
        except TypeError as e:
            if "unsupported operand type(s) for <" in str(e):
                print(f"❌ CRITICAL: limit=None still crashes with TypeError: {e}")
                pytest.fail("limit=None comparison bug not fixed")
            else:
                raise

    def test_limit_parameter_enforcement(self):
        """Test that limit parameter is properly enforced."""
        mock_client = Mock()

        # Mock response with more items than limit
        mock_response = {
            "searchResults": [
                {"id": 1, "name": "Item 1"},
                {"id": 2, "name": "Item 2"},
                {"id": 3, "name": "Item 3"},
                {"id": 4, "name": "Item 4"},
                {"id": 5, "name": "Item 5"},
            ],
            "pagination": {
                "currentPage": 0,
                "pageSize": 50,
                "totalPages": 1,
                "totalResults": 5,
            },
        }

        mock_client.get.return_value = mock_response
        resource = BaseResource(mock_client, "/test")

        # Test limit=3 should only return 3 items
        results = list(resource.list(limit=3))
        assert len(results) == 3, f"limit=3 should return 3 items, got {len(results)}"
        print("✓ FIXED: limit parameter properly enforced")

        # Test limit=0 should return 0 items
        results = list(resource.list(limit=0))
        assert len(results) == 0, f"limit=0 should return 0 items, got {len(results)}"
        print("✓ limit=0 edge case works correctly")

    def test_limit_with_pagination(self):
        """Test limit parameter works correctly across multiple pages."""
        mock_client = Mock()

        # Mock first page response
        first_page_response = {
            "searchResults": [
                {"id": 1, "name": "Item 1"},
                {"id": 2, "name": "Item 2"},
            ],
            "pagination": {
                "currentPage": 0,
                "pageSize": 2,
                "totalPages": 3,
                "totalResults": 6,
            },
        }

        # Mock second page response
        second_page_response = {
            "searchResults": [
                {"id": 3, "name": "Item 3"},
                {"id": 4, "name": "Item 4"},
            ],
            "pagination": {
                "currentPage": 1,
                "pageSize": 2,
                "totalPages": 3,
                "totalResults": 6,
            },
        }

        # Set up client to return different responses for different calls
        mock_client.get.side_effect = [first_page_response, second_page_response]
        resource = BaseResource(mock_client, "/test")

        # Test limit=3 with page_size=2 should stop after getting 3 items
        results = list(resource.list(page_size=2, limit=3))

        # Should get 2 from first page + 1 from second page = 3 total
        assert (
            len(results) == 3
        ), f"limit=3 with pagination should return 3 items, got {len(results)}"
        print("✓ FIXED: limit parameter works correctly with pagination")

    def test_different_response_structures(self):
        """Test that BaseResource handles different API response structures."""
        mock_client = Mock()
        resource = BaseResource(mock_client, "/test")

        # Test 1: searchResults structure (most common)
        search_results_response = {
            "searchResults": [{"id": 1}, {"id": 2}],
            "pagination": {"currentPage": 0},
        }

        mock_client.get.return_value = search_results_response
        results = list(resource.list(limit=5))
        assert len(results) == 2
        print("✓ searchResults response structure handled correctly")

        # Test 2: Direct list response
        mock_client.get.return_value = [{"id": 1}, {"id": 2}, {"id": 3}]
        results = list(resource.list(limit=2))
        assert len(results) == 2
        print("✓ Direct list response structure handled correctly")

        # Test 3: Data wrapper response
        data_wrapper_response = {
            "data": [{"id": 1}, {"id": 2}],
            "pagination": {"currentPage": 0},
        }

        mock_client.get.return_value = data_wrapper_response
        results = list(resource.list(limit=5))
        assert len(results) == 2
        print("✓ Data wrapper response structure handled correctly")


class TestBaseResourceOtherMethods:
    """Test other BaseResource methods for completeness."""

    def test_build_url_method(self):
        """Test the _build_url method."""
        mock_client = Mock()
        resource = BaseResource(mock_client, "/test")

        # Test base URL
        assert resource._build_url() == "/test"

        # Test with path
        assert resource._build_url("123") == "/test/123"
        assert (
            resource._build_url("/123") == "/test/123"
        )  # Leading slash should be handled

        print("✓ _build_url method works correctly")

    def test_get_method(self):
        """Test the get method."""
        mock_client = Mock()
        mock_client.get.return_value = {"id": 123, "name": "Test Item"}

        resource = BaseResource(mock_client, "/test")
        result = resource.get(123)

        # Verify the client was called with correct URL
        mock_client.get.assert_called_once_with("/test/123")
        assert result == {"id": 123, "name": "Test Item"}

        print("✓ get method works correctly")

    def test_create_method(self):
        """Test the create method."""
        mock_client = Mock()
        mock_client.post.return_value = {"id": 456, "name": "Created Item"}

        resource = BaseResource(mock_client, "/test")
        data = {"name": "New Item"}
        result = resource.create(data)

        # Verify the client was called with correct parameters
        mock_client.post.assert_called_once_with("/test", json_data=data)
        assert result == {"id": 456, "name": "Created Item"}

        print("✓ create method works correctly")

    def test_update_method(self):
        """Test the update method."""
        mock_client = Mock()
        mock_client.put.return_value = {"id": 123, "name": "Updated Item"}

        resource = BaseResource(mock_client, "/test")
        data = {"name": "Updated Item"}
        result = resource.update(123, data)

        # Verify the client was called with correct parameters
        mock_client.put.assert_called_once_with("/test/123", json_data=data)
        assert result == {"id": 123, "name": "Updated Item"}

        print("✓ update method works correctly")

    def test_patch_method(self):
        """Test the patch method."""
        mock_client = Mock()
        mock_client.patch.return_value = {"id": 123, "name": "Patched Item"}

        resource = BaseResource(mock_client, "/test")
        data = {"name": "Patched Item"}
        result = resource.patch(123, data)

        # Verify the client was called with correct parameters
        mock_client.patch.assert_called_once_with("/test/123", json_data=data)
        assert result == {"id": 123, "name": "Patched Item"}

        print("✓ patch method works correctly")

    def test_delete_method(self):
        """Test the delete method."""
        mock_client = Mock()
        mock_client.delete.return_value = {"success": True}

        resource = BaseResource(mock_client, "/test")
        result = resource.delete(123)

        # Verify the client was called with correct parameters
        mock_client.delete.assert_called_once_with("/test/123", params=None)
        assert result == {"success": True}

        print("✓ delete method works correctly")
