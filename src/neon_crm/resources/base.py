"""Base resource class for all Neon CRM API resources."""

from typing import TYPE_CHECKING, Any, Dict, Iterator, List, Optional, Tuple
from urllib.parse import urljoin

from ..fuzzy_search import FieldFuzzySearch
from ..governance import Permission, ResourceType, PermissionChecker
from ..logging import NeonLogger
from ..types import CustomFieldCategory, SearchRequest
from ..validation import SearchRequestValidator

if TYPE_CHECKING:
    from ..client import NeonClient
    from ..custom_field_manager import BatchResult, ValidationResult


class BaseResource:
    """Base class for all API resources."""

    # Each resource should define its ResourceType
    _resource_type: ResourceType = (
        ResourceType.ACCOUNTS
    )  # Default, should be overridden

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

    def get(self, resource_id: int) -> Dict[str, Any]:
        """Get a specific resource by ID.

        Args:
            resource_id: The resource ID

        Returns:
            The resource data
        """
        # Check permissions
        PermissionChecker.ensure_permission(self._resource_type, Permission.READ)

        url = self._build_url(str(resource_id))
        return self._client.get(url)

    def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new resource.

        Args:
            data: The resource data

        Returns:
            The created resource data
        """
        # Check permissions
        PermissionChecker.ensure_permission(self._resource_type, Permission.WRITE)

        return self._client.post(self._endpoint, json_data=data)

    def update(
        self, resource_id: int, data: Dict[str, Any], update_type: str = "partial"
    ) -> Dict[str, Any]:
        """Update a resource with configurable update type.

        Args:
            resource_id: The resource ID
            data: The resource data to update
            update_type: Type of update - "full" for PUT (complete replacement)
                        or "partial" for PATCH (partial update). Default: "partial"

        Returns:
            The updated resource data
        """
        if update_type == "full":
            return self.put(resource_id, data)
        elif update_type == "partial":
            return self.patch(resource_id, data)
        else:
            raise ValueError(
                f"Invalid update_type '{update_type}'. Must be 'full' or 'partial'"
            )

    def put(self, resource_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update a resource using PUT (full replacement).

        Args:
            resource_id: The resource ID
            data: The complete resource data

        Returns:
            The updated resource data
        """
        # Check permissions
        PermissionChecker.ensure_permission(self._resource_type, Permission.UPDATE)

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
        # Check permissions
        PermissionChecker.ensure_permission(self._resource_type, Permission.UPDATE)

        url = self._build_url(str(resource_id))
        return self._client.patch(url, json_data=data)

    def delete(self, resource_id: int) -> Dict[str, Any]:
        """Delete a resource.

        Args:
            resource_id: The resource ID

        Returns:
            The deletion response
        """
        # Check permissions
        PermissionChecker.ensure_permission(self._resource_type, Permission.DELETE)

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

    # Advanced Custom Field Management Methods

    def get_custom_field_value(self, resource_id: int, field_name: str) -> Any:
        """Get the current value of a custom field for a resource.

        Args:
            resource_id: ID of the resource
            field_name: Name of the custom field

        Returns:
            Current field value, parsed to appropriate Python type

        Example:
            >>> client.accounts.get_custom_field_value(123, "V-Volunteer Skills")
            ['Technology', 'Writing', 'Data Entry']
        """
        from ..custom_field_manager import CustomFieldValueManager

        resource_name = self._endpoint.lstrip("/")
        manager = CustomFieldValueManager(self._client, resource_name)
        return manager.get_custom_field_value(resource_id, field_name)

    def set_custom_field_value(
        self, resource_id: int, field_name: str, value: Any, validate: bool = True
    ) -> bool:
        """Set a custom field value for a resource.

        Args:
            resource_id: ID of the resource
            field_name: Name of the custom field
            value: Value to set
            validate: Whether to validate the value before setting

        Returns:
            True if successful, False otherwise

        Example:
            >>> client.accounts.set_custom_field_value(123, "V-Tech Skills", ["Python", "API Development"])
            True
        """
        from ..custom_field_manager import CustomFieldValueManager

        resource_name = self._endpoint.lstrip("/")
        manager = CustomFieldValueManager(self._client, resource_name)
        return manager.set_custom_field_value(resource_id, field_name, value, validate)

    def add_to_multivalue_field(
        self, resource_id: int, field_name: str, new_option: str
    ) -> bool:
        """Add an option to a multi-value field without losing existing values.

        Args:
            resource_id: ID of the resource
            field_name: Name of the multi-value custom field
            new_option: Option to add

        Returns:
            True if successful, False otherwise

        Example:
            >>> client.accounts.add_to_multivalue_field(123, "V-Volunteer Skills", "Technology")
            True
        """
        from ..custom_field_manager import CustomFieldValueManager

        resource_name = self._endpoint.lstrip("/")
        manager = CustomFieldValueManager(self._client, resource_name)
        return manager.add_to_multivalue_field(resource_id, field_name, new_option)

    def remove_from_multivalue_field(
        self, resource_id: int, field_name: str, option_to_remove: str
    ) -> bool:
        """Remove an option from a multi-value field.

        Args:
            resource_id: ID of the resource
            field_name: Name of the multi-value custom field
            option_to_remove: Option to remove

        Returns:
            True if successful, False otherwise

        Example:
            >>> client.accounts.remove_from_multivalue_field(123, "V-Volunteer Skills", "Data Entry")
            True
        """
        from ..custom_field_manager import CustomFieldValueManager

        resource_name = self._endpoint.lstrip("/")
        manager = CustomFieldValueManager(self._client, resource_name)
        return manager.remove_from_multivalue_field(
            resource_id, field_name, option_to_remove
        )

    def append_to_text_field(
        self,
        resource_id: int,
        field_name: str,
        additional_text: str,
        separator: str = " ",
    ) -> bool:
        """Append text to a text field.

        Args:
            resource_id: ID of the resource
            field_name: Name of the text custom field
            additional_text: Text to append
            separator: Separator between existing and new text

        Returns:
            True if successful, False otherwise

        Example:
            >>> client.accounts.append_to_text_field(123, "V-Notes", "Updated contact info")
            True
        """
        from ..custom_field_manager import CustomFieldValueManager

        resource_name = self._endpoint.lstrip("/")
        manager = CustomFieldValueManager(self._client, resource_name)
        return manager.append_to_text_field(
            resource_id, field_name, additional_text, separator
        )

    def clear_custom_field_value(self, resource_id: int, field_name: str) -> bool:
        """Clear a custom field value.

        Args:
            resource_id: ID of the resource
            field_name: Name of the custom field

        Returns:
            True if successful, False otherwise

        Example:
            >>> client.accounts.clear_custom_field_value(123, "V-Temp Field")
            True
        """
        from ..custom_field_manager import CustomFieldValueManager

        resource_name = self._endpoint.lstrip("/")
        manager = CustomFieldValueManager(self._client, resource_name)
        return manager.clear_custom_field_value(resource_id, field_name)

    def set_multiple_custom_field_values(
        self, resource_id: int, field_values: Dict[str, Any], validate: bool = True
    ) -> "BatchResult":
        """Set multiple custom field values in a single operation.

        Args:
            resource_id: ID of the resource
            field_values: Dictionary mapping field names to values
            validate: Whether to validate values before setting

        Returns:
            BatchResult with operation statistics

        Example:
            >>> result = client.accounts.set_multiple_custom_field_values(123, {
            ...     "V-Skills": ["Python", "JavaScript"],
            ...     "V-Notes": "Updated profile",
            ...     "V-Active": True
            ... })
            >>> print(f"Success: {result.successful}, Failed: {result.failed}")
        """
        from ..custom_field_manager import CustomFieldValueManager

        resource_name = self._endpoint.lstrip("/")
        manager = CustomFieldValueManager(self._client, resource_name)
        return manager.set_multiple_custom_field_values(
            resource_id, field_values, validate
        )

    def validate_custom_field_value(
        self, field_name: str, value: Any
    ) -> "ValidationResult":
        """Validate a value for a custom field.

        Args:
            field_name: Name of the custom field
            value: Value to validate

        Returns:
            ValidationResult with validation status and messages

        Example:
            >>> result = client.accounts.validate_custom_field_value("V-Skills", ["Python", "InvalidSkill"])
            >>> if not result.is_valid:
            ...     print(f"Validation errors: {result.errors}")
        """
        from ..custom_field_manager import CustomFieldValueManager

        resource_name = self._endpoint.lstrip("/")
        manager = CustomFieldValueManager(self._client, resource_name)
        return manager.validate_field_value(field_name, value)

    def search_by_custom_field_value(
        self,
        field_name: str,
        value: Any,
        operator: str = "EQUAL",
        limit: Optional[int] = None,
    ) -> Iterator[Dict[str, Any]]:
        """Search for resources by custom field value.

        Args:
            field_name: Name of the custom field to search by
            value: Value to search for
            operator: Search operator (EQUAL, NOT_EQUAL, CONTAINS, etc.)
            limit: Maximum number of results to return

        Yields:
            Individual resource dictionaries matching the search

        Example:
            >>> for account in client.accounts.search_by_custom_field_value("V-Skills", "Technology"):
            ...     print(f"{account['firstName']} {account['lastName']}")
        """
        search_request = {
            "searchFields": [
                {"field": field_name, "operator": operator, "value": str(value)}
            ],
            "outputFields": ["*"],  # Get all available fields
        }

        if hasattr(self, "search"):
            yield from self.search(search_request, limit=limit)
        else:
            raise NotImplementedError("Search not supported for this resource type")

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


