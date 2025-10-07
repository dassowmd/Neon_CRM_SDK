"""Memberships resource for the Neon CRM SDK."""

from typing import TYPE_CHECKING, Any, Dict, Iterator, List, Optional

from ..governance import ResourceType
from .base import CalculationResource, ListableResource

if TYPE_CHECKING:
    from ..client import NeonClient
    from ..migration_tools import MembershipsMigrationManager


class MembershipsResource(ListableResource, CalculationResource):
    """Resource for managing memberships."""

    _resource_type = ResourceType.MEMBERSHIPS

    def __init__(self, client: "NeonClient") -> None:
        """Initialize the memberships resource."""
        super().__init__(client, "/memberships")

    def list(
        self,
        current_page: int = 0,
        page_size: int = 50,
        limit: Optional[int] = None,
        membership_status: Optional[str] = None,
        membership_type_id: Optional[int] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        **kwargs: Any,
    ) -> Iterator[Dict[str, Any]]:
        """List memberships with optional filtering.

        Args:
            current_page: Page number to start from (0-indexed)
            page_size: Number of items per page
            membership_status: Filter by membership status
            membership_type_id: Filter by membership type ID
            start_date: Filter by start date (YYYY-MM-DD format)
            end_date: Filter by end date (YYYY-MM-DD format)
            **kwargs: Additional query parameters

        Yields:
            Individual membership dictionaries
        """
        params = {}
        if membership_status is not None:
            params["membershipStatus"] = membership_status
        if membership_type_id is not None:
            params["membershipTypeId"] = membership_type_id
        if start_date is not None:
            params["startDate"] = start_date
        if end_date is not None:
            params["endDate"] = end_date

        params.update(kwargs)

        return super().list(
            current_page=current_page, page_size=page_size, limit=limit, **params
        )

    def create_migration_manager(
        self,
        membership_status: Optional[str] = None,
        membership_type_id: Optional[int] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        **kwargs: Any,
    ) -> "MembershipsMigrationManager":
        """Create a migration manager for membership migrations.

        Args:
            membership_status: Filter by membership status
            membership_type_id: Filter by membership type ID
            start_date: Filter by start date (YYYY-MM-DD format)
            end_date: Filter by end date (YYYY-MM-DD format)
            **kwargs: Additional parameters for membership operations

        Returns:
            MembershipsMigrationManager instance configured for this memberships resource
        """
        from ..migration_tools import MembershipsMigrationManager

        return MembershipsMigrationManager(
            self,
            self._client,
            membership_status,
            membership_type_id,
            start_date,
            end_date,
            **kwargs,
        )

    def calculate_dates(self, calculation_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate membership term start and end dates.

        Args:
            calculation_data: The membership data for date calculation

        Returns:
            The calculated dates
        """
        return self.calculate(calculation_data, "Dates")

    def calculate_fee(self, calculation_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate the cost of a membership.

        Args:
            calculation_data: The membership data for fee calculation

        Returns:
            The calculated fee
        """
        return self.calculate(calculation_data, "Fee")

    def get_levels(self) -> List[Dict[str, Any]]:
        """Get all membership levels.

        Returns:
            List of membership level dictionaries
        """
        response = self._client.get("/memberships/levels")
        return response.get("membershipLevels", []) if response else []

    def get_terms(self) -> List[Dict[str, Any]]:
        """Get all membership terms.

        Returns:
            List of membership term dictionaries
        """
        response = self._client.get("/memberships/terms")
        return response.get("membershipTerms", []) if response else []
