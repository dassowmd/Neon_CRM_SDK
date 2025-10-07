"""Events resource for the Neon CRM SDK."""

from typing import TYPE_CHECKING, Any, Dict, Iterator, List, Optional

from ..governance import ResourceType
from .base import ListableResource, SearchableResource

if TYPE_CHECKING:
    from ..client import NeonClient
    from ..migration_tools import EventsMigrationManager


class EventsResource(ListableResource, SearchableResource):
    """Resource for managing events (legacy events only)."""

    _resource_type = ResourceType.EVENTS

    def __init__(self, client: "NeonClient") -> None:
        """Initialize the events resource."""
        super().__init__(client, "/events")

    def list(
        self,
        current_page: int = 0,
        page_size: int = 50,
        limit: Optional[int] = None,
        event_status: Optional[str] = None,
        category_id: Optional[int] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        **kwargs: Any,
    ) -> Iterator[Dict[str, Any]]:
        """List events with optional filtering.

        Args:
            current_page: Page number to start from (0-indexed)
            page_size: Number of items per page
            event_status: Filter by event status
            category_id: Filter by event category ID
            start_date: Filter by start date (YYYY-MM-DD format)
            end_date: Filter by end date (YYYY-MM-DD format)
            **kwargs: Additional query parameters

        Yields:
            Individual event dictionaries
        """
        params = {}
        if event_status is not None:
            params["eventStatus"] = event_status
        if category_id is not None:
            params["categoryId"] = category_id
        if start_date is not None:
            params["startDate"] = start_date
        if end_date is not None:
            params["endDate"] = end_date

        params.update(kwargs)

        return super().list(
            current_page=current_page, page_size=page_size, limit=limit, **params
        )

    def get_categories(self) -> List[Dict[str, Any]]:
        """Get all event categories.

        Returns:
            List of event category dictionaries with id and name fields
        """
        response = self._client.get("/events/categories")
        return response if isinstance(response, list) else []

    def get_registrations(
        self,
        event_id: str,
        page: int = 0,
        page_size: int = 50,
        limit: Optional[int] = None,
        registrant_account_id: Optional[str] = None,
        sort_direction: Optional[str] = None,
        sort_field: Optional[str] = None,
        **kwargs: Any,
    ) -> Iterator[Dict[str, Any]]:
        """Get registrations for a specific event.

        Args:
            event_id: The event ID
            page: Page number to start from (0-indexed)
            page_size: Number of items per page
            limit: Maximum number of registrations to return
            registrant_account_id: Filter by registrant account ID
            sort_direction: Sort direction ("ASC" or "DESC")
            sort_field: Field to sort by
            **kwargs: Additional query parameters

        Yields:
            Individual registration dictionaries
        """
        params = {"page": page, "pageSize": page_size}

        if registrant_account_id is not None:
            params["registrantAccountId"] = registrant_account_id
        if sort_direction is not None:
            params["sortDirection"] = sort_direction
        if sort_field is not None:
            params["sortField"] = sort_field

        params.update(kwargs)

        url = f"/events/{event_id}/eventRegistrations"
        count = 0
        current_page = page

        while True:
            params["page"] = current_page
            response = self._client.get(url, params=params)

            # Handle different response structures
            if isinstance(response, list):
                registrations = response
            elif isinstance(response, dict):
                # Try common response keys
                registrations = (
                    response.get("eventRegistrations")
                    or response.get("registrations")
                    or response.get("data")
                    or []
                )
            else:
                registrations = []

            if not registrations:
                break

            for registration in registrations:
                if limit is not None and count >= limit:
                    return
                yield registration
                count += 1

            # Check if we should continue to next page
            if len(registrations) < page_size:
                break
            current_page += 1

    def create_migration_manager(
        self,
        event_status: Optional[str] = None,
        category_id: Optional[int] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        **kwargs: Any,
    ) -> "EventsMigrationManager":
        """Create a migration manager for event migrations.

        Args:
            event_status: Filter by event status
            category_id: Filter by event category ID
            start_date: Filter by start date (YYYY-MM-DD format)
            end_date: Filter by end date (YYYY-MM-DD format)
            **kwargs: Additional parameters for event operations

        Returns:
            EventsMigrationManager instance configured for this events resource
        """
        from ..migration_tools import EventsMigrationManager

        return EventsMigrationManager(
            self,
            self._client,
            event_status,
            category_id,
            start_date,
            end_date,
            **kwargs,
        )