class ListableResource(BaseResource):
    """Base class for resources that support list functionality."""

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


class SearchableResource(BaseResource):
    """Base class for resources that support search functionality."""

    def __init__(self, client: "NeonClient", endpoint: str) -> None:
        """Initialize the searchable resource."""
        super().__init__(client, endpoint)
        # Extract resource name from endpoint for validation
        # Use the endpoint directly without stripping 's' to match client attributes
        resource_name = endpoint.lstrip("/")  # Remove leading slash only
        self._validator = SearchRequestValidator(resource_name, client)

    def _is_standard_field(self, field_name: str) -> bool:
        """Check if a field name is a standard field for this resource.

        Args:
            field_name: The field name to check

        Returns:
            True if the field is a standard field, False otherwise
        """
        try:
            available_fields = self.get_output_fields()
            standard_fields = available_fields.get("standardFields", [])

            # Check if field_name exists in standard fields
            if isinstance(standard_fields, list):
                return field_name in standard_fields

        except Exception:
            # If we can't get standard fields, assume it might be custom
            pass

        return False

    def _convert_field_names_to_ids(
        self, search_request: SearchRequest
    ) -> SearchRequest:
        """Convert custom field names to their integer IDs in search and output fields.

        Args:
            search_request: The search request with potential custom field names

        Returns:
            Search request with custom field names converted to appropriate ID format
        """
        # Make a copy to avoid modifying the original
        converted_request = search_request.copy()

        # Get the resource category for custom field lookups
        category = self._get_resource_category()
        if not category:
            self._logger.debug("No custom field category mapping for this resource")
            return converted_request

        # Convert custom field names in searchFields
        search_fields = converted_request.get("searchFields", [])
        if search_fields:
            for field in search_fields:
                if isinstance(field, dict) and "field" in field:
                    field_name = field["field"]
                    # Skip if already an integer ID (existing custom field ID)
                    if isinstance(field_name, int):
                        continue
                    # Skip if already a digit string (existing custom field ID like "123")
                    if isinstance(field_name, str) and field_name.isdigit():
                        continue

                    # Skip if this is a standard field - no need to convert
                    if self._is_standard_field(field_name):
                        continue

                    # Try to find custom field by name
                    custom_field = self._client.custom_fields.find_by_name_and_category(
                        field_name, category
                    )
                    if custom_field and "id" in custom_field:
                        # Convert to string for search fields (API expects strings)
                        field["field"] = str(custom_field["id"])
                        self._logger.debug(
                            f"Converted custom field name '{field_name}' to ID string '{custom_field['id']}' for search"
                        )

        # Convert custom field names in outputFields
        output_fields = converted_request.get("outputFields", [])
        if output_fields:
            converted_output_fields = []
            for field_name in output_fields:
                # Skip if already an integer ID (existing custom field ID)
                if isinstance(field_name, int):
                    converted_output_fields.append(field_name)
                    continue
                # Skip if already a digit string (existing custom field ID like "123")
                if isinstance(field_name, str) and field_name.isdigit():
                    converted_output_fields.append(field_name)
                    continue

                # Skip if this is a standard field - no need to convert
                if self._is_standard_field(field_name):
                    converted_output_fields.append(field_name)
                    continue

                # Try to find custom field by name
                custom_field = self._client.custom_fields.find_by_name_and_category(
                    field_name, category
                )
                if custom_field and "id" in custom_field:
                    # Convert to integer for output fields (API expects integers)
                    converted_output_fields.append(custom_field["id"])
                    self._logger.debug(
                        f"Converted custom field name '{field_name}' to ID integer {custom_field['id']} for output"
                    )
                else:
                    # Keep original field name if not found as custom field (might be standard field)
                    converted_output_fields.append(field_name)

            converted_request["outputFields"] = converted_output_fields

        return converted_request

    def _get_primary_key_field(self) -> str:
        """Get the primary key field name for this resource.

        Returns:
            The primary key field name (e.g., 'accountId', 'donationId')
        """
        endpoint_to_primary_key = {
            "/accounts": "accountId",
            "/donations": "donationId",
            "/events": "eventId",
            "/activities": "activityId",
            "/memberships": "membershipId",
            "/attendees": "attendeeId",
            "/individuals": "individualId",
            "/companies": "companyId",
            "/products": "productId",
            "/prospects": "prospectId",
            "/grants": "grantId",
            "/households": "householdId",
            "/pledges": "pledgeId",
            "/recurring-donations": "recurringDonationId",
            "/soft-credits": "softCreditId",
            "/orders": "orderId",
            "/payments": "paymentId",
            "/volunteers": "volunteerId",
        }
        return endpoint_to_primary_key.get(self._endpoint, "id")

    def _chunk_fields(
        self, fields: List[Any], chunk_size: int = 299
    ) -> List[List[Any]]:
        """Split a list of fields into chunks, ensuring primary key is in each chunk.

        Args:
            fields: List of field names/IDs to chunk
            chunk_size: Maximum fields per chunk (default 299 to leave room for primary key)

        Returns:
            List of field chunks, each containing up to chunk_size fields plus primary key
        """
        if len(fields) <= 300:
            return [fields]

        primary_key = self._get_primary_key_field()

        # Remove primary key from fields if already present to avoid duplication
        fields_without_pk = [f for f in fields if f != primary_key]

        chunks = []
        for i in range(0, len(fields_without_pk), chunk_size):
            chunk = [primary_key] + fields_without_pk[i : i + chunk_size]
            chunks.append(chunk)

        self._logger.info(
            f"Split {len(fields)} fields into {len(chunks)} chunks "
            f"(max {chunk_size + 1} fields per chunk including primary key)"
        )

        return chunks

    def _merge_chunked_results(
        self, chunk_results: List[List[Dict[str, Any]]], primary_key: str
    ) -> List[Dict[str, Any]]:
        """Merge results from multiple field chunks back into unified records.

        Uses the first chunk as authoritative for record set consistency,
        filtering out phantom records that appear mid-search.

        Args:
            chunk_results: List of result lists from each field chunk
            primary_key: Primary key field name to use for merging

        Returns:
            List of merged records with all fields, filtered for consistency
        """
        if not chunk_results or not chunk_results[0]:
            return []

        # Use first chunk to establish authoritative record set
        # This prevents phantom records added mid-search from corrupting results
        first_chunk = chunk_results[0]
        authoritative_keys = {
            record.get(primary_key)
            for record in first_chunk
            if record.get(primary_key) is not None
        }

        self._logger.debug(
            f"Using first chunk as authoritative with {len(authoritative_keys)} records"
        )

        # Track records and detect inconsistencies
        merged_records = {}
        chunk_keys_by_index = []

        # Process each chunk
        for chunk_idx, chunk_items in enumerate(chunk_results):
            chunk_keys = set()

            for record in chunk_items:
                pk_value = record.get(primary_key)
                if pk_value is not None:
                    chunk_keys.add(pk_value)

                    # Only process records that were in the first chunk (authoritative set)
                    if pk_value in authoritative_keys:
                        # Initialize record if first time seeing this primary key
                        if pk_value not in merged_records:
                            merged_records[pk_value] = {primary_key: pk_value}

                        # Merge all fields from this record
                        for field_name, field_value in record.items():
                            merged_records[pk_value][field_name] = field_value

            chunk_keys_by_index.append(chunk_keys)

        # Analyze consistency and detect phantom/missing records
        self._analyze_chunk_consistency(
            chunk_keys_by_index, authoritative_keys, primary_key
        )

        # Sort by primary key to ensure deterministic ordering
        def sort_key(x):
            """Sort key function that handles both numeric and string keys."""
            str_x = str(x)
            if str_x.isdigit():
                return (0, int(x))  # Numeric keys sort first, by numeric value
            else:
                return (1, str_x.lower())  # String keys sort second, case-insensitive

        sorted_keys = sorted(authoritative_keys, key=sort_key)

        # Only return records that exist in merged_records (complete data)
        complete_records = [
            merged_records[pk] for pk in sorted_keys if pk in merged_records
        ]

        self._logger.debug(
            f"Merged {len(chunk_results)} chunks into {len(complete_records)} complete records"
        )

        return complete_records

    def _analyze_chunk_consistency(
        self, chunk_keys_by_index: List[set], authoritative_keys: set, primary_key: str
    ) -> None:
        """Analyze consistency across chunks and log detailed diagnostics.

        Args:
            chunk_keys_by_index: List of sets containing keys found in each chunk
            authoritative_keys: Set of keys from the first (authoritative) chunk
            primary_key: Primary key field name for logging
        """
        # Check for phantom records (appear in later chunks but not first)
        phantom_records = set()
        missing_records = set()

        for chunk_idx, chunk_keys in enumerate(chunk_keys_by_index[1:], 1):
            # Records in this chunk but not in authoritative set
            phantom_in_chunk = chunk_keys - authoritative_keys
            if phantom_in_chunk:
                phantom_records.update(phantom_in_chunk)
                self._logger.warning(
                    f"Phantom records detected in chunk {chunk_idx}: "
                    f"{sorted(phantom_in_chunk)} "
                    f"(likely added to database mid-search)"
                )

            # Records missing from this chunk that should be there
            missing_in_chunk = authoritative_keys - chunk_keys
            if missing_in_chunk:
                missing_records.update(missing_in_chunk)
                self._logger.warning(
                    f"Records missing from chunk {chunk_idx}: "
                    f"{sorted(missing_in_chunk)} "
                    f"(may indicate data deletion or API inconsistency)"
                )

        # Summary statistics
        chunk_sizes = [len(keys) for keys in chunk_keys_by_index]
        if len(set(chunk_sizes)) > 1:
            self._logger.info(
                f"Chunk size variation detected - Sizes: {chunk_sizes}, "
                f"Phantom: {len(phantom_records)}, Missing: {len(missing_records)}"
            )

        if phantom_records:
            self._logger.info(
                f"Filtered out {len(phantom_records)} phantom records to maintain "
                f"consistent snapshot (records added during search execution)"
            )

    def _prepare_search_request(self, search_request: SearchRequest) -> SearchRequest:
        """Prepare search request by handling missing or wildcard output_fields and type conversions.

        Args:
            search_request: The original search request

        Returns:
            Modified search request with proper output_fields and field type conversions
        """
        # First convert custom field names to IDs
        search_request = self._convert_field_names_to_ids(search_request)

        # Make a copy to avoid modifying the original
        prepared_request = search_request.copy()

        # Fix integer conversions in searchFields: integers should be strings
        search_fields = prepared_request.get("searchFields", [])
        if search_fields:
            for field in search_fields:
                if isinstance(field, dict) and "value" in field:
                    # Convert integer values to strings (API expects strings)
                    if isinstance(field["value"], int):
                        field["value"] = str(field["value"])
                        self._logger.debug(
                            f"Converted integer search value to string: {field['field']} = '{field['value']}'"
                        )

        # Fix integer conversions in outputFields: all-digit strings should be integers
        output_fields = prepared_request.get("outputFields", [])
        if output_fields:
            converted_fields = []
            for field in output_fields:
                if isinstance(field, str) and field.isdigit():
                    # Convert all-digit strings to integers
                    converted_field = int(field)
                    converted_fields.append(converted_field)
                    self._logger.debug(
                        f"Converted all-digit string to integer in outputFields: '{field}' -> {converted_field}"
                    )
                else:
                    converted_fields.append(field)
            prepared_request["outputFields"] = converted_fields
            output_fields = converted_fields

        # Handle missing output_fields or wildcard '*'
        if not output_fields or (len(output_fields) == 1 and output_fields[0] == "*"):
            self._logger.debug(
                "Output fields missing or wildcard detected, fetching available fields"
            )

            try:
                # Get all available output fields
                available_fields = self.get_output_fields()

                all_fields = []

                # Add standard fields
                standard_fields = available_fields.get("standardFields", [])
                if isinstance(standard_fields, list):
                    all_fields.extend(standard_fields)

                # Add custom fields (use display names with type inference)
                custom_fields = available_fields.get("customFields", [])
                for field in custom_fields:
                    if isinstance(field, dict) and "displayName" in field:
                        all_fields.append(field["displayName"])

                        # Log type information for debugging
                        from ..custom_field_types import CustomFieldTypeMapper

                        field_info = CustomFieldTypeMapper.get_field_info(field)
                        self._logger.debug(
                            f"Custom field '{field['displayName']}': "
                            f"dataType={field_info['dataType']}, "
                            f"displayType={field_info['displayType']}, "
                            f"inferredType={field_info['pythonTypeName']}"
                        )
                    elif isinstance(field, str):
                        all_fields.append(field)

                if all_fields:
                    prepared_request["outputFields"] = all_fields
                    self._logger.debug(
                        f"Auto-populated {len(all_fields)} output fields"
                    )
                else:
                    self._logger.warning("No output fields available for this resource")

            except Exception as e:
                self._logger.warning(f"Failed to fetch output fields: {e}")
                # Fall back to original request if field discovery fails

        return prepared_request

    def _execute_chunked_search(
        self, search_request: SearchRequest, limit: Optional[int] = None
    ) -> Iterator[Dict[str, Any]]:
        """Execute search with field chunking for >300 field requests.

        Ensures consistent record ordering across all chunks by adding explicit sorting.

        Args:
            search_request: The prepared search request
            limit: Maximum number of results to return

        Yields:
            Individual merged resource dictionaries
        """
        output_fields = search_request.get("outputFields", [])
        field_chunks = self._chunk_fields(output_fields)
        primary_key = self._get_primary_key_field()

        url = self._build_url("search")
        page_size = search_request.get("pagination", {}).get("pageSize", 50)
        current_page = 0
        results_returned = 0

        # Ensure consistent ordering across chunks by adding sort parameter
        base_request = search_request.copy()
        if "sortBy" not in base_request:
            # Add explicit sort by primary key to guarantee consistent ordering
            base_request["sortBy"] = [{"field": primary_key, "direction": "ASC"}]
            self._logger.debug(
                f"Added explicit sorting by {primary_key} to ensure consistent ordering across field chunks"
            )

        while True:
            # Execute all field chunks for this page
            chunk_results = []
            pagination = {}

            for chunk_idx, field_chunk in enumerate(field_chunks):
                # Create request for this field chunk
                chunk_request = base_request.copy()
                chunk_request["outputFields"] = field_chunk
                chunk_request["pagination"] = {
                    "currentPage": current_page,
                    "pageSize": page_size,
                }

                self._logger.debug(
                    f"Executing chunk {chunk_idx + 1}/{len(field_chunks)} "
                    f"with {len(field_chunk)} fields (page {current_page})"
                )

                response = self._client.post(url, json_data=chunk_request)

                # Extract search results
                if "searchResults" in response:
                    chunk_items = response["searchResults"]
                    # Use pagination from first chunk as canonical
                    if chunk_idx == 0:
                        pagination = response.get("pagination", {})
                else:
                    # Fallback if response structure is different
                    chunk_items = response if isinstance(response, list) else [response]
                    if chunk_idx == 0:
                        pagination = {}

                chunk_results.append(chunk_items)

            # Merge results from all chunks
            if chunk_results:
                merged_items = self._merge_chunked_results(chunk_results, primary_key)

                # Yield merged items with limit checking
                for item in merged_items:
                    if limit is None or results_returned < limit:
                        yield item
                        results_returned += 1
                    else:
                        return  # Stop iteration when limit is reached

            # Check if there are more pages (using pagination from first chunk)
            if not pagination:
                break

            current_page_num = pagination.get("currentPage", 0)
            total_pages = pagination.get("totalPages", 1)

            if current_page_num >= total_pages - 1:
                break

            current_page += 1

    def search(
        self,
        search_request: SearchRequest,
        validate: bool = False,  # TODO figure out why validation doesnt play well with dates (beacuse they are strings)
        limit: Optional[int] = None,
    ) -> Iterator[Dict[str, Any]]:
        """Search for resources.

        Args:
            search_request: The search request parameters
            validate: Whether to validate the search request (default: True)
            limit: Maximum number of results to return (overrides pagination)

        Yields:
            Individual resource dictionaries from search results

        Raises:
            ValueError: If validation is enabled and the search request is invalid
        """
        # Check permissions
        PermissionChecker.ensure_permission(self._resource_type, Permission.READ)

        import time

        self._logger.debug(
            f"Starting search operation: fields={len(search_request.get('outputFields', []))}, validate={validate}, limit={limit}"
        )

        # TEMPORARILY DISABLED: Convert field names from display format to API format
        # The API actually expects display format field names, not camelCase
        # from ..field_mapping import FieldNameMapper
        # search_request = FieldNameMapper.convert_search_request(search_request)

        # Handle missing or wildcard output_fields
        search_request = self._prepare_search_request(search_request)

        # Check if we need field chunking
        output_fields = search_request.get("outputFields", [])
        if len(output_fields) > 300:
            self._logger.info(
                f"Field count ({len(output_fields)}) exceeds 300 limit. "
                f"Using automatic field chunking for transparent handling."
            )
            yield from self._execute_chunked_search(search_request, limit)
            return

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
        results_returned = 0

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

            # Yield each item with limit checking
            for item in items:
                if limit is None or results_returned < limit:
                    yield item
                    results_returned += 1
                else:
                    return  # Stop iteration when limit is reached

            # Check if there are more pages
            if not pagination:
                break

            current_page_num = pagination.get("currentPage", 0)
            total_pages = pagination.get("totalPages", 1)

            if current_page_num >= total_pages - 1:
                break

            current_page += 1

    def search_paginated(
        self,
        search_request: SearchRequest,
        page_size: int = 50,
        max_pages: Optional[int] = None,
        validate: bool = True,
    ) -> Iterator[Dict[str, Any]]:
        """Search with explicit pagination control.

        Args:
            search_request: The search request parameters
            page_size: Number of results per page
            max_pages: Maximum number of pages to retrieve (None for all)
            validate: Whether to validate the search request

        Yields:
            Individual resource dictionaries from search results
        """
        # Calculate limit from page constraints
        limit = None
        if max_pages is not None:
            limit = max_pages * page_size

        # Set pagination in the search request
        search_request = search_request.copy()
        search_request["pagination"] = {
            "pageSize": page_size,
            "currentPage": 0,
        }

        # Use the search method with limit
        yield from self.search(search_request, validate=validate, limit=limit)

    def get_search_fields(self) -> Dict[str, Any]:
        """Get available search fields for this resource.

        Returns:
            Dictionary of available search field definitions

        Raises:
            NotImplementedError: If this resource doesn't support field discovery
        """
        try:
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
        except Exception as e:
            # Check if this is a 404 error indicating the endpoint doesn't exist
            if (
                hasattr(e, "response")
                and hasattr(e.response, "status_code")
                and e.response.status_code == 404
            ):
                raise NotImplementedError(
                    f"Resource {self._endpoint} does not support search field discovery"
                )
            elif "404" in str(e):
                raise NotImplementedError(
                    f"Resource {self._endpoint} does not support search field discovery"
                )
            else:
                # Re-raise other errors
                raise

    def get_output_fields(self) -> Dict[str, Any]:
        """Get available output fields for this resource.

        Returns:
            Dictionary of available output field definitions

        Raises:
            NotImplementedError: If this resource doesn't support field discovery
        """
        try:
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
        except Exception as e:
            # Check if this is a 404 error indicating the endpoint doesn't exist
            if (
                hasattr(e, "response")
                and hasattr(e.response, "status_code")
                and e.response.status_code == 404
            ):
                raise NotImplementedError(
                    f"Resource {self._endpoint} does not support output field discovery"
                )
            elif "404" in str(e):
                raise NotImplementedError(
                    f"Resource {self._endpoint} does not support output field discovery"
                )
            else:
                # Re-raise other errors
                raise


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


