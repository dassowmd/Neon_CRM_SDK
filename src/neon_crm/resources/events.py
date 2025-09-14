"""Events resource for the Neon CRM SDK."""

from typing import TYPE_CHECKING, Any, Dict, Iterator, Optional

from .base import SearchableResource

if TYPE_CHECKING:
    from ..client import NeonClient


class EventsResource(SearchableResource):
    """Resource for managing events (legacy events only)."""

    def __init__(self, client: "NeonClient") -> None:
        """Initialize the events resource."""
        super().__init__(client, "/events")

    def list(
        self,
        current_page: int = 0,
        page_size: int = 50,
        limit: Optional[int] = None,
        event_status: Optional[str] = None,
        category_id: Optional[int] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        **kwargs: Any,
    ) -> Iterator[Dict[str, Any]]:
        """List events with optional filtering.

        Args:
            current_page: Page number to start from (0-indexed)
            page_size: Number of items per page
            event_status: Filter by event status
            category_id: Filter by event category ID
            start_date: Filter by start date (YYYY-MM-DD format)
            end_date: Filter by end date (YYYY-MM-DD format)
            **kwargs: Additional query parameters

        Yields:
            Individual event dictionaries
        """
        params = {}
        if event_status is not None:
            params["eventStatus"] = event_status
        if category_id is not None:
            params["categoryId"] = category_id
        if start_date is not None:
            params["startDate"] = start_date
        if end_date is not None:
            params["endDate"] = end_date

        params.update(kwargs)

        return super().list(
            current_page=current_page, page_size=page_size, limit=limit, **params
        )
