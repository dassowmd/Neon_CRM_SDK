"""Orders resource for the Neon CRM SDK."""

from typing import TYPE_CHECKING, Any, Dict, Iterator, Optional

from .base import SearchableResource, CalculationResource

if TYPE_CHECKING:
    from ..client import NeonClient


class OrdersResource(SearchableResource, CalculationResource):
    """Resource for managing orders."""

    def __init__(self, client: "NeonClient") -> None:
        """Initialize the orders resource."""
        super().__init__(client, "/orders")

    def list(
        self,
        current_page: int = 0,
        page_size: int = 50,
        limit: Optional[int] = None,
        order_status: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        **kwargs: Any,
    ) -> Iterator[Dict[str, Any]]:
        """List orders with optional filtering.

        Args:
            current_page: Page number to start from (0-indexed)
            page_size: Number of items per page
            order_status: Filter by order status
            start_date: Filter by start date (YYYY-MM-DD format)
            end_date: Filter by end date (YYYY-MM-DD format)
            **kwargs: Additional query parameters

        Yields:
            Individual order dictionaries
        """
        params = {}
        if order_status is not None:
            params["orderStatus"] = order_status
        if start_date is not None:
            params["startDate"] = start_date
        if end_date is not None:
            params["endDate"] = end_date

        params.update(kwargs)

        return super().list(
            current_page=current_page, page_size=page_size, limit=limit, **params
        )

    def calculate_order_total(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate the total cost of an order.

        Args:
            order_data: The order data for calculation

        Returns:
            The calculated order totals
        """
        return self.calculate(order_data)
