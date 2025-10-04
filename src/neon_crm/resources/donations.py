"""Donations resource for the Neon CRM SDK."""

from typing import TYPE_CHECKING

from .base import SearchableResource
from ..governance import ResourceType

if TYPE_CHECKING:
    from ..client import NeonClient


class DonationsResource(SearchableResource):
    """Resource for managing donations."""

    _resource_type = ResourceType.DONATIONS

    def __init__(self, client: "NeonClient") -> None:
        """Initialize the donations resource."""
        super().__init__(client, "/donations")
