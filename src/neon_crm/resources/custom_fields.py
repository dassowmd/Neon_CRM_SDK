"""Custom Fields resource for the Neon CRM SDK."""

from typing import TYPE_CHECKING, Any, Dict, Iterator, List, Optional, Union

from ..types import CustomFieldCategory
from .base import BaseResource

if TYPE_CHECKING:
    from ..client import NeonClient


class CustomFieldsResource(BaseResource):
    """Resource for managing custom fields."""

    def __init__(self, client: "NeonClient") -> None:
        """Initialize the custom fields resource."""
        super().__init__(client, "/customFields")

    def list(
        self,
        current_page: int = 0,
        page_size: int = 50,
        limit: Optional[int] = None,
        field_type: Optional[str] = None,
        category: Optional[Union[CustomFieldCategory, str]] = None,
        **kwargs: Any,
    ) -> Iterator[Dict[str, Any]]:
        """List custom fields with optional filtering.

        Args:
            current_page: Page number to start from (0-indexed)
            page_size: Number of items per page
            limit: Maximum number of items to return
            field_type: Filter by field type (text, number, date, etc.)
            category: Filter by category (Account, Donation, Event, etc.)
            **kwargs: Additional query parameters

        Yields:
            Individual custom field dictionaries
        """
        params = {}
        if field_type is not None:
            params["fieldType"] = field_type
        if category is not None:
            params["category"] = (
                category.value
                if isinstance(category, CustomFieldCategory)
                else category
            )

        params.update(kwargs)

        return super().list(
            current_page=current_page, page_size=page_size, limit=limit, **params
        )

    def get_by_category(
        self, category: Union[CustomFieldCategory, str]
    ) -> Iterator[Dict[str, Any]]:
        """Get custom fields for a specific category.

        Args:
            category: The category (Account, Donation, Event, etc.)

        Yields:
            Custom field definitions for the category
        """
        return self.list(category=category)

    def find_by_name_and_category(
        self, field_name: str, category: Union[CustomFieldCategory, str]
    ) -> Optional[Dict[str, Any]]:
        """Find a custom field by name within a specific category.

        Args:
            field_name: The name of the custom field to find
            category: The category to search within

        Returns:
            The custom field data if found, None otherwise
        """
        for field in self.get_by_category(category):
            if field.get("name") == field_name:
                return field
        return None

    def get_field_options(self, field_id: int) -> List[Dict[str, Any]]:
        """Get options for a dropdown/select custom field.

        Args:
            field_id: The custom field ID

        Returns:
            List of field options if applicable
        """
        field = self.get(field_id)
        return field.get("options", [])

    def list_groups(
        self,
        current_page: int = 0,
        page_size: int = 50,
        limit: Optional[int] = None,
        category: Optional[Union[CustomFieldCategory, str]] = None,
        **kwargs: Any,
    ) -> Iterator[Dict[str, Any]]:
        """List custom field groups.

        Args:
            current_page: Page number to start from (0-indexed)
            page_size: Number of items per page
            limit: Maximum number of items to return
            category: Filter by category (Account, Donation, Event, etc.) - maps to 'component' API parameter
            **kwargs: Additional query parameters

        Yields:
            Individual custom field group dictionaries
        """
        params = {
            "currentPage": current_page,
            "pageSize": page_size,
        }

        # Map category to component parameter (API design inconsistency)
        if category is not None:
            params["component"] = (
                category.value
                if isinstance(category, CustomFieldCategory)
                else category
            )

        params.update(kwargs)

        results_returned = 0
        while True:
            response = self._client.get("/customFields/groups", params=params)

            # Handle different response structures
            if "groups" in response:
                items = response["groups"]
                pagination = response.get("pagination", {})
            elif isinstance(response, list):
                # Direct list response
                items = response
                pagination = {}
            else:
                # Try the standard endpoint name pattern
                items = response.get("customFields", [])
                pagination = response.get("pagination", {})

            # Yield each item
            for item in items:
                if limit is None or results_returned < limit:
                    yield item
                    results_returned += 1
                else:
                    break

            # Check if there are more pages
            if not pagination:
                break

            current_page_num = pagination.get("currentPage", 0)
            total_pages = pagination.get("totalPages", 1)

            if current_page_num >= total_pages - 1:
                break

            # Check limit for pagination continuation
            if limit is not None and results_returned >= limit:
                break

            # Update params for next page
            params["currentPage"] = current_page_num + 1

    def get_group(self, group_id: int) -> Dict[str, Any]:
        """Get a specific custom field group by ID.

        Args:
            group_id: The custom field group ID

        Returns:
            The custom field group data
        """
        return self._client.get(f"/customFields/groups/{group_id}")

    def get_groups_by_category(
        self, category: Union[CustomFieldCategory, str]
    ) -> Iterator[Dict[str, Any]]:
        """Get custom field groups for a specific category.

        Args:
            category: The category (Account, Donation, Event, etc.)

        Yields:
            Custom field group definitions for the category
        """
        return self.list_groups(category=category)

    def find_group_by_name(self, group_name: str) -> Optional[Dict[str, Any]]:
        """Find a custom field group by name.

        Args:
            group_name: The name of the custom field group to find

        Returns:
            The custom field group data if found, None otherwise
        """
        for group in self.list_groups():
            if group.get("name") == group_name:
                return group
        return None

    def find_group_by_name_and_category(
        self, group_name: str, category: Union[CustomFieldCategory, str]
    ) -> Optional[Dict[str, Any]]:
        """Find a custom field group by name within a specific category.

        Args:
            group_name: The name of the custom field group to find
            category: The category to search within

        Returns:
            The custom field group data if found, None otherwise
        """
        for group in self.get_groups_by_category(category):
            if group.get("name") == group_name:
                return group
        return None

    def list_all_categories(
        self,
        current_page: int = 0,
        page_size: int = 50,
        limit: Optional[int] = None,
        **kwargs: Any,
    ) -> Iterator[Dict[str, Any]]:
        """Iterate through custom fields from all categories.

        Args:
            current_page: Page number to start from (0-indexed)
            page_size: Number of items per page
            limit: Maximum number of items to return across all categories
            **kwargs: Additional query parameters

        Yields:
            Individual custom field dictionaries from all categories
        """
        results_returned = 0

        for category in CustomFieldCategory:
            if limit is not None and results_returned >= limit:
                break

            try:
                remaining_limit = (
                    limit - results_returned if limit is not None else None
                )
                for field in self.list(
                    current_page=current_page,
                    page_size=page_size,
                    limit=remaining_limit,
                    category=category,
                    **kwargs,
                ):
                    yield field
                    results_returned += 1
                    if limit is not None and results_returned >= limit:
                        break
            except Exception:
                # Skip categories that might not exist or have issues
                continue

    def list_all_groups_categories(
        self,
        current_page: int = 0,
        page_size: int = 50,
        limit: Optional[int] = None,
        **kwargs: Any,
    ) -> Iterator[Dict[str, Any]]:
        """Iterate through custom field groups from all categories.

        Args:
            current_page: Page number to start from (0-indexed)
            page_size: Number of items per page
            limit: Maximum number of items to return across all categories
            **kwargs: Additional query parameters

        Yields:
            Individual custom field group dictionaries from all categories
        """
        results_returned = 0

        for category in CustomFieldCategory:
            if limit is not None and results_returned >= limit:
                break

            try:
                remaining_limit = (
                    limit - results_returned if limit is not None else None
                )
                for group in self.list_groups(
                    current_page=current_page,
                    page_size=page_size,
                    limit=remaining_limit,
                    category=category,
                    **kwargs,
                ):
                    yield group
                    results_returned += 1
                    if limit is not None and results_returned >= limit:
                        break
            except Exception:
                # Skip categories that might not exist or have issues
                continue
