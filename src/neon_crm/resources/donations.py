"""Donations resource for the Neon CRM SDK."""

from typing import TYPE_CHECKING

from .base import SearchableResource

if TYPE_CHECKING:
    from ..client import NeonClient


class DonationsResource(SearchableResource):
    """Resource for managing donations.

    Note: Donations only support search operations, not list operations.
    Use the search() method to retrieve donations with specific criteria.
    """

    def __init__(self, client: "NeonClient") -> None:
        """Initialize the donations resource."""
        super().__init__(client, "/donations")
