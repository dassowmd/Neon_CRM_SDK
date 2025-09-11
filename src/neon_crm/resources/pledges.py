"""pledges resource for the Neon CRM SDK."""

from typing import TYPE_CHECKING

from .base import BaseResource

if TYPE_CHECKING:
    from ..client import NeonClient


class PledgesResource(BaseResource):
    """Resource for managing pledges."""

    def __init__(self, client: "NeonClient") -> None:
        """Initialize the pledges resource."""
        super().__init__(client, "/pledges")
