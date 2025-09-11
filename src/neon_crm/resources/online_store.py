"""online store resource for the Neon CRM SDK."""

from typing import TYPE_CHECKING

from .base import BaseResource

if TYPE_CHECKING:
    from ..client import NeonClient


class OnlineStoreResource(BaseResource):
    """Resource for managing online_store."""

    def __init__(self, client: "NeonClient") -> None:
        """Initialize the online_store resource."""
        super().__init__(client, "/online_store")
