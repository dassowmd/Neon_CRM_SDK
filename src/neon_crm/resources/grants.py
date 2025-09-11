"""Grants resource for the Neon CRM SDK."""

from typing import TYPE_CHECKING

from .base import SearchableResource

if TYPE_CHECKING:
    from ..client import NeonClient


class GrantsResource(SearchableResource):
    """Resource for managing grants."""

    def __init__(self, client: "NeonClient") -> None:
        """Initialize the grants resource."""
        super().__init__(client, "/grants")
