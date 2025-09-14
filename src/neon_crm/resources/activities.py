"""Activities resource for the Neon CRM SDK."""

from typing import TYPE_CHECKING, Any, Dict, Iterator, Optional

from .base import SearchableResource

if TYPE_CHECKING:
    from ..client import NeonClient


class ActivitiesResource(SearchableResource):
    """Resource for managing activities."""

    def __init__(self, client: "NeonClient") -> None:
        """Initialize the activities resource."""
        super().__init__(client, "/activities")

    def list(
        self,
        current_page: int = 0,
        page_size: int = 50,
        activity_type: Optional[str] = None,
        account_id: Optional[int] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        **kwargs: Any,
    ) -> Iterator[Dict[str, Any]]:
        """List activities with optional filtering.

        Args:
            current_page: Page number to start from (0-indexed)
            page_size: Number of items per page
            activity_type: Filter by activity type
            account_id: Filter by account ID
            start_date: Filter by start date (YYYY-MM-DD format)
            end_date: Filter by end date (YYYY-MM-DD format)
            **kwargs: Additional query parameters

        Yields:
            Individual activity dictionaries
        """
        params = {}
        if activity_type is not None:
            params["activityType"] = activity_type
        if account_id is not None:
            params["accountId"] = account_id
        if start_date is not None:
            params["startDate"] = start_date
        if end_date is not None:
            params["endDate"] = end_date

        params.update(kwargs)

        return super().list(current_page=current_page, page_size=page_size, **params)
