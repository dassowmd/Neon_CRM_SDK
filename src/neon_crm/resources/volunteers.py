"""Volunteers resource for the Neon CRM SDK."""

from typing import TYPE_CHECKING

from .base import SearchableResource

if TYPE_CHECKING:
    from ..client import NeonClient


class VolunteersResource(SearchableResource):
    """Resource for managing volunteers."""

    def __init__(self, client: "NeonClient") -> None:
        """Initialize the volunteers resource."""
        super().__init__(client, "/volunteers")
