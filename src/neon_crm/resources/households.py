"""Households resource for the Neon CRM SDK."""

from typing import TYPE_CHECKING, Any, Dict, Iterator, Optional

from .base import BaseResource

if TYPE_CHECKING:
    from ..client import NeonClient


class HouseholdsResource(BaseResource):
    """Resource for managing households."""

    def __init__(self, client: "NeonClient") -> None:
        """Initialize the households resource."""
        super().__init__(client, "/households")

    def list(
        self,
        current_page: int = 0,
        page_size: int = 50,
        limit: Optional[int] = None,
        household_name: Optional[str] = None,
        **kwargs: Any,
    ) -> Iterator[Dict[str, Any]]:
        """List households with optional filtering.

        Args:
            current_page: Page number to start from (0-indexed)
            page_size: Number of items per page
            household_name: Filter by household name
            **kwargs: Additional query parameters

        Yields:
            Individual household dictionaries
        """
        params = {}
        if household_name is not None:
            params["householdName"] = household_name

        params.update(kwargs)

        return super().list(current_page=current_page, page_size=page_size, **params)

    def add_member(self, household_id: int, account_id: int) -> Dict[str, Any]:
        """Add a member to a household.

        Args:
            household_id: The household ID
            account_id: The account ID to add

        Returns:
            The response from the add member operation
        """
        data = {"accountId": account_id}
        return self._client.post(
            self._build_url(f"{household_id}/members"), json_data=data
        )

    def remove_member(self, household_id: int, account_id: int) -> Dict[str, Any]:
        """Remove a member from a household.

        Args:
            household_id: The household ID
            account_id: The account ID to remove

        Returns:
            The response from the remove member operation
        """
        return self._client.delete(
            self._build_url(f"{household_id}/members/{account_id}")
        )
