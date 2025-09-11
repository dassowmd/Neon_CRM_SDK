"""orders resource for the Neon CRM SDK."""

from typing import TYPE_CHECKING

from .base import BaseResource

if TYPE_CHECKING:
    from ..client import NeonClient


class OrdersResource(BaseResource):
    """Resource for managing orders."""

    def __init__(self, client: "NeonClient") -> None:
        """Initialize the orders resource."""
        super().__init__(client, "/orders")
