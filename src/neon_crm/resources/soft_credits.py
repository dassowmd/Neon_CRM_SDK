"""soft credits resource for the Neon CRM SDK."""

from typing import TYPE_CHECKING

from .base import BaseResource

if TYPE_CHECKING:
    from ..client import NeonClient


class SoftCreditsResource(BaseResource):
    """Resource for managing soft_credits."""

    def __init__(self, client: "NeonClient") -> None:
        """Initialize the soft_credits resource."""
        super().__init__(client, "/soft_credits")
