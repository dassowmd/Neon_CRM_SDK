"""Webhooks resource for the Neon CRM SDK."""

from typing import TYPE_CHECKING

from .base import BaseResource

if TYPE_CHECKING:
    from ..client import NeonClient


class WebhooksResource(BaseResource):
    """Resource for managing webhooks."""

    def __init__(self, client: "NeonClient") -> None:
        """Initialize the webhooks resource."""
        super().__init__(client, "/webhooks")
