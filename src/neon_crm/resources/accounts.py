"""Accounts resource for the Neon CRM SDK."""

from typing import TYPE_CHECKING, Any, Dict, Iterator, Optional

from .base import RelationshipResource, SearchableResource

if TYPE_CHECKING:
    from ..client import NeonClient


class AccountsResource(SearchableResource):
    """Resource for managing accounts (contacts and organizations)."""

    def __init__(self, client: "NeonClient") -> None:
        """Initialize the accounts resource."""
        super().__init__(client, "/accounts")

    def list(
        self,
        current_page: int = 1,
        page_size: int = 50,
        email: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        user_type: Optional[str] = None,
        **kwargs: Any,
    ) -> Iterator[Dict[str, Any]]:
        """List accounts with optional filtering.

        Args:
            current_page: Page number to start from (1-indexed)
            page_size: Number of items per page
            email: Filter by email address
            first_name: Filter by first name
            last_name: Filter by last name
            user_type: Filter by user type ("INDIVIDUAL" or "COMPANY")
            **kwargs: Additional query parameters

        Yields:
            Individual account dictionaries
        """
        params = {}
        if email is not None:
            params["email"] = email
        if first_name is not None:
            params["firstName"] = first_name
        if last_name is not None:
            params["lastName"] = last_name
        if user_type is not None:
            params["userType"] = user_type

        params.update(kwargs)

        return super().list(current_page=current_page, page_size=page_size, **params)

    def link(self, individual_id: int, company_id: int) -> Dict[str, Any]:
        """Link an individual account to a company.

        Args:
            individual_id: ID of the individual account
            company_id: ID of the company account

        Returns:
            The response from the link operation
        """
        data = {
            "individualId": individual_id,
            "companyId": company_id,
        }
        return self._client.post(self._build_url("link"), json_data=data)

    def unlink(self, individual_id: int, company_id: int) -> Dict[str, Any]:
        """Remove an individual account from a company.

        Args:
            individual_id: ID of the individual account
            company_id: ID of the company account

        Returns:
            The response from the unlink operation
        """
        data = {
            "individualId": individual_id,
            "companyId": company_id,
        }
        return self._client.post(self._build_url("unlink"), json_data=data)

    def get_contacts(self, account_id: int) -> "AccountContactsResource":
        """Get the contacts resource for a company account.

        Args:
            account_id: The company account ID

        Returns:
            AccountContactsResource for managing contacts
        """
        return AccountContactsResource(self._client, self._endpoint, account_id)

    def get_donations(self, account_id: int, **kwargs: Any) -> Iterator[Dict[str, Any]]:
        """Get donations for an account.

        Args:
            account_id: The account ID
            **kwargs: Additional query parameters

        Yields:
            Individual donation dictionaries
        """
        url = self._build_url(f"{account_id}/donations")
        response = self._client.get(url, params=kwargs)

        # Handle different response structures
        if isinstance(response, list):
            for item in response:
                yield item
        elif "donations" in response:
            for item in response["donations"]:
                yield item
        elif "data" in response:
            if isinstance(response["data"], list):
                for item in response["data"]:
                    yield item

    def get_event_registrations(
        self, account_id: int, **kwargs: Any
    ) -> Iterator[Dict[str, Any]]:
        """Get event registrations for an account.

        Args:
            account_id: The account ID
            **kwargs: Additional query parameters

        Yields:
            Individual event registration dictionaries
        """
        url = self._build_url(f"{account_id}/eventRegistrations")
        response = self._client.get(url, params=kwargs)

        # Handle different response structures
        if isinstance(response, list):
            for item in response:
                yield item
        elif "eventRegistrations" in response:
            for item in response["eventRegistrations"]:
                yield item
        elif "data" in response:
            if isinstance(response["data"], list):
                for item in response["data"]:
                    yield item

    def get_memberships(
        self, account_id: int, **kwargs: Any
    ) -> Iterator[Dict[str, Any]]:
        """Get memberships for an account.

        Args:
            account_id: The account ID
            **kwargs: Additional query parameters

        Yields:
            Individual membership dictionaries
        """
        url = self._build_url(f"{account_id}/memberships")
        response = self._client.get(url, params=kwargs)

        # Handle different response structures
        if isinstance(response, list):
            for item in response:
                yield item
        elif "memberships" in response:
            for item in response["memberships"]:
                yield item
        elif "data" in response:
            if isinstance(response["data"], list):
                for item in response["data"]:
                    yield item

    def get_orders(self, account_id: int, **kwargs: Any) -> Iterator[Dict[str, Any]]:
        """Get order history for an account.

        Args:
            account_id: The account ID
            **kwargs: Additional query parameters

        Yields:
            Individual order dictionaries
        """
        url = self._build_url(f"{account_id}/orders")
        response = self._client.get(url, params=kwargs)

        # Handle different response structures
        if isinstance(response, list):
            for item in response:
                yield item
        elif "orders" in response:
            for item in response["orders"]:
                yield item
        elif "data" in response:
            if isinstance(response["data"], list):
                for item in response["data"]:
                    yield item

    def get_pledges(self, account_id: int, **kwargs: Any) -> Iterator[Dict[str, Any]]:
        """Get pledges for an account.

        Args:
            account_id: The account ID
            **kwargs: Additional query parameters

        Yields:
            Individual pledge dictionaries
        """
        url = self._build_url(f"{account_id}/pledges")
        response = self._client.get(url, params=kwargs)

        # Handle different response structures
        if isinstance(response, list):
            for item in response:
                yield item
        elif "pledges" in response:
            for item in response["pledges"]:
                yield item
        elif "data" in response:
            if isinstance(response["data"], list):
                for item in response["data"]:
                    yield item


class AccountContactsResource(RelationshipResource):
    """Resource for managing contacts within a company account."""

    def __init__(self, client: "NeonClient", endpoint: str, account_id: int) -> None:
        """Initialize the account contacts resource.

        Args:
            client: The Neon client instance
            endpoint: The base accounts endpoint
            account_id: The company account ID
        """
        super().__init__(client, endpoint, account_id, "contacts")
