"""Activities resource for the Neon CRM SDK."""

from typing import TYPE_CHECKING

from .base import SearchableResource
from ..governance import ResourceType

if TYPE_CHECKING:
    from ..client import NeonClient


class ActivitiesResource(SearchableResource):
    """Resource for managing activities.

    Note: Activities only support search operations, not list operations.
    Use the search() method to retrieve activities with specific criteria.
    """

    _resource_type = ResourceType.ACTIVITIES

    def __init__(self, client: "NeonClient") -> None:
        """Initialize the activities resource."""
        super().__init__(client, "/activities")
