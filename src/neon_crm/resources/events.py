"""Events resource for the Neon CRM SDK."""

from typing import TYPE_CHECKING

from .base import SearchableResource

if TYPE_CHECKING:
    from ..client import NeonClient


class EventsResource(SearchableResource):
    """Resource for managing events (legacy events only)."""

    def __init__(self, client: "NeonClient") -> None:
        """Initialize the events resource."""
        super().__init__(client, "/events")
