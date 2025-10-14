"""Memberships-specific migration tools for Neon CRM.

This module provides migration functionality specifically tailored for memberships,
handling membership-specific requirements like status and type filtering parameters.
"""

from typing import Any, Dict, List, Optional, Iterator, Union, TYPE_CHECKING
from .base import BaseMigrationManager

if TYPE_CHECKING:
    from ..client import NeonClient


class MembershipsMigrationManager(BaseMigrationManager):
    """Migration manager specifically for memberships resource."""

    def __init__(
        self,
        memberships_resource,
        client: "NeonClient",
        membership_status: Optional[str] = None,
        membership_type_id: Optional[int] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        **kwargs,
    ):
        """Initialize the memberships migration manager.

        Args:
            memberships_resource: The memberships resource instance
            client: Neon CRM client instance
            membership_status: Filter by membership status
            membership_type_id: Filter by membership type ID
            start_date: Filter by start date (YYYY-MM-DD format)
            end_date: Filter by end date (YYYY-MM-DD format)
            **kwargs: Additional parameters for membership operations
        """
        super().__init__(memberships_resource, client, "memberships")
        self._membership_status = membership_status
        self._membership_type_id = membership_type_id
        self._start_date = start_date
        self._end_date = end_date
        self._additional_params = kwargs

    def get_sample_resources(
        self, resource_filter: Dict[str, Any], limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get a small sample of memberships for conflict analysis.

        Args:
            resource_filter: Filter criteria for memberships
            limit: Maximum number of memberships to return

        Returns:
            List of membership dictionaries
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
        """Get memberships that should be included in the migration.

        Args:
            config: Configuration dictionary with resource_filter

        Returns:
            Iterator of membership dictionaries
        """
        resource_filter = config.get("resource_filter")

        # Prepare list parameters with membership-specific filters
        list_params = {
            "limit": 1000,
            **self._additional_params,
        }

        # Add membership-specific parameters if provided
        if self._membership_status is not None:
            list_params["membership_status"] = self._membership_status
        if self._membership_type_id is not None:
            list_params["membership_type_id"] = self._membership_type_id
        if self._start_date is not None:
            list_params["start_date"] = self._start_date
        if self._end_date is not None:
            list_params["end_date"] = self._end_date

        if resource_filter:
            # Use search with the provided filter if the resource supports it
            # Note: Memberships may not support search, so we'll try list with filters
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
            # Get all memberships with specified filters
            yield from self._resource.list(**list_params)

    def get_resource_id_field(self) -> str:
        """Get the field name used for membership IDs.

        Returns:
            Field name for membership IDs
        """
        return "Membership ID"
