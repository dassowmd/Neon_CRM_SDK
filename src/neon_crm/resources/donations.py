"""Donations resource for the Neon CRM SDK."""

from typing import TYPE_CHECKING, Any

from .base import SearchableResource
from ..governance import ResourceType

if TYPE_CHECKING:
    from ..client import NeonClient
    from ..migration_tools import DonationsMigrationManager


class DonationsResource(SearchableResource):
    """Resource for managing donations."""

    _resource_type = ResourceType.DONATIONS

    def __init__(self, client: "NeonClient") -> None:
        """Initialize the donations resource."""
        super().__init__(client, "/donations")

    def create_migration_manager(self, **kwargs: Any) -> "DonationsMigrationManager":
        """Create a migration manager for donation migrations.

        Args:
            **kwargs: Additional parameters for donation operations

        Returns:
            DonationsMigrationManager instance configured for this donations resource
        """
        from ..migration_tools import DonationsMigrationManager

        return DonationsMigrationManager(self, self._client, **kwargs)