class CalculationResource(BaseResource):
    """Base class for resources that provide calculation functionality."""

    def calculate(
        self, calculation_data: Dict[str, Any], calculation_type: str = ""
    ) -> Dict[str, Any]:
        """Perform a calculation using the resource's calculation endpoint.

        Args:
            calculation_data: The data to use for the calculation
            calculation_type: Optional calculation type suffix (e.g., "Fee", "Dates")

        Returns:
            The calculation result data
        """
        # Build the calculation endpoint URL
        if calculation_type:
            url = self._build_url(f"calculate{calculation_type}")
        else:
            url = self._build_url("calculate")

        self._logger.debug(f"Performing calculation via {url}")
        return self._client.post(url, json_data=calculation_data)


class PropertiesResource(BaseResource):
    """Base class for read-only properties and configuration resources."""

    def __init__(self, client: "NeonClient", endpoint: str = "/properties") -> None:
        """Initialize the properties resource.

        Args:
            client: The Neon client instance
            endpoint: The base endpoint for properties (default: "/properties")
        """
        super().__init__(client, endpoint)

    def get_property(self, property_name: str) -> Dict[str, Any]:
        """Get a specific property by name.

        Args:
            property_name: The property name (e.g., "countries", "genders")

        Returns:
            The property data
        """
        url = self._build_url(property_name)
        self._logger.debug(f"Fetching property: {property_name}")
        return self._client.get(url)

    def get_activity_statuses(self) -> Dict[str, Any]:
        """Get available activity statuses."""
        return self.get_property("activityStatuses")

    def get_address_types(self) -> Dict[str, Any]:
        """Get available address types."""
        return self.get_property("addressTypes")

    def get_company_types(self) -> Dict[str, Any]:
        """Get available company types."""
        return self.get_property("companyTypes")

    def get_countries(self) -> Dict[str, Any]:
        """Get available countries."""
        return self.get_property("countries")

    def get_current_system_user(self) -> Dict[str, Any]:
        """Get current system user information."""
        return self.get_property("currentSystemUser")

    def get_event_categories(self) -> Dict[str, Any]:
        """Get available event categories."""
        return self.get_property("eventCategories")

    def get_event_topics(self) -> Dict[str, Any]:
        """Get available event topics."""
        return self.get_property("eventTopics")

    def get_funds(self) -> Dict[str, Any]:
        """Get available funds."""
        return self.get_property("funds")

    def get_genders(self) -> Dict[str, Any]:
        """Get available genders."""
        return self.get_property("genders")

    def get_individual_types(self) -> Dict[str, Any]:
        """Get available individual types."""
        return self.get_property("individualTypes")

    def get_organization_profile(self) -> Dict[str, Any]:
        """Get organization profile information."""
        return self.get_property("organizationProfile")

    def get_prefixes(self) -> Dict[str, Any]:
        """Get available name prefixes."""
        return self.get_property("prefixes")

    def get_purposes(self) -> Dict[str, Any]:
        """Get available purposes."""
        return self.get_property("purposes")

    def get_relation_types(self) -> Dict[str, Any]:
        """Get available relation types."""
        return self.get_property("relationTypes")

    def get_solicitation_methods(self) -> Dict[str, Any]:
        """Get available solicitation methods."""
        return self.get_property("solicitationMethods")

    def get_sources(self) -> Dict[str, Any]:
        """Get available sources."""
        return self.get_property("sources")

    def get_state_provinces(self) -> Dict[str, Any]:
        """Get available states and provinces."""
        return self.get_property("stateProvinces")

    def get_system_timezones(self) -> Dict[str, Any]:
        """Get available system timezones."""
        return self.get_property("systemTimezones")

    def get_system_users(self) -> Dict[str, Any]:
        """Get available system users."""
        return self.get_property("systemUsers")


