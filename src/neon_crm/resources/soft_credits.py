"""Soft Credits resource for the Neon CRM SDK."""

from typing import TYPE_CHECKING, Any, Dict, Iterator, Optional

from .base import SearchableResource

if TYPE_CHECKING:
    from ..client import NeonClient


class SoftCreditsResource(SearchableResource):
    """Resource for managing soft credits."""

    def __init__(self, client: "NeonClient") -> None:
        """Initialize the soft credits resource."""
        super().__init__(client, "/softCredits")

    def list(
        self,
        current_page: int = 0,
        page_size: int = 50,
        donation_id: Optional[int] = None,
        account_id: Optional[int] = None,
        campaign_id: Optional[int] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        **kwargs: Any,
    ) -> Iterator[Dict[str, Any]]:
        """List soft credits with optional filtering.

        Args:
            current_page: Page number to start from (0-indexed)
            page_size: Number of items per page
            donation_id: Filter by donation ID
            account_id: Filter by account ID (the credited account)
            campaign_id: Filter by campaign ID
            start_date: Filter by start date (YYYY-MM-DD format)
            end_date: Filter by end date (YYYY-MM-DD format)
            **kwargs: Additional query parameters

        Yields:
            Individual soft credit dictionaries
        """
        params = {}
        if donation_id is not None:
            params["donationId"] = donation_id
        if account_id is not None:
            params["accountId"] = account_id
        if campaign_id is not None:
            params["campaignId"] = campaign_id
        if start_date is not None:
            params["startDate"] = start_date
        if end_date is not None:
            params["endDate"] = end_date

        params.update(kwargs)

        return super().list(current_page=current_page, page_size=page_size, **params)

    def get_by_account(self, account_id: int) -> Iterator[Dict[str, Any]]:
        """Get soft credits for a specific account.

        Args:
            account_id: The account ID

        Yields:
            Soft credits for the specified account
        """
        return self.list(account_id=account_id)

    def get_by_donation(self, donation_id: int) -> Iterator[Dict[str, Any]]:
        """Get soft credits for a specific donation.

        Args:
            donation_id: The donation ID

        Yields:
            Soft credits for the specified donation
        """
        return self.list(donation_id=donation_id)
