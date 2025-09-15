"""Base resource class for all Neon CRM API resources."""

from typing import TYPE_CHECKING, Any, Dict, Iterator
from urllib.parse import urljoin

from ..types import SearchRequest

if TYPE_CHECKING:
    from ..client import NeonClient


class BaseResource:
    """Base class for all API resources."""

    def __init__(self, client: "NeonClient", endpoint: str) -> None:
        """Initialize the resource.

        Args:
            client: The Neon client instance
            endpoint: The base endpoint for this resource (e.g., "/accounts")
        """
        self._client = client
        self._endpoint = endpoint.rstrip("/")

    def _build_url(self, path: str = "") -> str:
        """Build a full URL for the resource.

        Args:
            path: Additional path to append to the base endpoint

        Returns:
            The full URL path
        """
        if path:
            return urljoin(self._endpoint + "/", path.lstrip("/"))
        return self._endpoint

    def list(
        self,
        current_page: int = 0,
        page_size: int = 50,
        limit: int = None,
        **kwargs: Any,
    ) -> Iterator[Dict[str, Any]]:
        """List resources with pagination.

        Args:
            current_page: Page number to start from (0-indexed)
            page_size: Number of items per page
            limit: Maximum number of items to return
            **kwargs: Additional query parameters

        Yields:
            Individual resource dictionaries
        """
        params = {
            "currentPage": current_page,
            "pageSize": page_size,
            **kwargs,
        }

        results_returned = 0
        while True:
            response = self._client.get(self._endpoint, params=params)

            # Handle different response structures
            if self._endpoint.lstrip("/") in response:
                items = response[self._endpoint.lstrip("/")]
                pagination = response.get("pagination", {})
            # elif "searchResults" in response:
            #     # Paginated search results
            #     items = response["searchResults"]
            #     pagination = response.get("pagination", {})
            # elif isinstance(response, list):
            #     # Direct list response
            #     items = response
            #     pagination = {}
            # elif "data" in response:
            #     # Response with data wrapper
            #     items = response["data"]
            #     pagination = response.get("pagination", {})
            else:
                raise Exception("Unable to parse response")

            # Yield each item
            for item in items:
                if limit is None or results_returned < limit:
                    yield item
                    results_returned += 1
                else:
                    break

            # Check if there are more pages
            if not pagination:
                break

            current_page_num = pagination.get("currentPage", 0)
            total_pages = pagination.get("totalPages", 1)

            if current_page_num >= total_pages - 1:
                break

            # Check limit for pagination continuation
            if limit is not None and results_returned >= limit:
                break

            # Update params for next page
            params["currentPage"] = current_page_num + 1

    def get(self, resource_id: int) -> Dict[str, Any]:
        """Get a specific resource by ID.

        Args:
            resource_id: The resource ID

        Returns:
            The resource data
        """
        url = self._build_url(str(resource_id))
        return self._client.get(url)

    def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new resource.

        Args:
            data: The resource data

        Returns:
            The created resource data
        """
        return self._client.post(self._endpoint, json_data=data)

    def update(self, resource_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update a resource using PUT.

        Args:
            resource_id: The resource ID
            data: The updated resource data

        Returns:
            The updated resource data
        """
        url = self._build_url(str(resource_id))
        return self._client.put(url, json_data=data)

    def patch(self, resource_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """Partially update a resource using PATCH.

        Args:
            resource_id: The resource ID
            data: The partial resource data

        Returns:
            The updated resource data
        """
        url = self._build_url(str(resource_id))
        return self._client.patch(url, json_data=data)

    def delete(self, resource_id: int) -> Dict[str, Any]:
        """Delete a resource.

        Args:
            resource_id: The resource ID

        Returns:
            The deletion response
        """
        url = self._build_url(str(resource_id))
        return self._client.delete(url)


class SearchableResource(BaseResource):
    """Base class for resources that support search functionality."""

    def search(self, search_request: SearchRequest) -> Iterator[Dict[str, Any]]:
        """Search for resources.

        Args:
            search_request: The search request parameters

        Yields:
            Individual resource dictionaries from search results
        """
        url = self._build_url("search")

        # Start with the first page
        current_page = 0
        page_size = search_request.get("pagination", {}).get("pageSize", 50)

        while True:
            # Add pagination to the search request
            request_data = search_request.copy()
            request_data["pagination"] = {
                "currentPage": current_page,
                "pageSize": page_size,
            }

            response = self._client.post(url, json_data=request_data)

            # Extract search results
            if "searchResults" in response:
                items = response["searchResults"]
                pagination = response.get("pagination", {})
            else:
                # Fallback if response structure is different
                items = response if isinstance(response, list) else [response]
                pagination = {}

            # Yield each item
            yield from items

            # Check if there are more pages
            if not pagination:
                break

            current_page_num = pagination.get("currentPage", 0)
            total_pages = pagination.get("totalPages", 1)

            if current_page_num >= total_pages - 1:
                break

            current_page += 1

    def get_search_fields(self) -> Dict[str, Any]:
        """Get available search fields for this resource.

        Returns:
            Dictionary of available search field definitions
        """
        url = self._build_url("search/searchFields")
        response = self._client.get(url)
        return response

    def get_output_fields(self) -> Dict[str, Any]:
        """Get available output fields for this resource.

        Returns:
            Dictionary of available output field definitions
        """
        url = self._build_url("search/outputFields")
        response = self._client.get(url)
        return response


class RelationshipResource(BaseResource):
    """Base class for resources that manage relationships between entities."""

    def __init__(
        self, client: "NeonClient", endpoint: str, parent_id: int, relationship: str
    ) -> None:
        """Initialize the relationship resource.

        Args:
            client: The Neon client instance
            endpoint: The base endpoint for the parent resource
            parent_id: The ID of the parent resource
            relationship: The relationship name (e.g., "contacts", "donations")
        """
        super().__init__(client, endpoint)
        self.parent_id = parent_id
        self.relationship = relationship
        self._endpoint = f"{endpoint}/{parent_id}/{relationship}"

    def list(self, **kwargs: Any) -> Iterator[Dict[str, Any]]:
        """List related resources.

        Args:
            **kwargs: Additional query parameters

        Yields:
            Individual related resource dictionaries
        """
        return super().list(**kwargs)

    def get(self, resource_id: int) -> Dict[str, Any]:
        """Get a specific related resource.

        Args:
            resource_id: The related resource ID

        Returns:
            The related resource data
        """
        return super().get(resource_id)

    def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new related resource.

        Args:
            data: The related resource data

        Returns:
            The created related resource data
        """
        return super().create(data)

    def update(self, resource_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update a related resource.

        Args:
            resource_id: The related resource ID
            data: The updated resource data

        Returns:
            The updated resource data
        """
        return super().update(resource_id, data)

    def patch(self, resource_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """Partially update a related resource.

        Args:
            resource_id: The related resource ID
            data: The partial resource data

        Returns:
            The updated resource data
        """
        return super().patch(resource_id, data)

    def delete(self, resource_id: int) -> Dict[str, Any]:
        """Delete a related resource.

        Args:
            resource_id: The related resource ID

        Returns:
            The deletion response
        """
        return super().delete(resource_id)
