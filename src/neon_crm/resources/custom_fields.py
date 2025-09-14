"""Custom Fields resource for the Neon CRM SDK."""

from typing import TYPE_CHECKING, Any, Dict, Iterator, Optional

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
        component: Optional[str] = None,
        **kwargs: Any,
    ) -> Iterator[Dict[str, Any]]:
        """List custom fields with optional filtering.

        Args:
            current_page: Page number to start from (0-indexed)
            page_size: Number of items per page
            field_type: Filter by field type (text, number, date, etc.)
            component: Filter by component (accounts, donations, events, etc.)
            **kwargs: Additional query parameters

        Yields:
            Individual custom field dictionaries
        """
        params = {}
        if field_type is not None:
            params["fieldType"] = field_type
        if component is not None:
            params["component"] = component

        params.update(kwargs)

        return super().list(current_page=current_page, page_size=page_size, **params)

    def get_by_component(self, component: str) -> Iterator[Dict[str, Any]]:
        """Get custom fields for a specific component.

        Args:
            component: The component name (accounts, donations, events, etc.)

        Yields:
            Custom field definitions for the component
        """
        return self.list(component=component)
