"""Custom Fields resource for the Neon CRM SDK."""

from typing import TYPE_CHECKING

from .base import BaseResource

if TYPE_CHECKING:
    from ..client import NeonClient


class CustomFieldsResource(BaseResource):
    """Resource for managing custom fields."""

    def __init__(self, client: "NeonClient") -> None:
        """Initialize the custom fields resource."""
        super().__init__(client, "/customFields")
