"""Campaigns resource for the Neon CRM SDK."""

from typing import TYPE_CHECKING

from .base import SearchableResource

if TYPE_CHECKING:
    from ..client import NeonClient


class CampaignsResource(SearchableResource):
    """Resource for managing campaigns."""

    def __init__(self, client: "NeonClient") -> None:
        """Initialize the campaigns resource."""
        super().__init__(client, "/campaigns")
