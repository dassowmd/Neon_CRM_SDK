"""Activities resource for the Neon CRM SDK."""

from typing import TYPE_CHECKING

from .base import SearchableResource

if TYPE_CHECKING:
    from ..client import NeonClient


class ActivitiesResource(SearchableResource):
    """Resource for managing activities."""

    def __init__(self, client: "NeonClient") -> None:
        """Initialize the activities resource."""
        super().__init__(client, "/activities")
