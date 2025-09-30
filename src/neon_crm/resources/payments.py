"""Payments resource for the Neon CRM SDK."""

from typing import TYPE_CHECKING, Any, Dict, Iterator, Optional

from .base import BaseResource

if TYPE_CHECKING:
    from ..client import NeonClient


class PaymentsResource(BaseResource):
    """Resource for managing payments."""

    def __init__(self, client: "NeonClient") -> None:
        """Initialize the payments resource."""
        super().__init__(client, "/payments")

    def list(
        self,
        current_page: int = 0,
        page_size: int = 50,
        limit: Optional[int] = None,
        payment_status: Optional[str] = None,
        payment_method: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        **kwargs: Any,
    ) -> Iterator[Dict[str, Any]]:
        """List payments with optional filtering.

        Args:
            current_page: Page number to start from (0-indexed)
            page_size: Number of items per page
            payment_status: Filter by payment status
            payment_method: Filter by payment method
            start_date: Filter by start date (YYYY-MM-DD format)
            end_date: Filter by end date (YYYY-MM-DD format)
            **kwargs: Additional query parameters

        Yields:
            Individual payment dictionaries
        """
        params = {}
        if payment_status is not None:
            params["paymentStatus"] = payment_status
        if payment_method is not None:
            params["paymentMethod"] = payment_method
        if start_date is not None:
            params["startDate"] = start_date
        if end_date is not None:
            params["endDate"] = end_date

        params.update(kwargs)

        return super().list(
            current_page=current_page, page_size=page_size, limit=limit, **params
        )
