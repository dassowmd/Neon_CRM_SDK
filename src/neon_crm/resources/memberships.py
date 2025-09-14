"""Memberships resource for the Neon CRM SDK."""

from typing import TYPE_CHECKING, Any, Dict, Iterator, Optional

from .base import SearchableResource

if TYPE_CHECKING:
    from ..client import NeonClient


class MembershipsResource(SearchableResource):
    """Resource for managing memberships."""

    def __init__(self, client: "NeonClient") -> None:
        """Initialize the memberships resource."""
        super().__init__(client, "/memberships")

    def list(
        self,
        current_page: int = 0,
        page_size: int = 50,
        limit: Optional[int] = None,
        membership_status: Optional[str] = None,
        membership_type_id: Optional[int] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        **kwargs: Any,
    ) -> Iterator[Dict[str, Any]]:
        """List memberships with optional filtering.

        Args:
            current_page: Page number to start from (0-indexed)
            page_size: Number of items per page
            membership_status: Filter by membership status
            membership_type_id: Filter by membership type ID
            start_date: Filter by start date (YYYY-MM-DD format)
            end_date: Filter by end date (YYYY-MM-DD format)
            **kwargs: Additional query parameters

        Yields:
            Individual membership dictionaries
        """
        params = {}
        if membership_status is not None:
            params["membershipStatus"] = membership_status
        if membership_type_id is not None:
            params["membershipTypeId"] = membership_type_id
        if start_date is not None:
            params["startDate"] = start_date
        if end_date is not None:
            params["endDate"] = end_date

        params.update(kwargs)

        return super().list(
            current_page=current_page, page_size=page_size, limit=limit, **params
        )
