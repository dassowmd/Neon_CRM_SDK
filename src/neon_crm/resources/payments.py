"""payments resource for the Neon CRM SDK."""

from typing import TYPE_CHECKING

from .base import BaseResource

if TYPE_CHECKING:
    from ..client import NeonClient


class PaymentsResource(BaseResource):
    """Resource for managing payments."""

    def __init__(self, client: "NeonClient") -> None:
        """Initialize the payments resource."""
        super().__init__(client, "/payments")
