"""Custom Fields resource for the Neon CRM SDK."""

from typing import TYPE_CHECKING, Any, Dict, Iterator, Optional, Union

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
