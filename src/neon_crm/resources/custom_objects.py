"""Custom Objects resource for the Neon CRM SDK."""

from typing import TYPE_CHECKING, Any, Dict, Iterator, Optional

from .base import SearchableResource
from ..governance import ResourceType

if TYPE_CHECKING:
    from ..client import NeonClient


class CustomObjectsResource(SearchableResource):
    """Resource for managing custom objects."""
    
    _resource_type = ResourceType.CUSTOM_OBJECTS

    def __init__(self, client: "NeonClient") -> None:
        """Initialize the custom objects resource."""
        super().__init__(client, "/customObjects")

    def list(
        self,
        current_page: int = 1,
        page_size: int = 50,
        object_type: Optional[str] = None,
        status: Optional[str] = None,
        **kwargs: Any,
    ) -> Iterator[Dict[str, Any]]:
        """List custom objects with optional filtering.

        Args:
            current_page: Page number to start from (1-indexed)
            page_size: Number of items per page
            object_type: Filter by object type
            status: Filter by status
            **kwargs: Additional query parameters

        Yields:
            Individual custom object dictionaries
        """
        params = {}
        if object_type is not None:
            params["objectType"] = object_type
        if status is not None:
            params["status"] = status

        params.update(kwargs)

        return super().list(current_page=current_page, page_size=page_size, **params)

    def get_by_type(self, object_type: str) -> Iterator[Dict[str, Any]]:
        """Get custom objects of a specific type.

        Args:
            object_type: The custom object type

        Yields:
            Custom objects of the specified type
        """
        return self.list(object_type=object_type)
