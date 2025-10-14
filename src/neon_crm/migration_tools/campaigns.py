"""Campaigns-specific migration tools for Neon CRM.

This module provides migration functionality specifically tailored for campaigns.
"""

from typing import Any, Dict, List, Optional, Iterator, Union, TYPE_CHECKING
from .base import BaseMigrationManager

if TYPE_CHECKING:
    from ..client import NeonClient


class CampaignsMigrationManager(BaseMigrationManager):
    """Migration manager specifically for campaigns resource."""

    def __init__(self, campaigns_resource, client: "NeonClient", **kwargs):
        """Initialize the campaigns migration manager.

        Args:
            campaigns_resource: The campaigns resource instance
            client: Neon CRM client instance
            **kwargs: Additional parameters for campaign operations
        """
        super().__init__(campaigns_resource, client, "campaigns")
        self._additional_params = kwargs

    def get_sample_resources(
        self, resource_filter: Dict[str, Any], limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get a small sample of campaigns for conflict analysis.

        Args:
            resource_filter: Filter criteria for campaigns
            limit: Maximum number of campaigns to return

        Returns:
            List of campaign dictionaries
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
        """Get campaigns that should be included in the migration.

        Args:
            config: Configuration dictionary with resource_filter

        Returns:
            Iterator of campaign dictionaries
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
            # Get all campaigns
            yield from self._resource.list(**list_params)

    def get_resource_id_field(self) -> str:
        """Get the field name used for campaign IDs.

        Returns:
            Field name for campaign IDs
        """
        return "Campaign ID"
