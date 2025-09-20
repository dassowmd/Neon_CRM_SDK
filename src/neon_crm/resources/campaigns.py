"""Campaigns resource for the Neon CRM SDK."""

from typing import TYPE_CHECKING, Any, Dict, Iterator, Optional

from .base import BaseResource

if TYPE_CHECKING:
    from ..client import NeonClient


class CampaignsResource(BaseResource):
    """Resource for managing campaigns."""

    def __init__(self, client: "NeonClient") -> None:
        """Initialize the campaigns resource."""
        super().__init__(client, "/campaigns")

    def list(
        self,
        current_page: int = 0,
        page_size: int = 50,
        limit: Optional[int] = None,
        campaign_status: Optional[str] = None,
        campaign_type: Optional[str] = None,
        **kwargs: Any,
    ) -> Iterator[Dict[str, Any]]:
        """List campaigns with optional filtering.

        Args:
            current_page: Page number to start from (0-indexed)
            page_size: Number of items per page
            campaign_status: Filter by campaign status
            campaign_type: Filter by campaign type
            **kwargs: Additional query parameters

        Yields:
            Individual campaign dictionaries
        """
        params = {}
        if campaign_status is not None:
            params["campaignStatus"] = campaign_status
        if campaign_type is not None:
            params["campaignType"] = campaign_type

        params.update(kwargs)

        return super().list(
            current_page=current_page, page_size=page_size, limit=limit, **params
        )
