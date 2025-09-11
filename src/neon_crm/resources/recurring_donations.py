"""recurring donations resource for the Neon CRM SDK."""

from typing import TYPE_CHECKING

from .base import BaseResource

if TYPE_CHECKING:
    from ..client import NeonClient


class RecurringDonationsResource(BaseResource):
    """Resource for managing recurring_donations."""

    def __init__(self, client: "NeonClient") -> None:
        """Initialize the recurring_donations resource."""
        super().__init__(client, "/recurring_donations")
