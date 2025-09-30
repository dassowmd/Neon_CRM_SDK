"""Custom Fields resource for the Neon CRM SDK."""

from typing import TYPE_CHECKING, Any, Dict, Iterator, List, Optional, Tuple, Union

from ..fuzzy_search import FieldFuzzySearch
from ..types import CustomFieldCategory
from .base import ListableResource


class FieldNotFoundError(Exception):
    """Exception raised when a field is not found, with helpful suggestions."""

    def __init__(
        self,
        field_name: str,
        category: str = None,
        fuzzy_suggestions: List[str] = None,
        semantic_suggestions: List[str] = None,
    ):
        """Initialize the field not found error with suggestions.

        Args:
            field_name: The field name that was not found
            category: The category being searched (if applicable)
            fuzzy_suggestions: List of similar field names (typos, etc.)
            semantic_suggestions: List of semantically related field names
        """
        self.field_name = field_name
        self.category = category
        self.fuzzy_suggestions = fuzzy_suggestions or []
        self.semantic_suggestions = semantic_suggestions or []

        # Build helpful error message
        category_text = f" in category '{category}'" if category else ""
        message = f"Field '{field_name}' not found{category_text}."

        if self.fuzzy_suggestions:
            message += "\n\nDid you mean one of these similar field names?\n"
            for suggestion in self.fuzzy_suggestions[:5]:
                message += f"  - {suggestion}\n"

        if self.semantic_suggestions:
            message += "\nOr perhaps you're looking for one of these related fields?\n"
            for suggestion in self.semantic_suggestions[:5]:
                message += f"  - {suggestion}\n"

        if not self.fuzzy_suggestions and not self.semantic_suggestions:
            message += " No similar fields found."

        super().__init__(message)


from ..governance import ResourceType
from .base import BaseResource

if TYPE_CHECKING:
    from ..client import NeonClient


