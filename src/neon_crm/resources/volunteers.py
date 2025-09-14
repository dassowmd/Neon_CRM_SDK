"""Volunteers resource for the Neon CRM SDK."""

from typing import TYPE_CHECKING, Any, Dict, Iterator, Optional

from .base import SearchableResource

if TYPE_CHECKING:
    from ..client import NeonClient


class VolunteersResource(SearchableResource):
    """Resource for managing volunteers."""

    def __init__(self, client: "NeonClient") -> None:
        """Initialize the volunteers resource."""
        super().__init__(client, "/volunteers")

    def list(
        self,
        current_page: int = 0,
        page_size: int = 50,
        limit: Optional[int] = None,
        volunteer_status: Optional[str] = None,
        skill_id: Optional[int] = None,
        availability: Optional[str] = None,
        **kwargs: Any,
    ) -> Iterator[Dict[str, Any]]:
        """List volunteers with optional filtering.

        Args:
            current_page: Page number to start from (0-indexed)
            page_size: Number of items per page
            volunteer_status: Filter by volunteer status
            skill_id: Filter by skill ID
            availability: Filter by availability
            **kwargs: Additional query parameters

        Yields:
            Individual volunteer dictionaries
        """
        params = {}
        if volunteer_status is not None:
            params["volunteerStatus"] = volunteer_status
        if skill_id is not None:
            params["skillId"] = skill_id
        if availability is not None:
            params["availability"] = availability

        params.update(kwargs)

        return super().list(
            current_page=current_page, page_size=page_size, limit=limit, **params
        )
