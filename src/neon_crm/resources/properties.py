"""Properties resource for the Neon CRM SDK."""

from typing import TYPE_CHECKING, Any, Dict

from ..governance import ResourceType
from .base import BaseResource, PropertiesResource as BasePropertiesResource

if TYPE_CHECKING:
    from ..client import NeonClient


class PropertiesResource(BasePropertiesResource):
    """Resource for managing Neon CRM properties and configuration data."""

    _resource_type = ResourceType.PROPERTIES

    def __init__(self, client: "NeonClient") -> None:
        """Initialize the properties resource."""
        super().__init__(client, "/properties")
