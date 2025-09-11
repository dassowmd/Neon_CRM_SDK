"""Grants resource for the Neon CRM SDK."""

from typing import TYPE_CHECKING, Any, Dict, Iterator, Optional

from .base import SearchableResource
from ..governance import ResourceType

if TYPE_CHECKING:
    from ..client import NeonClient


class GrantsResource(SearchableResource):
    """Resource for managing grants."""
    
    _resource_type = ResourceType.GRANTS

    def __init__(self, client: "NeonClient") -> None:
        """Initialize the grants resource."""
        super().__init__(client, "/grants")

    def list(
        self,
        current_page: int = 1,
        page_size: int = 50,
        grant_status: Optional[str] = None,
        funder_name: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        **kwargs: Any,
    ) -> Iterator[Dict[str, Any]]:
        """List grants with optional filtering.

        Args:
            current_page: Page number to start from (1-indexed)
            page_size: Number of items per page
            grant_status: Filter by grant status
            funder_name: Filter by funder name
            start_date: Filter by start date (YYYY-MM-DD format)
            end_date: Filter by end date (YYYY-MM-DD format)
            **kwargs: Additional query parameters

        Yields:
            Individual grant dictionaries
        """
        params = {}
        if grant_status is not None:
            params["grantStatus"] = grant_status
        if funder_name is not None:
            params["funderName"] = funder_name
        if start_date is not None:
            params["startDate"] = start_date
        if end_date is not None:
            params["endDate"] = end_date

        params.update(kwargs)

        return super().list(current_page=current_page, page_size=page_size, **params)

    def get_by_funder(self, funder_name: str) -> Iterator[Dict[str, Any]]:
        """Get grants from a specific funder.

        Args:
            funder_name: The funder name

        Yields:
            Grants from the specified funder
        """
        return self.list(funder_name=funder_name)

    def get_active(self) -> Iterator[Dict[str, Any]]:
        """Get all active grants.

        Yields:
            Active grant records
        """
        return self.list(grant_status="active")
