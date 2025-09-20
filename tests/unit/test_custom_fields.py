"""Unit tests for the custom_fields module."""

from unittest.mock import Mock, patch

from neon_crm.resources.custom_fields import CustomFieldsResource
from neon_crm.types import CustomFieldCategory


class TestCustomFieldsResource:
    """Test the CustomFieldsResource class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_client = Mock()
        self.resource = CustomFieldsResource(self.mock_client)

    def test_initialization(self):
        """Test CustomFieldsResource initialization."""
        assert self.resource._client == self.mock_client
        assert self.resource._endpoint == "/customFields"

    def test_list_without_filters(self):
        """Test listing custom fields without filters."""
        # Mock the parent list method
        with patch.object(self.resource, "_BaseResource__init__") as mock_init:
            mock_init.return_value = None

        mock_list = Mock()
        mock_list.return_value = iter([{"id": 1, "name": "Field 1"}])

        with patch("neon_crm.resources.base.BaseResource.list", mock_list):
            list(self.resource.list(current_page=0, page_size=50))

        mock_list.assert_called_once_with(current_page=0, page_size=50, limit=None)

    def test_list_with_field_type_filter(self):
        """Test listing custom fields with field type filter."""
        mock_list = Mock()
        mock_list.return_value = iter([{"id": 1, "name": "Field 1", "type": "text"}])

        with patch("neon_crm.resources.base.BaseResource.list", mock_list):
            list(self.resource.list(field_type="text"))

        mock_list.assert_called_once_with(
            current_page=0, page_size=50, limit=None, fieldType="text"
        )

    def test_list_with_category_enum_filter(self):
        """Test listing custom fields with category enum filter."""
        mock_list = Mock()
        mock_list.return_value = iter([{"id": 1, "name": "Field 1"}])

        with patch("neon_crm.resources.base.BaseResource.list", mock_list):
            list(self.resource.list(category=CustomFieldCategory.ACCOUNT))

        mock_list.assert_called_once_with(
            current_page=0, page_size=50, limit=None, category="ACCOUNT"
        )

    def test_list_with_category_string_filter(self):
        """Test listing custom fields with category string filter."""
        mock_list = Mock()
        mock_list.return_value = iter([{"id": 1, "name": "Field 1"}])

        with patch("neon_crm.resources.base.BaseResource.list", mock_list):
            list(self.resource.list(category="DONATION"))

        mock_list.assert_called_once_with(
            current_page=0, page_size=50, limit=None, category="DONATION"
        )

    def test_list_with_multiple_filters(self):
        """Test listing custom fields with multiple filters."""
        mock_list = Mock()
        mock_list.return_value = iter([{"id": 1, "name": "Field 1"}])

        with patch("neon_crm.resources.base.BaseResource.list", mock_list):
            list(
                self.resource.list(
                    field_type="text",
                    category=CustomFieldCategory.ACCOUNT,
                    limit=10,
                    extra_param="value",
                )
            )

        mock_list.assert_called_once_with(
            current_page=0,
            page_size=50,
            limit=10,
            fieldType="text",
            category="ACCOUNT",
            extra_param="value",
        )

    def test_get_by_category_with_enum(self):
        """Test getting custom fields by category with enum."""
        mock_list = Mock()
        mock_list.return_value = iter([{"id": 1, "name": "Field 1"}])

        with patch.object(self.resource, "list", mock_list):
            list(self.resource.get_by_category(CustomFieldCategory.ACCOUNT))

        mock_list.assert_called_once_with(category=CustomFieldCategory.ACCOUNT)

    def test_get_by_category_with_string(self):
        """Test getting custom fields by category with string."""
        mock_list = Mock()
        mock_list.return_value = iter([{"id": 1, "name": "Field 1"}])

        with patch.object(self.resource, "list", mock_list):
            list(self.resource.get_by_category("DONATION"))

        mock_list.assert_called_once_with(category="DONATION")

    def test_find_by_name_and_category_with_cache_hit(self):
        """Test finding custom field by name with cache hit."""
        # Setup cache mock
        self.mock_client._cache = Mock()
        cache_mock = Mock()
        cache_mock.cache_get_or_set.return_value = {"id": 1, "name": "Test Field"}
        self.mock_client._cache.custom_fields = cache_mock
        self.mock_client._cache.create_cache_key.return_value = "test_key"

        result = self.resource.find_by_name_and_category(
            "Test Field", CustomFieldCategory.ACCOUNT
        )

        assert result == {"id": 1, "name": "Test Field"}
        self.mock_client._cache.create_cache_key.assert_called_once_with(
            "custom_field", "ACCOUNT", "Test Field"
        )
        cache_mock.cache_get_or_set.assert_called_once()

    def test_find_by_name_and_category_with_cache_miss(self):
        """Test finding custom field by name with cache miss."""
        # Setup cache to return None, then mock the fetch function
        self.mock_client._cache = Mock()
        cache_mock = Mock()

        # Mock the fields returned by get_by_category
        mock_fields = [
            {"id": 1, "name": "Other Field"},
            {"id": 2, "name": "Test Field"},
            {"id": 3, "name": "Another Field"},
        ]

        def cache_get_or_set(key, fetch_func):
            # Simulate cache miss by calling fetch_func
            return fetch_func()

        cache_mock.cache_get_or_set.side_effect = cache_get_or_set
        self.mock_client._cache.custom_fields = cache_mock
        self.mock_client._cache.create_cache_key.return_value = "test_key"

        with patch.object(self.resource, "get_by_category", return_value=mock_fields):
            result = self.resource.find_by_name_and_category(
                "Test Field", CustomFieldCategory.ACCOUNT
            )

        assert result == {"id": 2, "name": "Test Field"}

    def test_find_by_name_and_category_not_found_with_cache(self):
        """Test finding custom field by name when not found with cache."""
        self.mock_client._cache = Mock()
        cache_mock = Mock()

        mock_fields = [
            {"id": 1, "name": "Other Field"},
            {"id": 3, "name": "Another Field"},
        ]

        def cache_get_or_set(key, fetch_func):
            return fetch_func()

        cache_mock.cache_get_or_set.side_effect = cache_get_or_set
        self.mock_client._cache.custom_fields = cache_mock
        self.mock_client._cache.create_cache_key.return_value = "test_key"

        with patch.object(self.resource, "get_by_category", return_value=mock_fields):
            result = self.resource.find_by_name_and_category(
                "Nonexistent Field", CustomFieldCategory.ACCOUNT
            )

        assert result is None

    def test_find_by_name_and_category_without_cache(self):
        """Test finding custom field by name without cache."""
        self.mock_client._cache = None

        mock_fields = [
            {"id": 1, "name": "Other Field"},
            {"id": 2, "name": "Test Field"},
            {"id": 3, "name": "Another Field"},
        ]

        with patch.object(self.resource, "get_by_category", return_value=mock_fields):
            result = self.resource.find_by_name_and_category("Test Field", "ACCOUNT")

        assert result == {"id": 2, "name": "Test Field"}

    def test_find_by_name_and_category_not_found_without_cache(self):
        """Test finding custom field by name when not found without cache."""
        self.mock_client._cache = None

        mock_fields = [
            {"id": 1, "name": "Other Field"},
            {"id": 3, "name": "Another Field"},
        ]

        with patch.object(self.resource, "get_by_category", return_value=mock_fields):
            result = self.resource.find_by_name_and_category(
                "Nonexistent Field", "ACCOUNT"
            )

        assert result is None

    def test_find_by_name_and_category_with_string_category(self):
        """Test finding custom field with string category."""
        self.mock_client._cache = Mock()
        cache_mock = Mock()
        cache_mock.cache_get_or_set.return_value = {"id": 1, "name": "Test Field"}
        self.mock_client._cache.custom_fields = cache_mock
        self.mock_client._cache.create_cache_key.return_value = "test_key"

        self.resource.find_by_name_and_category("Test Field", "DONATION")

        self.mock_client._cache.create_cache_key.assert_called_once_with(
            "custom_field", "DONATION", "Test Field"
        )

    def test_get_field_options(self):
        """Test getting field options."""
        mock_field = {
            "id": 123,
            "name": "Test Field",
            "options": [
                {"id": 1, "label": "Option 1", "value": "opt1"},
                {"id": 2, "label": "Option 2", "value": "opt2"},
            ],
        }

        self.mock_client.get.return_value = mock_field

        result = self.resource.get_field_options(123)

        expected_options = [
            {"id": 1, "label": "Option 1", "value": "opt1"},
            {"id": 2, "label": "Option 2", "value": "opt2"},
        ]
        assert result == expected_options
        self.mock_client.get.assert_called_once_with("/customFields/123")

    def test_get_field_options_no_options(self):
        """Test getting field options when field has no options."""
        mock_field = {"id": 123, "name": "Test Field"}

        self.mock_client.get.return_value = mock_field

        result = self.resource.get_field_options(123)

        assert result == []

    def test_list_groups(self):
        """Test listing custom field groups."""
        mock_response = {
            "customFieldGroups": [
                {"id": 1, "name": "Group 1"},
                {"id": 2, "name": "Group 2"},
            ],
            "pagination": {"currentPage": 0, "totalPages": 1},
        }

        self.mock_client.get.return_value = mock_response

        result = list(self.resource.list_groups())

        assert len(result) == 2
        assert result[0]["name"] == "Group 1"
        self.mock_client.get.assert_called_once_with(
            "/customFields/groups", params={"currentPage": 0, "pageSize": 50}
        )

    def test_list_groups_with_category_filter(self):
        """Test listing custom field groups with category filter."""
        mock_response = {
            "customFieldGroups": [{"id": 1, "name": "Account Group"}],
            "pagination": {"currentPage": 0, "totalPages": 1},
        }

        self.mock_client.get.return_value = mock_response

        list(self.resource.list_groups(category=CustomFieldCategory.ACCOUNT))

        self.mock_client.get.assert_called_once_with(
            "/customFields/groups",
            params={"currentPage": 0, "pageSize": 50, "component": "ACCOUNT"},
        )

    def test_get_group(self):
        """Test getting a specific field group."""
        mock_response = {"id": 1, "name": "Test Group"}

        self.mock_client.get.return_value = mock_response

        result = self.resource.get_group(1)

        assert result == mock_response
        self.mock_client.get.assert_called_once_with("/customFields/groups/1")

    def test_get_groups_by_category(self):
        """Test getting groups by category."""
        mock_groups = [{"id": 1, "name": "Account Group"}]

        with patch.object(self.resource, "list_groups", return_value=mock_groups):
            result = list(
                self.resource.get_groups_by_category(CustomFieldCategory.ACCOUNT)
            )

        assert result == mock_groups

    def test_find_group_by_name(self):
        """Test finding a group by name."""
        mock_groups = [
            {"id": 1, "name": "Other Group"},
            {"id": 2, "name": "Test Group"},
        ]

        with patch.object(self.resource, "list_groups", return_value=mock_groups):
            result = self.resource.find_group_by_name("Test Group")

        assert result == {"id": 2, "name": "Test Group"}

    def test_find_group_by_name_and_category_with_cache(self):
        """Test finding field group by name with cache."""
        self.mock_client._cache = Mock()
        cache_mock = Mock()
        cache_mock.cache_get_or_set.return_value = {"id": 1, "name": "Test Group"}
        self.mock_client._cache.custom_field_groups = cache_mock
        self.mock_client._cache.create_cache_key.return_value = "group_key"

        result = self.resource.find_group_by_name_and_category(
            "Test Group", CustomFieldCategory.ACCOUNT
        )

        assert result == {"id": 1, "name": "Test Group"}
        self.mock_client._cache.create_cache_key.assert_called_once_with(
            "custom_field_group", "ACCOUNT", "Test Group"
        )

    def test_find_group_by_name_and_category_without_cache(self):
        """Test finding field group by name without cache."""
        self.mock_client._cache = None

        mock_groups = [
            {"id": 1, "name": "Other Group"},
            {"id": 2, "name": "Test Group"},
        ]

        with patch.object(self.resource, "list_field_groups", return_value=mock_groups):
            result = self.resource.find_group_by_name_and_category(
                "Test Group", "ACCOUNT"
            )

        assert result == {"id": 2, "name": "Test Group"}
