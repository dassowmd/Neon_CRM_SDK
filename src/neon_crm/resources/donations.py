"""Donations resource for the Neon CRM SDK."""

from typing import TYPE_CHECKING, Any, Dict, Iterator, Optional

from .base import SearchableResource
from ..governance import ResourceType

if TYPE_CHECKING:
    from ..client import NeonClient


class DonationsResource(SearchableResource):
    """Resource for managing donations."""
    
    _resource_type = ResourceType.DONATIONS

    def __init__(self, client: "NeonClient") -> None:
        """Initialize the donations resource."""
        super().__init__(client, "/donations")

    def list(
        self,
        current_page: int = 1,
        page_size: int = 50,
        campaign_id: Optional[int] = None,
        fund_id: Optional[int] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        **kwargs: Any,
    ) -> Iterator[Dict[str, Any]]:
        """List donations with optional filtering.

        Args:
            current_page: Page number to start from (1-indexed)
            page_size: Number of items per page
            campaign_id: Filter by campaign ID
            fund_id: Filter by fund ID
            start_date: Filter by start date (YYYY-MM-DD format)
            end_date: Filter by end date (YYYY-MM-DD format)
            **kwargs: Additional query parameters

        Yields:
            Individual donation dictionaries
        """
        params = {}
        if campaign_id is not None:
            params["campaignId"] = campaign_id
        if fund_id is not None:
            params["fundId"] = fund_id
        if start_date is not None:
            params["startDate"] = start_date
        if end_date is not None:
            params["endDate"] = end_date

        params.update(kwargs)

        return super().list(current_page=current_page, page_size=page_size, **params)