class CustomFieldsResource(ListableResource):
    """Resource for managing custom fields."""

    _resource_type = ResourceType.CUSTOM_FIELDS

    def __init__(self, client: "NeonClient") -> None:
        """Initialize the custom fields resource."""
        super().__init__(client, "/customFields")

    def list(
        self,
        current_page: int = 0,
        page_size: int = 50,
        limit: Optional[int] = None,
        field_type: Optional[str] = None,
        category: Optional[Union[CustomFieldCategory, str]] = None,
        **kwargs: Any,
    ) -> Iterator[Dict[str, Any]]:
        """List custom fields with optional filtering.

        Args:
            current_page: Page number to start from (0-indexed)
            page_size: Number of items per page
            limit: Maximum number of items to return
            field_type: Filter by field type (text, number, date, etc.)
            category: Filter by category (Account, Donation, Event, etc.)
            **kwargs: Additional query parameters

        Yields:
            Individual custom field dictionaries
        """
        params = {}
        if field_type is not None:
            params["fieldType"] = field_type
        if category is not None:
            params["category"] = (
                category.value
                if isinstance(category, CustomFieldCategory)
                else category
            )

        params.update(kwargs)

        return super().list(
            current_page=current_page, page_size=page_size, limit=limit, **params
        )

    def get_by_category(
        self, category: Union[CustomFieldCategory, str]
    ) -> Iterator[Dict[str, Any]]:
        """Get custom fields for a specific category.

        Args:
            category: The category (Account, Donation, Event, etc.)

        Yields:
            Custom field definitions for the category
        """
        return self.list(category=category)

    def find_by_name_and_category(
        self, field_name: str, category: Union[CustomFieldCategory, str]
    ) -> Optional[Dict[str, Any]]:
        """Find a custom field by name within a specific category.

        Args:
            field_name: The name of the custom field to find
            category: The category to search within

        Returns:
            The custom field data if found, None otherwise
        """
        category_str = (
            category.value if isinstance(category, CustomFieldCategory) else category
        )
        self._logger.debug(
            f"Finding custom field '{field_name}' in category '{category_str}'"
        )

        # Use caching if available
        if self._client._cache:
            cache_key = self._client._cache.create_cache_key(
                "custom_field", category_str, field_name
            )

            def _fetch_field():
                self._logger.debug(
                    f"Cache miss: fetching custom field '{field_name}' from API"
                )
                for field in self.get_by_category(category):
                    if field.get("name") == field_name:
                        self._logger.debug(
                            f"Found custom field '{field_name}' with ID {field.get('id')}"
                        )
                        return field
                self._logger.debug(
                    f"Custom field '{field_name}' not found in category '{category_str}'"
                )
                return None

            result = self._client._cache.custom_fields.cache_get_or_set(
                cache_key, _fetch_field
            )
        else:
            # Fallback to non-cached version
            self._logger.debug("Cache not available, using direct API lookup")
            result = None
            for field in self.get_by_category(category):
                if field.get("name") == field_name:
                    self._logger.debug(
                        f"Found custom field '{field_name}' with ID {field.get('id')}"
                    )
                    result = field
                    break

            if result is None:
                self._logger.debug(
                    f"Custom field '{field_name}' not found in category '{category_str}'"
                )

        # If field not found, log helpful suggestions at INFO level
        if result is None:
            self._log_field_suggestions(field_name, category_str)

        return result

    def _log_field_suggestions(self, field_name: str, category_str: str) -> None:
        """Log helpful field suggestions when a field is not found."""
        try:
            # Get all available fields in this category for suggestions
            available_fields = list(self.get_by_category(category_str))
            field_names = [
                field.get("name", "") for field in available_fields if field.get("name")
            ]

            if not field_names:
                return

            # Generate fuzzy suggestions (typos, similar names)
            fuzzy_search = FieldFuzzySearch(case_sensitive=False)
            fuzzy_suggestions = fuzzy_search.suggest_corrections(
                field_name, field_names, threshold=0.3, max_suggestions=3
            )

            # Generate semantic suggestions (related meaning)
            semantic_matches = (
                fuzzy_search.semantic_matcher.find_semantically_similar_fields(
                    field_name, field_names, threshold=0.1, max_results=3
                )
            )
            semantic_suggestions = [match[0] for match in semantic_matches]

            # Remove duplicates between fuzzy and semantic suggestions
            semantic_suggestions = [
                s for s in semantic_suggestions if s not in fuzzy_suggestions
            ]

            # Log suggestions at INFO level
            if fuzzy_suggestions or semantic_suggestions:
                suggestion_msg = f"Custom field '{field_name}' not found in category '{category_str}'."

                if fuzzy_suggestions:
                    suggestion_msg += f" Did you mean: {', '.join(fuzzy_suggestions)}?"

                if semantic_suggestions:
                    if fuzzy_suggestions:
                        suggestion_msg += f" Or perhaps you were looking for: {', '.join(semantic_suggestions)}?"
                    else:
                        suggestion_msg += f" Maybe you were looking for: {', '.join(semantic_suggestions)}?"

                self._logger.info(suggestion_msg)

        except Exception as e:
            # Don't let suggestion generation break the main functionality
            self._logger.debug(f"Failed to generate field suggestions: {e}")

    def get_field_options(self, field_id: int) -> List[Dict[str, Any]]:
        """Get options for a dropdown/select custom field.

        Args:
            field_id: The custom field ID

        Returns:
            List of field options if applicable
        """
        field = self.get(field_id)
        return field.get("options", [])

    def list_groups(
        self,
        current_page: int = 0,
        page_size: int = 50,
        limit: Optional[int] = None,
        category: Optional[Union[CustomFieldCategory, str]] = None,
        **kwargs: Any,
    ) -> Iterator[Dict[str, Any]]:
        """List custom field groups.

        Args:
            current_page: Page number to start from (0-indexed)
            page_size: Number of items per page
            limit: Maximum number of items to return
            category: Filter by category (Account, Donation, Event, etc.) - maps to 'component' API parameter
            **kwargs: Additional query parameters

        Yields:
            Individual custom field group dictionaries
        """
        params = {
            "currentPage": current_page,
            "pageSize": page_size,
        }

        # Map category to component parameter (API design inconsistency)
        if category is not None:
            params["component"] = (
                category.value
                if isinstance(category, CustomFieldCategory)
                else category
            )

        params.update(kwargs)

        results_returned = 0
        while True:
            response = self._client.get("/customFields/groups", params=params)

            # Handle different response structures
            if "groups" in response:
                items = response["groups"]
                pagination = response.get("pagination", {})
            elif isinstance(response, list):
                # Direct list response
                items = response
                pagination = {}
            else:
                # Try the standard endpoint name pattern
                items = response.get("customFields", [])
                pagination = response.get("pagination", {})

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

    def get_group(self, group_id: int) -> Dict[str, Any]:
        """Get a specific custom field group by ID.

        Args:
            group_id: The custom field group ID

        Returns:
            The custom field group data
        """
        return self._client.get(f"/customFields/groups/{group_id}")

    def get_groups_by_category(
        self, category: Union[CustomFieldCategory, str]
    ) -> Iterator[Dict[str, Any]]:
        """Get custom field groups for a specific category.

        Args:
            category: The category (Account, Donation, Event, etc.)

        Yields:
            Custom field group definitions for the category
        """
        return self.list_groups(category=category)

    def find_group_by_name(self, group_name: str) -> Optional[Dict[str, Any]]:
        """Find a custom field group by name.

        Args:
            group_name: The name of the custom field group to find

        Returns:
            The custom field group data if found, None otherwise
        """
        for group in self.list_groups():
            if group.get("name") == group_name:
                return group
        return None

    def find_group_by_name_and_category(
        self, group_name: str, category: Union[CustomFieldCategory, str]
    ) -> Optional[Dict[str, Any]]:
        """Find a custom field group by name within a specific category.

        Args:
            group_name: The name of the custom field group to find
            category: The category to search within

        Returns:
            The custom field group data if found, None otherwise
        """
        # Use caching if available
        if self._client._cache:
            category_str = (
                category.value
                if isinstance(category, CustomFieldCategory)
                else category
            )
            cache_key = self._client._cache.create_cache_key(
                "custom_field_group", category_str, group_name
            )

            def _fetch_group():
                for group in self.get_groups_by_category(category):
                    if group.get("name") == group_name:
                        return group
                return None

            return self._client._cache.custom_field_groups.cache_get_or_set(
                cache_key, _fetch_group
            )

        # Fallback to non-cached version
        for group in self.get_groups_by_category(category):
            if group.get("name") == group_name:
                return group
        return None

    def list_all_categories(
        self,
        current_page: int = 0,
        page_size: int = 50,
        limit: Optional[int] = None,
        **kwargs: Any,
    ) -> Iterator[Dict[str, Any]]:
        """Iterate through custom fields from all categories.

        Args:
            current_page: Page number to start from (0-indexed)
            page_size: Number of items per page
            limit: Maximum number of items to return across all categories
            **kwargs: Additional query parameters

        Yields:
            Individual custom field dictionaries from all categories
        """
        results_returned = 0

        for category in CustomFieldCategory:
            if limit is not None and results_returned >= limit:
                break

            try:
                remaining_limit = (
                    limit - results_returned if limit is not None else None
                )
                for field in self.list(
                    current_page=current_page,
                    page_size=page_size,
                    limit=remaining_limit,
                    category=category,
                    **kwargs,
                ):
                    yield field
                    results_returned += 1
                    if limit is not None and results_returned >= limit:
                        break
            except Exception:
                # Skip categories that might not exist or have issues
                continue

    def fuzzy_search_by_name(
        self,
        query: str,
        category: Optional[Union[CustomFieldCategory, str]] = None,
        threshold: float = 0.3,
        max_results: int = 10,
        case_sensitive: bool = False,
    ) -> List[Tuple[Dict[str, Any], float]]:
        """Search custom fields by name using fuzzy matching.

        Args:
            query: The search query for field names
            category: Optional category to limit search scope
            threshold: Minimum similarity score (0.0-1.0) to include in results
            max_results: Maximum number of results to return
            case_sensitive: Whether to perform case-sensitive matching

        Returns:
            List of (field_dict, similarity_score) tuples sorted by score

        Example:
            # Search for fields similar to "volunteer"
            results = client.custom_fields.fuzzy_search_by_name("volunteer")
            for field, score in results:
                print(f"{field['name']} (ID: {field['id']}) - Score: {score:.2f}")

            # Search within specific category
            results = client.custom_fields.fuzzy_search_by_name(
                "email", category="Account", threshold=0.5
            )
        """
        if not query:
            return []

        self._logger.debug(
            f"Fuzzy searching custom fields for '{query}' with threshold {threshold}"
        )

        # Get fields to search through
        if category is not None:
            fields = list(self.get_by_category(category))
            self._logger.debug(
                f"Searching {len(fields)} fields in category '{category}'"
            )
        else:
            fields = list(self.list_all_categories())
            self._logger.debug(f"Searching {len(fields)} fields across all categories")

        # Perform fuzzy search
        fuzzy_search = FieldFuzzySearch(case_sensitive=case_sensitive)
        results = fuzzy_search.search_custom_fields(
            query, fields, threshold, max_results
        )

        self._logger.debug(f"Found {len(results)} fuzzy matches for '{query}'")
        return results

    def semantic_search_by_name(
        self,
        query: str,
        category: Optional[Union[CustomFieldCategory, str]] = None,
        threshold: float = 0.1,
        max_results: int = 10,
    ) -> List[Tuple[Dict[str, Any], float]]:
        """Search custom fields using semantic similarity.

        Args:
            query: The search query for field names
            category: Optional category to limit search scope
            threshold: Minimum semantic similarity score (0.0-1.0)
            max_results: Maximum number of results to return

        Returns:
            List of (field_dict, similarity_score) tuples sorted by score

        Example:
            # Search for fields with similar meaning to "address"
            results = client.custom_fields.semantic_search_by_name("address")
            for field, score in results:
                print(f"{field['name']} (ID: {field['id']}) - Score: {score:.2f}")
        """
        if not query:
            return []

        self._logger.debug(
            f"Semantic searching custom fields for '{query}' with threshold {threshold}"
        )

        # Get fields to search through
        if category is not None:
            fields = list(self.get_by_category(category))
            self._logger.debug(
                f"Searching {len(fields)} fields in category '{category}'"
            )
        else:
            fields = list(self.list_all_categories())
            self._logger.debug(f"Searching {len(fields)} fields across all categories")

        # Perform semantic search
        fuzzy_search = FieldFuzzySearch(case_sensitive=False)
        results = fuzzy_search.search_custom_fields_semantic(
            query, fields, threshold, max_results
        )

        self._logger.debug(f"Found {len(results)} semantic matches for '{query}'")
        return results

    def suggest_field_names(
        self,
        invalid_name: str,
        category: Optional[Union[CustomFieldCategory, str]] = None,
        max_suggestions: int = 5,
    ) -> List[str]:
        """Suggest valid custom field names for an invalid field name.

        Args:
            invalid_name: The invalid or misspelled field name
            category: Optional category to limit suggestions
            max_suggestions: Maximum number of suggestions to return

        Returns:
            List of suggested field names sorted by relevance

        Example:
            # Get suggestions for a misspelled field name
            suggestions = client.custom_fields.suggest_field_names("volunter")
            print(f"Did you mean: {', '.join(suggestions)}")
        """
        if not invalid_name:
            return []

        self._logger.debug(f"Suggesting field names for '{invalid_name}'")

        # Get available field names
        if category is not None:
            fields = list(self.get_by_category(category))
        else:
            fields = list(self.list_all_categories())

        field_names = [field.get("name", "") for field in fields if field.get("name")]

        # Use fuzzy search to find suggestions
        fuzzy_search = FieldFuzzySearch(case_sensitive=False)
        suggestions = fuzzy_search.suggest_corrections(
            invalid_name, field_names, threshold=0.4, max_suggestions=max_suggestions
        )

        self._logger.debug(
            f"Generated {len(suggestions)} suggestions for '{invalid_name}'"
        )
        return suggestions
