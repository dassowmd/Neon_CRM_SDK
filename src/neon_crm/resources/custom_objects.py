"""Custom Objects resource for the Neon CRM SDK."""

from typing import TYPE_CHECKING

from .base import SearchableResource

if TYPE_CHECKING:
    from ..client import NeonClient


class CustomObjectsResource(SearchableResource):
    """Resource for managing custom objects."""

    def __init__(self, client: "NeonClient") -> None:
        """Initialize the custom objects resource."""
        super().__init__(client, "/customObjects")
