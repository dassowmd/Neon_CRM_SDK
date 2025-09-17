"""Base resource class for all Neon CRM API resources."""

from typing import TYPE_CHECKING, Any, Dict, Iterator, List, Optional, Tuple
from urllib.parse import urljoin

from ..fuzzy_search import FieldFuzzySearch
from ..logging import NeonLogger
from ..types import CustomFieldCategory, SearchRequest
from ..validation import SearchRequestValidator

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
        self._logger = NeonLogger.get_logger(f"resource.{endpoint.strip('/')}")

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
        self._logger.debug(
            f"Starting list operation: page_size={page_size}, limit={limit}, kwargs={kwargs}"
        )
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
            elif isinstance(response, list):
                # Direct list response
                items = response
                pagination = {}
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

    def _get_resource_category(self) -> Optional[CustomFieldCategory]:
        """Get the CustomFieldCategory for this resource based on endpoint.

        Returns:
            The corresponding CustomFieldCategory, or None if not mappable
        """
        endpoint_to_category = {
            "/accounts": CustomFieldCategory.ACCOUNT,
            "/donations": CustomFieldCategory.DONATION,
            "/events": CustomFieldCategory.EVENT,
            "/activities": CustomFieldCategory.ACTIVITY,
            "/memberships": CustomFieldCategory.MEMBERSHIP,
            "/attendees": CustomFieldCategory.ATTENDEE,
            "/individuals": CustomFieldCategory.INDIVIDUAL,
            "/companies": CustomFieldCategory.COMPANY,
            "/products": CustomFieldCategory.PRODUCT,
            "/prospects": CustomFieldCategory.PROSPECT,
            "/grants": CustomFieldCategory.GRANT,
        }
        return endpoint_to_category.get(self._endpoint)

    def list_custom_fields(
        self,
        current_page: int = 0,
        page_size: int = 50,
        limit: Optional[int] = None,
        field_type: Optional[str] = None,
        **kwargs: Any,
    ) -> Iterator[Dict[str, Any]]:
        """List custom fields for this resource type.

        Args:
            current_page: Page number to start from (0-indexed)
            page_size: Number of items per page
            limit: Maximum number of items to return
            field_type: Filter by field type (text, number, date, etc.)
            **kwargs: Additional query parameters

        Yields:
            Individual custom field dictionaries for this resource type
        """
        category = self._get_resource_category()
        if not category:
            raise ValueError(
                f"Custom fields not supported for endpoint {self._endpoint}"
            )

        return self._client.custom_fields.list(
            current_page=current_page,
            page_size=page_size,
            limit=limit,
            field_type=field_type,
            category=category,
            **kwargs,
        )

    def get_custom_field(self, field_id: int) -> Dict[str, Any]:
        """Get a specific custom field by ID.

        Args:
            field_id: The custom field ID

        Returns:
            The custom field data
        """
        return self._client.custom_fields.get(field_id)

    def find_custom_field_by_name(self, field_name: str) -> Optional[Dict[str, Any]]:
        """Find a custom field by name for this resource type.

        Args:
            field_name: The name of the custom field to find

        Returns:
            The custom field data if found, None otherwise
        """
        category = self._get_resource_category()
        if not category:
            raise ValueError(
                f"Custom fields not supported for endpoint {self._endpoint}"
            )

        return self._client.custom_fields.find_by_name_and_category(
            field_name, category
        )

    def list_custom_field_groups(
        self,
        current_page: int = 0,
        page_size: int = 50,
        limit: Optional[int] = None,
        **kwargs: Any,
    ) -> Iterator[Dict[str, Any]]:
        """List custom field groups for this resource type.

        Args:
            current_page: Page number to start from (0-indexed)
            page_size: Number of items per page
            limit: Maximum number of items to return
            **kwargs: Additional query parameters

        Yields:
            Individual custom field group dictionaries for this resource type
        """
        category = self._get_resource_category()
        if not category:
            raise ValueError(
                f"Custom field groups not supported for endpoint {self._endpoint}"
            )

        return self._client.custom_fields.list_groups(
            current_page=current_page,
            page_size=page_size,
            limit=limit,
            category=category,
            **kwargs,
        )

    def get_custom_field_group(self, group_id: int) -> Dict[str, Any]:
        """Get a specific custom field group by ID.

        Args:
            group_id: The custom field group ID

        Returns:
            The custom field group data
        """
        return self._client.custom_fields.get_group(group_id)

    def find_custom_field_group_by_name(
        self, group_name: str
    ) -> Optional[Dict[str, Any]]:
        """Find a custom field group by name for this resource type.

        Args:
            group_name: The name of the custom field group to find

        Returns:
            The custom field group data if found, None otherwise
        """
        category = self._get_resource_category()
        if not category:
            raise ValueError(
                f"Custom field groups not supported for endpoint {self._endpoint}"
            )

        return self._client.custom_fields.find_group_by_name_and_category(
            group_name, category
        )

    def fuzzy_search_fields(
        self,
        query: str,
        field_type: str = "search",
        threshold: float = 0.3,
        max_results: int = 10,
        include_semantic: bool = True,
    ) -> List[Tuple[str, float, str]]:
        """Search for available fields using fuzzy and semantic matching.

        Args:
            query: The search query for field names
            field_type: Type of fields to search ('search', 'output', or 'all')
            threshold: Minimum similarity score (0.0-1.0) to include in results
            max_results: Maximum number of results to return
            include_semantic: Whether to include semantic similarity matching

        Returns:
            List of (field_name, score, match_type) tuples sorted by score

        Example:
            # Search for fields similar to "email"
            results = client.accounts.fuzzy_search_fields("email")
            for field_name, score, match_type in results:
                print(f"{field_name} - Score: {score:.2f} ({match_type})")

            # Search only output fields similar to "address"
            results = client.accounts.fuzzy_search_fields("address", field_type="output")
        """
        if not query:
            return []

        self._logger.debug(f"Fuzzy searching {field_type} fields for '{query}'")

        # Get available field names based on type
        try:
            if field_type == "search":
                available_fields = self._validator._get_available_search_fields()
            elif field_type == "output":
                available_fields = self._validator._get_available_output_fields()
            else:  # field_type == "all"
                search_fields = self._validator._get_available_search_fields()
                output_fields = self._validator._get_available_output_fields()
                available_fields = list(set(search_fields + output_fields))
        except Exception as e:
            self._logger.warning(f"Could not fetch available fields: {e}")
            return []

        if not available_fields:
            self._logger.debug("No available fields found for fuzzy search")
            return []

        # Perform fuzzy and semantic search
        fuzzy_search = FieldFuzzySearch(case_sensitive=False)

        if include_semantic:
            results = fuzzy_search.search_fields_combined(
                query,
                available_fields,
                fuzzy_threshold=threshold,
                semantic_threshold=0.1,
                max_results=max_results,
            )
        else:
            # Fuzzy only
            fuzzy_matches = fuzzy_search.search_standard_fields(
                query, available_fields, threshold, max_results
            )
            results = [(field, score, "fuzzy") for field, score in fuzzy_matches]

        self._logger.debug(f"Found {len(results)} field matches for '{query}'")
        return results

    def suggest_field_corrections(
        self, invalid_field: str, field_type: str = "search", max_suggestions: int = 5
    ) -> Dict[str, List[str]]:
        """Suggest corrections for an invalid field name.

        Args:
            invalid_field: The invalid field name
            field_type: Type of fields to search ('search', 'output', or 'all')
            max_suggestions: Maximum number of suggestions to return

        Returns:
            Dictionary with 'fuzzy_suggestions' and 'semantic_suggestions' keys

        Example:
            suggestions = client.accounts.suggest_field_corrections("frist_name")
            if suggestions['fuzzy_suggestions']:
                print("Did you mean:")
                for suggestion in suggestions['fuzzy_suggestions']:
                    print(f"  - {suggestion}")

            if suggestions['semantic_suggestions']:
                print("Or perhaps you meant:")
                for suggestion in suggestions['semantic_suggestions']:
                    print(f"  - {suggestion}")
        """
        if not invalid_field:
            return {"fuzzy_suggestions": [], "semantic_suggestions": []}

        self._logger.debug(f"Generating field suggestions for '{invalid_field}'")

        # Get available field names
        try:
            if field_type == "search":
                available_fields = self._validator._get_available_search_fields()
            elif field_type == "output":
                available_fields = self._validator._get_available_output_fields()
            else:  # field_type == "all"
                search_fields = self._validator._get_available_search_fields()
                output_fields = self._validator._get_available_output_fields()
                available_fields = list(set(search_fields + output_fields))
        except Exception as e:
            self._logger.warning(f"Could not fetch available fields: {e}")
            return {"fuzzy_suggestions": [], "semantic_suggestions": []}

        if not available_fields:
            return {"fuzzy_suggestions": [], "semantic_suggestions": []}

        # Generate suggestions
        fuzzy_search = FieldFuzzySearch(case_sensitive=False)

        # Fuzzy suggestions (typos, similar names)
        fuzzy_suggestions = fuzzy_search.suggest_corrections(
            invalid_field,
            available_fields,
            threshold=0.3,
            max_suggestions=max_suggestions,
        )

        # Semantic suggestions (related meaning)
        semantic_matches = (
            fuzzy_search.semantic_matcher.find_semantically_similar_fields(
                invalid_field,
                available_fields,
                threshold=0.1,
                max_results=max_suggestions,
            )
        )
        semantic_suggestions = [match[0] for match in semantic_matches]

        # Remove duplicates between fuzzy and semantic suggestions
        semantic_suggestions = [
            s for s in semantic_suggestions if s not in fuzzy_suggestions
        ]

        result = {
            "fuzzy_suggestions": fuzzy_suggestions,
            "semantic_suggestions": semantic_suggestions,
        }

        self._logger.debug(
            f"Generated {len(fuzzy_suggestions)} fuzzy and {len(semantic_suggestions)} semantic suggestions"
        )
        return result