class NestedResource(BaseResource):
    """Base class for resources that are nested under other resources.

    This is similar to RelationshipResource but more general-purpose
    for any nested resource pattern like /parent/{parentId}/child/{childId}.
    """

    def __init__(
        self,
        client: "NeonClient",
        parent_endpoint: str,
        parent_id: int,
        child_resource: str,
        child_id: Optional[int] = None,
    ) -> None:
        """Initialize the nested resource.

        Args:
            client: The Neon client instance
            parent_endpoint: The parent resource endpoint
            parent_id: The ID of the parent resource
            child_resource: The child resource name
            child_id: Optional child resource ID for specific resource operations
        """
        self._parent_endpoint = parent_endpoint.rstrip("/")
        self.parent_id = parent_id
        self.child_resource = child_resource
        self.child_id = child_id

        # Build the nested endpoint
        if child_id is not None:
            endpoint = (
                f"{self._parent_endpoint}/{parent_id}/{child_resource}/{child_id}"
            )
        else:
            endpoint = f"{self._parent_endpoint}/{parent_id}/{child_resource}"

        super().__init__(client, endpoint)

    def list(self, **kwargs: Any) -> Iterator[Dict[str, Any]]:
        """List nested resources.

        Args:
            **kwargs: Additional query parameters

        Yields:
            Individual nested resource dictionaries
        """
        if self.child_id is not None:
            raise ValueError(
                "Cannot list when child_id is specified. Use get() instead."
            )

        # For nested resources, we may need to handle different response structures
        response = self._client.get(self._endpoint, params=kwargs)

        # Handle different response structures
        if isinstance(response, list):
            yield from response
        elif self.child_resource in response:
            yield from response[self.child_resource]
        else:
            # Single item response
            yield response

    def get_child(self, child_id: int) -> Dict[str, Any]:
        """Get a specific child resource.

        Args:
            child_id: The child resource ID

        Returns:
            The child resource data
        """
        url = (
            f"{self._parent_endpoint}/{self.parent_id}/{self.child_resource}/{child_id}"
        )
        return self._client.get(url)

    def create_child(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new child resource.

        Args:
            data: The child resource data

        Returns:
            The created child resource data
        """
        url = f"{self._parent_endpoint}/{self.parent_id}/{self.child_resource}"
        return self._client.post(url, json_data=data)

    def update_child(self, child_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update a child resource.

        Args:
            child_id: The child resource ID
            data: The updated resource data

        Returns:
            The updated resource data
        """
        url = (
            f"{self._parent_endpoint}/{self.parent_id}/{self.child_resource}/{child_id}"
        )
        return self._client.put(url, json_data=data)

    def patch_child(self, child_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """Partially update a child resource.

        Args:
            child_id: The child resource ID
            data: The partial resource data

        Returns:
            The updated resource data
        """
        url = (
            f"{self._parent_endpoint}/{self.parent_id}/{self.child_resource}/{child_id}"
        )
        return self._client.patch(url, json_data=data)

    def delete_child(self, child_id: int) -> Dict[str, Any]:
        """Delete a child resource.

        Args:
            child_id: The child resource ID

        Returns:
            The deletion response
        """
        url = (
            f"{self._parent_endpoint}/{self.parent_id}/{self.child_resource}/{child_id}"
        )
        return self._client.delete(url)
