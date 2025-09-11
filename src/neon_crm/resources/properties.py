"""Properties resource for the Neon CRM SDK."""

from typing import TYPE_CHECKING, Any, Dict, Iterator, Optional

from .base import BaseResource
from ..governance import ResourceType

if TYPE_CHECKING:
    from ..client import NeonClient


class PropertiesResource(BaseResource):
    """Resource for managing system properties and configuration."""
    
    _resource_type = ResourceType.PROPERTIES

    def __init__(self, client: "NeonClient") -> None:
        """Initialize the properties resource."""
        super().__init__(client, "/properties")

    def list(
        self,
        current_page: int = 1,
        page_size: int = 50,
        category: Optional[str] = None,
        property_type: Optional[str] = None,
        **kwargs: Any,
    ) -> Iterator[Dict[str, Any]]:
        """List system properties with optional filtering.

        Args:
            current_page: Page number to start from (1-indexed)
            page_size: Number of items per page
            category: Filter by property category
            property_type: Filter by property type
            **kwargs: Additional query parameters

        Yields:
            Individual property dictionaries
        """
        params = {}
        if category is not None:
            params["category"] = category
        if property_type is not None:
            params["propertyType"] = property_type

        params.update(kwargs)

        return super().list(current_page=current_page, page_size=page_size, **params)

    def get_by_category(self, category: str) -> Iterator[Dict[str, Any]]:
        """Get properties by category.

        Args:
            category: The property category

        Yields:
            Properties in the specified category
        """
        return self.list(category=category)

    def get_system_info(self) -> Dict[str, Any]:
        """Get system information and configuration.

        Returns:
            System information dictionary
        """
        url = self._build_url("system")
        return self._client.get(url)

    def get_organization_info(self) -> Dict[str, Any]:
        """Get organization information.

        Returns:
            Organization information dictionary
        """
        url = self._build_url("organization")
        return self._client.get(url)
