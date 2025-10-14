"""Activities resource for the Neon CRM SDK."""

from typing import TYPE_CHECKING, Any

from .base import SearchableResource
from ..governance import ResourceType

if TYPE_CHECKING:
    from ..client import NeonClient
    from ..migration_tools import ActivitiesMigrationManager


class ActivitiesResource(SearchableResource):
    """Resource for managing activities.

    Note: Activities only support search operations, not list operations.
    Use the search() method to retrieve activities with specific criteria.
    """

    _resource_type = ResourceType.ACTIVITIES

    def __init__(self, client: "NeonClient") -> None:
        """Initialize the activities resource."""
        super().__init__(client, "/activities")

    def create_migration_manager(self, **kwargs: Any) -> "ActivitiesMigrationManager":
        """Create a migration manager for activity migrations.

        Args:
            **kwargs: Additional parameters for activity operations

        Returns:
            ActivitiesMigrationManager instance configured for this activities resource
        """
        from ..migration_tools import ActivitiesMigrationManager

        return ActivitiesMigrationManager(self, self._client, **kwargs)
