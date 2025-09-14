"""Online Store resource for the Neon CRM SDK."""

from typing import TYPE_CHECKING, Any, Dict, Iterator, Optional

from .base import BaseResource

if TYPE_CHECKING:
    from ..client import NeonClient


class OnlineStoreResource(BaseResource):
    """Resource for managing online store items and transactions."""

    def __init__(self, client: "NeonClient") -> None:
        """Initialize the online store resource."""
        super().__init__(client, "/onlineStore")

    def list_products(
        self,
        current_page: int = 0,
        page_size: int = 50,
        product_status: Optional[str] = None,
        category: Optional[str] = None,
        **kwargs: Any,
    ) -> Iterator[Dict[str, Any]]:
        """List online store products.

        Args:
            current_page: Page number to start from (0-indexed)
            page_size: Number of items per page
            product_status: Filter by product status
            category: Filter by product category
            **kwargs: Additional query parameters

        Yields:
            Individual product dictionaries
        """
        params = {}
        if product_status is not None:
            params["productStatus"] = product_status
        if category is not None:
            params["category"] = category

        params.update(kwargs)

        url = self._build_url("products")
        response = self._client.get(url, params=params)

        # Handle different response structures
        if isinstance(response, list):
            for item in response:
                yield item
        elif "products" in response:
            for item in response["products"]:
                yield item

    def list_transactions(
        self,
        current_page: int = 0,
        page_size: int = 50,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        **kwargs: Any,
    ) -> Iterator[Dict[str, Any]]:
        """List online store transactions.

        Args:
            current_page: Page number to start from (0-indexed)
            page_size: Number of items per page
            start_date: Filter by start date (YYYY-MM-DD format)
            end_date: Filter by end date (YYYY-MM-DD format)
            **kwargs: Additional query parameters

        Yields:
            Individual transaction dictionaries
        """
        params = {}
        if start_date is not None:
            params["startDate"] = start_date
        if end_date is not None:
            params["endDate"] = end_date

        params.update(kwargs)

        url = self._build_url("transactions")
        response = self._client.get(url, params=params)

        # Handle different response structures
        if isinstance(response, list):
            for item in response:
                yield item
        elif "transactions" in response:
            for item in response["transactions"]:
                yield item
