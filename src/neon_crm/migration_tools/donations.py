"""Donations-specific migration tools for Neon CRM.

This module provides migration functionality specifically tailored for donations.
Donations are typically search-only resources, so this manager focuses on search-based operations.
"""

from typing import Any, Dict, List, Optional, Iterator, Union, TYPE_CHECKING
from .base import BaseMigrationManager

if TYPE_CHECKING:
    from ..client import NeonClient


class DonationsMigrationManager(BaseMigrationManager):
    """Migration manager specifically for donations resource."""

    def __init__(self, donations_resource, client: "NeonClient", **kwargs):
        """Initialize the donations migration manager.

        Args:
            donations_resource: The donations resource instance
            client: Neon CRM client instance
            **kwargs: Additional parameters for donation operations
        """
        super().__init__(donations_resource, client, "donations")
        self._additional_params = kwargs

    def get_sample_resources(
        self, resource_filter: Dict[str, Any], limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get a small sample of donations for conflict analysis.

        Args:
            resource_filter: Filter criteria for donations
            limit: Maximum number of donations to return

        Returns:
            List of donation dictionaries
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
        """Get donations that should be included in the migration.

        Args:
            config: Configuration dictionary with resource_filter

        Returns:
            Iterator of donation dictionaries
        """
        resource_filter = config.get("resource_filter")

        if resource_filter:
            # Use search with the provided filter
            search_request = {
                "searchFields": [
                    {"field": key, "operator": "EQUAL", "value": value}
                    for key, value in resource_filter.items()
                ],
                "outputFields": ["*"],
            }
            yield from self._resource.search(search_request)
        else:
            # Get a limited set of donations using basic search
            # Since donations are search-only, we use a broad search
            search_request = {
                "searchFields": [
                    {"field": "Donation ID", "operator": "GREATER_THAN", "value": "0"}
                ],
                "outputFields": ["*"],
                "pagination": {"currentPage": 0, "pageSize": 50},
            }
            yield from self._resource.search(search_request)

    def get_resource_id_field(self) -> str:
        """Get the field name used for donation IDs.

        Returns:
            Field name for donation IDs
        """
        return "Donation ID"
