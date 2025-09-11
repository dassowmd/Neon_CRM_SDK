"""properties resource for the Neon CRM SDK."""

from typing import TYPE_CHECKING

from .base import BaseResource

if TYPE_CHECKING:
    from ..client import NeonClient


class PropertiesResource(BaseResource):
    """Resource for managing properties."""

    def __init__(self, client: "NeonClient") -> None:
        """Initialize the properties resource."""
        super().__init__(client, "/properties")
