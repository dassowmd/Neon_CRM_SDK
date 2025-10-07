"""Events-specific migration tools for Neon CRM.

This module provides migration functionality specifically tailored for events,
handling event-specific requirements like date filtering parameters.
"""

from typing import Any, Dict, List, Optional, Iterator, Union, TYPE_CHECKING
from .base import BaseMigrationManager

if TYPE_CHECKING:
    from ..client import NeonClient


class EventsMigrationManager(BaseMigrationManager):
    """Migration manager specifically for events resource."""

    def __init__(
        self,
        events_resource,
        client: "NeonClient",
        event_status: Optional[str] = None,
        category_id: Optional[int] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        **kwargs,
    ):
        """Initialize the events migration manager.

        Args:
            events_resource: The events resource instance
            client: Neon CRM client instance
            event_status: Filter by event status
            category_id: Filter by event category ID
            start_date: Filter by start date (YYYY-MM-DD format)
            end_date: Filter by end date (YYYY-MM-DD format)
            **kwargs: Additional parameters for event operations
        """
        super().__init__(events_resource, client, "events")
        self._event_status = event_status
        self._category_id = category_id
        self._start_date = start_date
        self._end_date = end_date
        self._additional_params = kwargs

    def get_sample_resources(
        self, resource_filter: Dict[str, Any], limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get a small sample of events for conflict analysis.

        Args:
            resource_filter: Filter criteria for events
            limit: Maximum number of events to return

        Returns:
            List of event dictionaries
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
        """Get events that should be included in the migration.

        Args:
            config: Configuration dictionary with resource_filter

        Returns:
            Iterator of event dictionaries
        """
        resource_filter = config.get("resource_filter")

        # Prepare list parameters with event-specific filters
        list_params = {
            "limit": 1000,
            **self._additional_params,
        }

        # Add event-specific parameters if provided
        if self._event_status is not None:
            list_params["event_status"] = self._event_status
        if self._category_id is not None:
            list_params["category_id"] = self._category_id
        if self._start_date is not None:
            list_params["start_date"] = self._start_date
        if self._end_date is not None:
            list_params["end_date"] = self._end_date

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
            # Get all events with specified filters
            yield from self._resource.list(**list_params)

    def get_resource_id_field(self) -> str:
        """Get the field name used for event IDs.

        Returns:
            Field name for event IDs
        """
        return "Event ID"
