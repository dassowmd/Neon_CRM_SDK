"""Memberships resource for the Neon CRM SDK."""

from typing import TYPE_CHECKING

from .base import SearchableResource

if TYPE_CHECKING:
    from ..client import NeonClient


class MembershipsResource(SearchableResource):
    """Resource for managing memberships."""

    def __init__(self, client: "NeonClient") -> None:
        """Initialize the memberships resource."""
        super().__init__(client, "/memberships")
