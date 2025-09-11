"""Households resource for the Neon CRM SDK."""

from typing import TYPE_CHECKING

from .base import BaseResource

if TYPE_CHECKING:
    from ..client import NeonClient


class HouseholdsResource(BaseResource):
    """Resource for managing households."""

    def __init__(self, client: "NeonClient") -> None:
        """Initialize the households resource."""
        super().__init__(client, "/households")
