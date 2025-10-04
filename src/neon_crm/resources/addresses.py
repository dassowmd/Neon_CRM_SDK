"""Address resource for the Neon CRM SDK."""

from typing import TYPE_CHECKING

from ..governance import ResourceType
from .base import BaseResource

if TYPE_CHECKING:
    from ..client import NeonClient


class AddressesResource(BaseResource):
    """Resource for managing addresses.

    Note: Addresses only support CRUD operations (GET by ID, POST, PUT, PATCH, DELETE).
    There is no list endpoint for addresses in the Neon CRM API.
    """

    _resource_type = ResourceType.ADDRESSES

    def __init__(self, client: "NeonClient") -> None:
        """Initialize the addresses resource."""
        super().__init__(client, "/addresses")
