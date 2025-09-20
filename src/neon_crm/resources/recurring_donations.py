"""Recurring Donations resource for the Neon CRM SDK."""

from typing import TYPE_CHECKING, Any, Dict, Iterator, Optional

from .base import BaseResource

if TYPE_CHECKING:
    from ..client import NeonClient


class RecurringDonationsResource(BaseResource):
    """Resource for managing recurring donations."""

    def __init__(self, client: "NeonClient") -> None:
        """Initialize the recurring donations resource."""
        super().__init__(client, "/recurring")

    def list(
        self,
        current_page: int = 0,
        page_size: int = 50,
        limit: Optional[int] = None,
        donation_status: Optional[str] = None,
        frequency: Optional[str] = None,
        campaign_id: Optional[int] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        **kwargs: Any,
    ) -> Iterator[Dict[str, Any]]:
        """List recurring donations with optional filtering.

        Args:
            current_page: Page number to start from (0-indexed)
            page_size: Number of items per page
            donation_status: Filter by donation status
            frequency: Filter by frequency (monthly, quarterly, annually, etc.)
            campaign_id: Filter by campaign ID
            start_date: Filter by start date (YYYY-MM-DD format)
            end_date: Filter by end date (YYYY-MM-DD format)
            **kwargs: Additional query parameters

        Yields:
            Individual recurring donation dictionaries
        """
        params = {}
        if donation_status is not None:
            params["donationStatus"] = donation_status
        if frequency is not None:
            params["frequency"] = frequency
        if campaign_id is not None:
            params["campaignId"] = campaign_id
        if start_date is not None:
            params["startDate"] = start_date
        if end_date is not None:
            params["endDate"] = end_date

        params.update(kwargs)

        return super().list(
            current_page=current_page, page_size=page_size, limit=limit, **params
        )

    def get_active(self) -> Iterator[Dict[str, Any]]:
        """Get all active recurring donations.

        Yields:
            Active recurring donation records
        """
        return self.list(donation_status="active")

    def get_by_frequency(self, frequency: str) -> Iterator[Dict[str, Any]]:
        """Get recurring donations by frequency.

        Args:
            frequency: The donation frequency

        Yields:
            Recurring donations with the specified frequency
        """
        return self.list(frequency=frequency)

    def cancel(self, donation_id: int) -> Dict[str, Any]:
        """Cancel a recurring donation.

        Args:
            donation_id: The recurring donation ID

        Returns:
            The response from the cancel operation
        """
        url = self._build_url(f"{donation_id}/cancel")
        return self._client.post(url)
