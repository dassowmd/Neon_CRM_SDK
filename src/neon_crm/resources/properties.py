"""Properties resource for the Neon CRM SDK."""

from typing import TYPE_CHECKING, Any, Dict

from .base import PropertiesResource as BasePropertiesResource

if TYPE_CHECKING:
    from ..client import NeonClient


class PropertiesResource(BasePropertiesResource):
    """Resource for accessing system properties and configuration data.

    This resource provides access to read-only system configuration
    such as countries, states, genders, etc.
    """

    def __init__(self, client: "NeonClient") -> None:
        """Initialize the properties resource."""
        super().__init__(client, "/properties")