class SearchableResource(BaseResource):
    """Base class for resources that support search functionality."""

    def __init__(self, client: "NeonClient", endpoint: str) -> None:
        """Initialize the searchable resource."""
        super().__init__(client, endpoint)
        # Extract resource name from endpoint for validation
        resource_name = endpoint.lstrip("/").rstrip(
            "s"
        )  # Remove leading slash and trailing 's'
        self._validator = SearchRequestValidator(resource_name, client)

    def search(
        self, search_request: SearchRequest, validate: bool = True
    ) -> Iterator[Dict[str, Any]]:
        """Search for resources.

        Args:
            search_request: The search request parameters
            validate: Whether to validate the search request (default: True)

        Yields:
            Individual resource dictionaries from search results

        Raises:
            ValueError: If validation is enabled and the search request is invalid
        """
        import time

        self._logger.debug(
            f"Starting search operation: fields={len(search_request.get('searchFields', []))}, validate={validate}"
        )

        # Validate search request if requested
        if validate:
            validation_start = time.time()
            errors = self._validator.validate_search_request(search_request)
            validation_time = time.time() - validation_start

            if errors:
                self._logger.warning(
                    f"Search validation failed in {validation_time:.3f}s: {'; '.join(errors)}"
                )
                raise ValueError(f"Invalid search request: {'; '.join(errors)}")

            self._logger.debug(f"Search validation passed in {validation_time:.3f}s")

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
        # Use caching if available
        if self._client._cache:
            cache_key = self._client._cache.create_cache_key(
                "search_fields", self._endpoint
            )

            def _fetch_search_fields():
                url = self._build_url("search/searchFields")
                return self._client.get(url)

            return self._client._cache.search_fields.cache_get_or_set(
                cache_key, _fetch_search_fields
            )

        # Fallback to non-cached version
        url = self._build_url("search/searchFields")
        response = self._client.get(url)
        return response

    def get_output_fields(self) -> Dict[str, Any]:
        """Get available output fields for this resource.

        Returns:
            Dictionary of available output field definitions
        """
        # Use caching if available
        if self._client._cache:
            cache_key = self._client._cache.create_cache_key(
                "output_fields", self._endpoint
            )

            def _fetch_output_fields():
                url = self._build_url("search/outputFields")
                return self._client.get(url)

            return self._client._cache.output_fields.cache_get_or_set(
                cache_key, _fetch_output_fields
            )

        # Fallback to non-cached version
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
