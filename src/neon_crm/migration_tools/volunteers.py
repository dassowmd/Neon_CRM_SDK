"""Volunteers-specific migration tools for Neon CRM.

This module provides migration functionality specifically tailored for volunteers.
"""

from typing import Any, Dict, List, Optional, Iterator, Union, TYPE_CHECKING
from .base import BaseMigrationManager

if TYPE_CHECKING:
    from ..client import NeonClient


class VolunteersMigrationManager(BaseMigrationManager):
    """Migration manager specifically for volunteers resource."""

    def __init__(self, volunteers_resource, client: "NeonClient", **kwargs):
        """Initialize the volunteers migration manager.

        Args:
            volunteers_resource: The volunteers resource instance
            client: Neon CRM client instance
            **kwargs: Additional parameters for volunteer operations
        """
        super().__init__(volunteers_resource, client, "volunteers")
        self._additional_params = kwargs

    def get_sample_resources(
        self, resource_filter: Dict[str, Any], limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get a small sample of volunteers for conflict analysis.

        Args:
            resource_filter: Filter criteria for volunteers
            limit: Maximum number of volunteers to return

        Returns:
            List of volunteer dictionaries
        """
        resources = []
        count = 0

        for resource in self.get_resources_for_migration(
            {"resource_filter": resource_filter}
        ):
            resources.append(resource)
            count += 1
            if count >= limit:
                break

        return resources

    def get_resources_for_migration(
        self, config: Dict[str, Any]
    ) -> Iterator[Dict[str, Any]]:
        """Get volunteers that should be included in the migration.

        Args:
            config: Configuration dictionary with resource_filter

        Returns:
            Iterator of volunteer dictionaries
        """
        resource_filter = config.get("resource_filter")

        # Prepare list parameters
        list_params = {
            "limit": 1000,
            **self._additional_params,
        }

        if resource_filter:
            # Use search with the provided filter if supported
            try:
                search_request = {
                    "searchFields": [
                        {"field": key, "operator": "EQUAL", "value": value}
                        for key, value in resource_filter.items()
                    ],
                    "outputFields": ["*"],
                }
                yield from self._resource.search(search_request)
            except AttributeError:
                # Fallback to list if search is not supported
                yield from self._resource.list(**list_params)
        else:
            # Get all volunteers
            yield from self._resource.list(**list_params)

    def get_resource_id_field(self) -> str:
        """Get the field name used for volunteer IDs.

        Returns:
            Field name for volunteer IDs
        """
        return "Volunteer ID"
