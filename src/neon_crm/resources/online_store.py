"""Online Store resource for the Neon CRM SDK."""

from typing import TYPE_CHECKING, Any, Dict, Iterator, Optional

from .base import BaseResource

if TYPE_CHECKING:
    from ..client import NeonClient


class OnlineStoreResource(BaseResource):
    """Resource for managing online store items and transactions."""

    def __init__(self, client: "NeonClient") -> None:
        """Initialize the online store resource."""
        super().__init__(client, "/store")

    def list(
        self,
        current_page: int = 0,
        page_size: int = 50,
        limit: Optional[int] = None,
        **kwargs: Any,
    ) -> Iterator[Dict[str, Any]]:
        """List online store products (default list method).

        Args:
            current_page: Page number to start from (0-indexed)
            page_size: Number of items per page
            limit: Maximum number of items to return
            **kwargs: Additional query parameters

        Yields:
            Individual product dictionaries
        """
        return self.list_products(
            current_page=current_page, page_size=page_size, limit=limit, **kwargs
        )

    def list_products(
        self,
        current_page: int = 0,
        page_size: int = 50,
        limit: Optional[int] = None,
        product_status: Optional[str] = None,
        category: Optional[str] = None,
        **kwargs: Any,
    ) -> Iterator[Dict[str, Any]]:
        """List online store products.

        Args:
            current_page: Page number to start from (0-indexed)
            page_size: Number of items per page
            limit: Maximum number of items to return
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

        # Override the endpoint for products
        original_endpoint = self._endpoint
        self._endpoint = "/store/products"
        try:
            return super().list(
                current_page=current_page, page_size=page_size, limit=limit, **params
            )
        finally:
            self._endpoint = original_endpoint

    def get_product(self, product_id: int) -> Dict[str, Any]:
        """Get a specific store product by ID.

        Args:
            product_id: The product ID

        Returns:
            The product data
        """
        # Override the endpoint for products
        original_endpoint = self._endpoint
        self._endpoint = "/store/products"
        try:
            return super().get(product_id)
        finally:
            self._endpoint = original_endpoint

    def list_catalogs(
        self,
        current_page: int = 0,
        page_size: int = 50,
        limit: Optional[int] = None,
        **kwargs: Any,
    ) -> Iterator[Dict[str, Any]]:
        """List store catalogs.

        Args:
            current_page: Page number to start from (0-indexed)
            page_size: Number of items per page
            limit: Maximum number of items to return
            **kwargs: Additional query parameters

        Yields:
            Individual catalog dictionaries
        """
        # Override the endpoint for catalogs
        original_endpoint = self._endpoint
        self._endpoint = "/store/catalogs"
        try:
            return super().list(
                current_page=current_page, page_size=page_size, limit=limit, **kwargs
            )
        finally:
            self._endpoint = original_endpoint

    def list_categories(
        self,
        current_page: int = 0,
        page_size: int = 50,
        limit: Optional[int] = None,
        **kwargs: Any,
    ) -> Iterator[Dict[str, Any]]:
        """List store categories.

        Args:
            current_page: Page number to start from (0-indexed)
            page_size: Number of items per page
            limit: Maximum number of items to return
            **kwargs: Additional query parameters

        Yields:
            Individual category dictionaries
        """
        # Override the endpoint for categories
        original_endpoint = self._endpoint
        self._endpoint = "/store/categories"
        try:
            return super().list(
                current_page=current_page, page_size=page_size, limit=limit, **kwargs
            )
        finally:
            self._endpoint = original_endpoint

    # Transaction endpoints
    def list_transactions(
        self,
        current_page: int = 0,
        page_size: int = 50,
        limit: Optional[int] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        status: Optional[str] = None,
        **kwargs: Any,
    ) -> Iterator[Dict[str, Any]]:
        """List store transactions.

        Args:
            current_page: Page number to start from (0-indexed)
            page_size: Number of items per page
            limit: Maximum number of items to return
            start_date: Filter by start date (YYYY-MM-DD format)
            end_date: Filter by end date (YYYY-MM-DD format)
            status: Filter by transaction status
            **kwargs: Additional query parameters

        Yields:
            Individual transaction dictionaries
        """
        params = {}
        if start_date is not None:
            params["startDate"] = start_date
        if end_date is not None:
            params["endDate"] = end_date
        if status is not None:
            params["status"] = status

        params.update(kwargs)

        # Override the endpoint for transactions
        original_endpoint = self._endpoint
        self._endpoint = "/store/transactions"
        try:
            return super().list(
                current_page=current_page, page_size=page_size, limit=limit, **params
            )
        finally:
            self._endpoint = original_endpoint

    def get_transaction(self, transaction_id: int) -> Dict[str, Any]:
        """Get a specific store transaction by ID.

        Args:
            transaction_id: The transaction ID

        Returns:
            The transaction data
        """
        # Override the endpoint for transactions
        original_endpoint = self._endpoint
        self._endpoint = "/store/transactions"
        try:
            return super().get(transaction_id)
        finally:
            self._endpoint = original_endpoint

    def list_orders(
        self,
        current_page: int = 0,
        page_size: int = 50,
        limit: Optional[int] = None,
        status: Optional[str] = None,
        customer_id: Optional[int] = None,
        **kwargs: Any,
    ) -> Iterator[Dict[str, Any]]:
        """List store orders.

        Args:
            current_page: Page number to start from (0-indexed)
            page_size: Number of items per page
            limit: Maximum number of items to return
            status: Filter by order status
            customer_id: Filter by customer ID
            **kwargs: Additional query parameters

        Yields:
            Individual order dictionaries
        """
        params = {}
        if status is not None:
            params["status"] = status
        if customer_id is not None:
            params["customerId"] = customer_id

        params.update(kwargs)

        # Override the endpoint for orders
        original_endpoint = self._endpoint
        self._endpoint = "/store/orders"
        try:
            return super().list(
                current_page=current_page, page_size=page_size, limit=limit, **params
            )
        finally:
            self._endpoint = original_endpoint

    def get_order(self, order_id: int) -> Dict[str, Any]:
        """Get a specific store order by ID.

        Args:
            order_id: The order ID

        Returns:
            The order data
        """
        # Override the endpoint for orders
        original_endpoint = self._endpoint
        self._endpoint = "/store/orders"
        try:
            return super().get(order_id)
        finally:
            self._endpoint = original_endpoint
