"""Search request validation for the Neon CRM SDK."""

import json
import os
import re
from typing import TYPE_CHECKING, Any, Dict, List, Union

from .logging import NeonLogger
from .types import SearchField, SearchOperator, SearchRequest

if TYPE_CHECKING:
    from .client import NeonClient


class SearchRequestValidator:
    """Validator for search requests."""

    # Class-level cache for field definitions loaded from JSON
    _field_definitions = None

    @classmethod
    def _load_field_definitions(cls) -> Dict[str, Any]:
        """Load field definitions from JSON file."""
        if cls._field_definitions is None:
            try:
                # Get path to JSON file relative to this module
                current_dir = os.path.dirname(__file__)
                json_path = os.path.join(current_dir, "field_definitions.json")

                with open(json_path) as f:
                    cls._field_definitions = json.load(f)
            except Exception:
                # Fallback to empty definitions if file loading fails
                cls._field_definitions = {
                    "valid_search_fields": {},
                    "valid_output_fields": {},
                    "field_types": {},
                }

        return cls._field_definitions

    @property
    def VALID_SEARCH_FIELDS(self) -> Dict[str, set]:
        """Get valid search fields, converting from JSON lists to sets."""
        definitions = self._load_field_definitions()
        return {
            resource: set(fields)
            for resource, fields in definitions.get("valid_search_fields", {}).items()
        }

    @property
    def VALID_OUTPUT_FIELDS(self) -> Dict[str, set]:
        """Get valid output fields, converting from JSON lists to sets."""
        definitions = self._load_field_definitions()
        return {
            resource: set(fields)
            for resource, fields in definitions.get("valid_output_fields", {}).items()
        }

    @property
    def FIELD_TYPES(self) -> Dict[str, str]:
        """Get field type mappings from JSON."""
        definitions = self._load_field_definitions()
        return definitions.get("field_types", {})

    # Define which operators are valid for different field types
    FIELD_TYPE_OPERATORS = {
        "string": {
            SearchOperator.EQUAL,
            SearchOperator.NOT_EQUAL,
            SearchOperator.BLANK,
            SearchOperator.NOT_BLANK,
            SearchOperator.CONTAIN,
            SearchOperator.NOT_CONTAIN,
        },
        "number": {
            SearchOperator.EQUAL,
            SearchOperator.NOT_EQUAL,
            SearchOperator.BLANK,
            SearchOperator.NOT_BLANK,
            SearchOperator.LESS_THAN,
            SearchOperator.GREATER_THAN,
            SearchOperator.LESS_AND_EQUAL,
            SearchOperator.GREATER_AND_EQUAL,
            SearchOperator.IN_RANGE,
            SearchOperator.NOT_IN_RANGE,
        },
        "date": {
            SearchOperator.EQUAL,
            SearchOperator.NOT_EQUAL,
            SearchOperator.BLANK,
            SearchOperator.NOT_BLANK,
            SearchOperator.LESS_THAN,
            SearchOperator.GREATER_THAN,
            SearchOperator.LESS_AND_EQUAL,
            SearchOperator.GREATER_AND_EQUAL,
            SearchOperator.IN_RANGE,
            SearchOperator.NOT_IN_RANGE,
        },
        "boolean": {
            SearchOperator.EQUAL,
            SearchOperator.NOT_EQUAL,
        },
        "enum": {
            SearchOperator.EQUAL,
            SearchOperator.NOT_EQUAL,
            SearchOperator.BLANK,
            SearchOperator.NOT_BLANK,
        },
    }

    def __init__(self, resource_name: str, client: "NeonClient" = None):
        """Initialize validator for a specific resource.

        Args:
            resource_name: Name of the resource (accounts, donations, etc.)
            client: Optional Neon client for dynamic field validation
        """
        self.resource_name = resource_name.lower()
        self.client = client
        self._custom_field_id_pattern = re.compile(r"^\d+$")
        self._cached_search_fields = None
        self._cached_output_fields = None
        self._logger = NeonLogger.get_logger(f"validation.{self.resource_name}")

    def validate_search_request(self, search_request: SearchRequest) -> List[str]:
        """Validate a complete search request.

        Args:
            search_request: The search request to validate

        Returns:
            List of validation error messages (empty if valid)
        """
        self._logger.debug(
            f"Validating search request: fields={len(search_request.get('searchFields', []))}, outputs={len(search_request.get('outputFields', []))}"
        )

        errors = []

        # Validate search fields
        if "searchFields" in search_request:
            for field in search_request["searchFields"]:
                field_errors = self.validate_search_field(field)
                errors.extend(field_errors)

        # Validate output fields
        if "outputFields" in search_request:
            output_errors = self.validate_output_fields(search_request["outputFields"])
            errors.extend(output_errors)

        # Validate pagination
        if "pagination" in search_request:
            pagination_errors = self.validate_pagination(search_request["pagination"])
            errors.extend(pagination_errors)

        if errors:
            self._logger.warning(
                f"Search request validation failed with {len(errors)} errors: {'; '.join(errors)}"
            )
        else:
            self._logger.debug("Search request validation passed")

        return errors

    def validate_search_field(self, search_field: SearchField) -> List[str]:
        """Validate a single search field.

        Args:
            search_field: The search field to validate

        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []

        field_name = search_field.get("field")
        operator = search_field.get("operator")
        value = search_field.get("value")

        # Check if field name is provided
        if not field_name:
            errors.append("Search field 'field' is required")
            return errors

        # Check if field is valid for this resource
        if not self._is_valid_search_field(field_name):
            valid_fields = self._get_available_search_fields()
            self._log_field_suggestions(field_name, valid_fields, "search")
            errors.append(
                f"Field '{field_name}' is not valid for resource '{self.resource_name}'. Valid fields: {sorted(valid_fields)}"
            )

        # Check if operator is provided
        if not operator:
            errors.append("Search field 'operator' is required")
            return errors

        # Validate operator
        operator_errors = self.validate_operator(field_name, operator)
        errors.extend(operator_errors)

        # Validate value based on operator
        value_errors = self.validate_field_value(field_name, operator, value)
        errors.extend(value_errors)

        return errors

    def validate_operator(
        self, field_name: str, operator: Union[SearchOperator, str]
    ) -> List[str]:
        """Validate that an operator is appropriate for a field.

        Args:
            field_name: Name of the field
            operator: The operator to validate

        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []

        # Convert string to enum if needed
        if isinstance(operator, str):
            try:
                operator = SearchOperator(operator)
            except ValueError:
                valid_ops = [op.value for op in SearchOperator]
                errors.append(
                    f"Invalid operator '{operator}'. Valid operators: {valid_ops}"
                )
                return errors

        # First try to get actual valid operators from API
        valid_operators_from_api = self._get_field_operators_from_api(field_name)
        if valid_operators_from_api:
            if operator.value not in valid_operators_from_api:
                errors.append(
                    f"Operator '{operator.value}' is not valid for field '{field_name}'. Valid operators: {valid_operators_from_api}"
                )
            return errors

        # Fallback to static field type validation if API info not available
        field_type = self._get_field_type(field_name)
        valid_operators = self.FIELD_TYPE_OPERATORS.get(field_type, set())
        if operator not in valid_operators:
            valid_ops = [op.value for op in valid_operators]
            errors.append(
                f"Operator '{operator.value}' is not valid for field '{field_name}' (type: {field_type}). Valid operators: {valid_ops}"
            )

        return errors

    def validate_field_value(
        self, field_name: str, operator: Union[SearchOperator, str], value: Any
    ) -> List[str]:
        """Validate that a value is appropriate for a field and operator.

        Args:
            field_name: Name of the field
            operator: The operator being used
            value: The value to validate

        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []

        # Convert string to enum if needed
        if isinstance(operator, str):
            try:
                operator = SearchOperator(operator)
            except ValueError:
                return []  # Operator validation will catch this

        # BLANK and NOT_BLANK operators don't need values
        if operator in {SearchOperator.BLANK, SearchOperator.NOT_BLANK}:
            if value is not None:
                errors.append(f"Operator '{operator.value}' should not have a value")
            return errors

        # All other operators need values
        if value is None:
            errors.append(f"Operator '{operator.value}' requires a value")
            return errors

        # Range operators need array values
        if operator in {SearchOperator.IN_RANGE, SearchOperator.NOT_IN_RANGE}:
            if not isinstance(value, list) or len(value) != 2:
                errors.append(
                    f"Operator '{operator.value}' requires an array of exactly 2 values [min, max]"
                )
                return errors

        # Get field type and validate value type
        field_type = self._get_field_type(field_name)
        type_errors = self.validate_value_type(field_name, field_type, value)
        errors.extend(type_errors)

        return errors

    def validate_value_type(
        self, field_name: str, field_type: str, value: Any
    ) -> List[str]:
        """Validate that a value matches the expected type for a field.

        Args:
            field_name: Name of the field
            field_type: Type of the field (string, number, date, boolean, enum)
            value: The value to validate

        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []

        if field_type == "number":
            if isinstance(value, list):
                # For range operators
                for v in value:
                    if not isinstance(v, (int, float)):
                        errors.append(
                            f"Field '{field_name}' expects numeric values, got {type(v).__name__}"
                        )
            elif not isinstance(value, (int, float)):
                errors.append(
                    f"Field '{field_name}' expects a numeric value, got {type(value).__name__}"
                )

        elif field_type == "boolean":
            if isinstance(value, list):
                for v in value:
                    if not isinstance(v, bool):
                        errors.append(
                            f"Field '{field_name}' expects boolean values, got {type(v).__name__}"
                        )
            elif not isinstance(value, bool):
                errors.append(
                    f"Field '{field_name}' expects a boolean value, got {type(value).__name__}"
                )

        elif field_type == "date":
            if isinstance(value, list):
                # For range operators
                for v in value:
                    if not isinstance(v, str):
                        errors.append(
                            f"Field '{field_name}' expects date string values (YYYY-MM-DD), got {type(v).__name__}"
                        )
                    elif not self._is_valid_date_string(v):
                        errors.append(
                            f"Field '{field_name}' expects date in YYYY-MM-DD format, got '{v}'"
                        )
            elif not isinstance(value, str):
                errors.append(
                    f"Field '{field_name}' expects a date string (YYYY-MM-DD), got {type(value).__name__}"
                )
            elif not self._is_valid_date_string(value):
                errors.append(
                    f"Field '{field_name}' expects date in YYYY-MM-DD format, got '{value}'"
                )

        # For string and enum types, we're more lenient and accept any value that can be converted to string

        return errors

    def _is_valid_date_string(self, date_str: str) -> bool:
        """Check if a string is a valid date in YYYY-MM-DD format.

        Args:
            date_str: The date string to validate

        Returns:
            True if valid, False otherwise
        """
        if not isinstance(date_str, str):
            return False

        parts = date_str.split("-")
        if len(parts) != 3:
            return False

        try:
            year, month, day = map(int, parts)
            # Basic validation
            if year < 1900 or year > 9999:
                return False
            if month < 1 or month > 12:
                return False
            if day < 1 or day > 31:
                return False
            return True
        except ValueError:
            return False

    def validate_output_fields(self, output_fields: List[str]) -> List[str]:
        """Validate output fields for this resource.

        Args:
            output_fields: List of output field names

        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []

        if not output_fields:
            errors.append("At least one output field is required")
            return errors

        for field_name in output_fields:
            if not self._is_valid_output_field(field_name):
                valid_fields = self._get_available_output_fields()
                self._log_field_suggestions(field_name, valid_fields, "output")
                errors.append(
                    f"Output field '{field_name}' is not valid for resource '{self.resource_name}'. Valid fields: {sorted(valid_fields)}"
                )

        return errors

    def validate_pagination(self, pagination: Dict[str, Any]) -> List[str]:
        """Validate pagination parameters.

        Args:
            pagination: Pagination parameters

        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []

        current_page = pagination.get("currentPage")
        page_size = pagination.get("pageSize")

        if current_page is not None:
            if not isinstance(current_page, int) or current_page < 0:
                errors.append("currentPage must be a non-negative integer")

        if page_size is not None:
            if not isinstance(page_size, int) or page_size < 1 or page_size > 500:
                errors.append("pageSize must be an integer between 1 and 500")

        return errors

    def _is_custom_field(self, field_name: Union[str, int]) -> bool:
        """Check if a field name is a custom field pattern.

        Args:
            field_name: The field name to check (string or integer)

        Returns:
            True if it's a custom field (integer ID or string digits)
        """
        # Accept integers directly as custom field IDs
        if isinstance(field_name, int):
            return True

        # Accept string representations of integers ("123")
        field_str = str(field_name)
        return bool(self._custom_field_id_pattern.match(field_str))

    def _is_valid_search_field(self, field_name: Union[str, int]) -> bool:
        """Check if a field is valid for search in this resource.

        Args:
            field_name: The field name to validate (string or integer)

        Returns:
            True if the field is valid for search
        """
        # Custom fields are always valid for search (support both string ID and customField patterns)
        if self._is_custom_field(field_name):
            return True

        # Convert to string for standard field checks
        field_str = str(field_name)

        # Step 1: Check exact match in static fields from JSON definitions
        valid_fields = self.VALID_SEARCH_FIELDS.get(self.resource_name, set())
        if field_str in valid_fields:
            return True

        # Step 2: Check exact match in dynamic fields from API
        if self.client:
            try:
                available_fields = self._get_dynamic_search_fields()
                if field_str in available_fields:
                    return True
            except (Exception, NotImplementedError):
                # Fall back to static validation if API doesn't support field discovery
                pass

        # Step 3: Only now try fuzzy/semantic matching as a last resort
        return self._try_fuzzy_field_match(field_str, "search")

    def _is_valid_output_field(self, field_name: Union[str, int]) -> bool:
        """Check if a field is valid for output in this resource.

        Args:
            field_name: The field name to validate (string or integer)

        Returns:
            True if the field is valid for output
        """
        # Custom fields are always valid for output (support both integer ID and display names)
        if self._is_custom_field(field_name):
            return True

        # Convert to string for standard field checks
        field_str = str(field_name)

        # Step 1: Check exact match in static fields from JSON definitions
        valid_fields = self.VALID_OUTPUT_FIELDS.get(self.resource_name, set())
        if field_str in valid_fields:
            return True

        # Step 2: Check exact match in dynamic fields from API
        if self.client:
            try:
                available_fields = self._get_dynamic_output_fields()
                if field_str in available_fields:
                    return True
            except (Exception, NotImplementedError):
                # Fall back to static validation if API doesn't support field discovery
                pass

        # Step 3: Only now try fuzzy/semantic matching as a last resort
        return self._try_fuzzy_field_match(field_str, "output")

    def _try_fuzzy_field_match(self, field_name: str, field_type: str) -> bool:
        """Try fuzzy/semantic matching as a fallback when exact matches fail.

        Args:
            field_name: The field name to match
            field_type: Type of field ('search' or 'output')

        Returns:
            True if a fuzzy/semantic match is found
        """
        try:
            from .fuzzy_search import FieldFuzzySearch

            # Get the appropriate field list for this field type
            if field_type == "search":
                available_fields = self._get_available_search_fields()
            else:  # output
                available_fields = self._get_available_output_fields()

            if not available_fields:
                return False

            # Try fuzzy matching first (typos, abbreviations)
            fuzzy_search = FieldFuzzySearch(case_sensitive=False)
            fuzzy_suggestions = fuzzy_search.suggest_corrections(
                field_name, available_fields, threshold=0.7, max_suggestions=1
            )

            if fuzzy_suggestions:
                self._logger.debug(
                    f"Found fuzzy match for '{field_name}': {fuzzy_suggestions[0]}"
                )
                return True

            # Try semantic matching (similar meaning)
            semantic_matches = (
                fuzzy_search.semantic_matcher.find_semantically_similar_fields(
                    field_name, available_fields, threshold=0.3, max_results=1
                )
            )

            if semantic_matches:
                self._logger.debug(
                    f"Found semantic match for '{field_name}': {semantic_matches[0][0]}"
                )
                return True

            return False

        except Exception as e:
            # Don't let fuzzy matching break the main functionality
            self._logger.debug(
                f"Fuzzy/semantic matching failed for '{field_name}': {e}"
            )
            return False

    def _get_available_search_fields(self) -> List[str]:
        """Get all available search fields for this resource.

        Returns:
            List of available search field names (standard fields only, no custom fields)
        """
        # Start with JSON-defined standard fields
        static_fields = list(self.VALID_SEARCH_FIELDS.get(self.resource_name, set()))

        if self.client:
            try:
                # Get dynamic fields but only include standard fields, not custom fields
                dynamic_standard_fields = self._get_dynamic_standard_search_fields()
                # Combine static and dynamic, removing duplicates
                all_fields = list(set(static_fields) | set(dynamic_standard_fields))
                return sorted(all_fields)
            except Exception:
                pass

        return sorted(static_fields)

    def _get_available_output_fields(self) -> List[str]:
        """Get all available output fields for this resource.

        Returns:
            List of available output field names (standard fields only, no custom fields)
        """
        # Start with JSON-defined standard fields
        static_fields = list(self.VALID_OUTPUT_FIELDS.get(self.resource_name, set()))

        if self.client:
            try:
                # Get dynamic fields but only include standard fields, not custom fields
                dynamic_standard_fields = self._get_dynamic_standard_output_fields()
                # Combine static and dynamic, removing duplicates
                all_fields = list(set(static_fields) | set(dynamic_standard_fields))
                return sorted(all_fields)
            except Exception:
                pass

        return sorted(static_fields)

    def _get_dynamic_standard_search_fields(self) -> List[str]:
        """Get only standard search fields from the API (excludes custom fields).

        Returns:
            List of standard search field names from the API
        """
        try:
            dynamic_fields = self._get_dynamic_search_fields()
            return [
                field
                for field in dynamic_fields
                if not self._is_custom_field_name(field)
            ]
        except Exception:
            return []

    def _get_dynamic_standard_output_fields(self) -> List[str]:
        """Get only standard output fields from the API (excludes custom fields).

        Returns:
            List of standard output field names from the API
        """
        try:
            dynamic_fields = self._get_dynamic_output_fields()
            return [
                field
                for field in dynamic_fields
                if not self._is_custom_field_name(field)
            ]
        except Exception:
            return []

    def _is_custom_field_name(self, field_name: str) -> bool:
        """Check if a field name appears to be a custom field.

        Args:
            field_name: The field name to check

        Returns:
            True if this appears to be a custom field name
        """
        # Custom fields often have organization-specific naming patterns
        # This is a heuristic approach - can be refined based on actual API responses
        if not field_name:
            return False

        # Common custom field patterns (these are heuristics)
        custom_indicators = [
            field_name.startswith("V-"),  # Common prefix pattern
            field_name.startswith("C-"),  # Another common prefix
            field_name.startswith("Custom"),  # Explicit custom prefix
            " - " in field_name,  # Custom fields often have dashes
            len(field_name) > 50,  # Very long field names are often custom
        ]

        return any(custom_indicators)

    def _get_dynamic_search_fields(self) -> List[str]:
        """Get search fields from the API dynamically.

        Returns:
            List of search field names from the API
        """
        if self._cached_search_fields is None:
            self._logger.debug(
                f"Fetching dynamic search fields for {self.resource_name}"
            )

            # The resource_name now matches client attribute names directly
            resource = getattr(self.client, self.resource_name, None)
            if not resource or not hasattr(resource, "get_search_fields"):
                self._logger.debug(
                    f"Resource {self.resource_name} doesn't support search fields"
                )
                return []

            try:
                response = resource.get_search_fields()
                fields = []

                # Add standard fields
                for field in response.get("standardFields", []):
                    field_name = field.get("fieldName")
                    if field_name:
                        fields.append(field_name)

                # Add custom fields
                for field in response.get("customFields", []):
                    field_name = field.get("displayName")
                    if field_name:
                        fields.append(field_name)

                self._cached_search_fields = fields
                self._logger.debug(
                    f"Retrieved {len(fields)} search fields for {self.resource_name}"
                )
            except NotImplementedError as e:
                self._logger.debug(
                    f"Resource {self.resource_name} doesn't support search field discovery: {e}"
                )
                self._cached_search_fields = []
            except Exception as e:
                self._logger.warning(
                    f"Failed to fetch search fields for {self.resource_name}: {e}"
                )
                return []

        return self._cached_search_fields

    def _get_dynamic_output_fields(self) -> List[str]:
        """Get output fields from the API dynamically.

        Returns:
            List of output field names from the API
        """
        if self._cached_output_fields is None:
            self._logger.debug(
                f"Fetching dynamic output fields for {self.resource_name}"
            )

            # The resource_name now matches client attribute names directly
            resource = getattr(self.client, self.resource_name, None)
            if not resource or not hasattr(resource, "get_output_fields"):
                self._logger.debug(
                    f"Resource {self.resource_name} doesn't support output fields"
                )
                return []

            try:
                response = resource.get_output_fields()
                fields = []

                # Add standard fields
                fields.extend(response.get("standardFields", []))

                # Add custom fields
                for field in response.get("customFields", []):
                    field_name = field.get("displayName")
                    if field_name:
                        fields.append(field_name)

                self._cached_output_fields = fields
                self._logger.debug(
                    f"Retrieved {len(fields)} output fields for {self.resource_name}"
                )
            except NotImplementedError as e:
                self._logger.debug(
                    f"Resource {self.resource_name} doesn't support output field discovery: {e}"
                )
                self._cached_output_fields = []
            except Exception as e:
                self._logger.warning(
                    f"Failed to fetch output fields for {self.resource_name}: {e}"
                )
                return []

        return self._cached_output_fields

    def _get_field_operators_from_api(self, field_name: str) -> List[str]:
        """Get valid operators for a field from the API.

        Args:
            field_name: The field name to get operators for

        Returns:
            List of valid operator strings from the API, or empty list if not found
        """
        try:
            # Get the search fields from API
            search_fields_data = self._get_dynamic_search_fields_with_operators()

            # Look for the field in the API response
            for field_data in search_fields_data:
                if field_data.get("fieldName") == field_name:
                    return field_data.get("operators", [])

            return []
        except Exception as e:
            self._logger.debug(
                f"Could not get operators for field '{field_name}' from API: {e}"
            )
            return []

    def _get_dynamic_search_fields_with_operators(self) -> List[Dict[str, Any]]:
        """Get search fields from API with full field data including operators.

        Returns:
            List of field dictionaries with operators information
        """
        if not self.client:
            return []

        try:
            # Get the resource
            resource = getattr(self.client, self.resource_name, None)
            if not resource or not hasattr(resource, "get_search_fields"):
                return []

            # Get the full API response
            response = resource.get_search_fields()

            # Return the standard fields with their operator information
            return response.get("standardFields", [])

        except (Exception, NotImplementedError) as e:
            self._logger.debug(
                f"Could not get search fields with operators for {self.resource_name}: {e}"
            )
            return []

    def _get_field_type(self, field_name: Union[str, int]) -> str:
        """Get the type of a field for validation.

        Args:
            field_name: The field name (string or integer)

        Returns:
            The field type (string, number, date, boolean, enum)
        """
        # Custom fields default to string type (most flexible)
        if self._is_custom_field(field_name):
            return "string"

        # Check static field type mappings
        field_str = str(field_name)
        return self.FIELD_TYPES.get(field_str, "string")

    def _log_field_suggestions(
        self, field_name: str, available_fields: List[str], field_type: str
    ) -> None:
        """Log helpful field suggestions when a field is not found.

        Args:
            field_name: The invalid field name
            available_fields: List of available field names
            field_type: Type of field ('search' or 'output')
        """
        try:
            from .fuzzy_search import FieldFuzzySearch

            if not available_fields:
                return

            # Generate fuzzy suggestions (typos, similar names)
            fuzzy_search = FieldFuzzySearch(case_sensitive=False)
            fuzzy_suggestions = fuzzy_search.suggest_corrections(
                field_name, available_fields, threshold=0.3, max_suggestions=3
            )

            # Generate semantic suggestions (related meaning)
            semantic_matches = (
                fuzzy_search.semantic_matcher.find_semantically_similar_fields(
                    field_name, available_fields, threshold=0.1, max_results=3
                )
            )
            semantic_suggestions = [match[0] for match in semantic_matches]

            # Remove duplicates between fuzzy and semantic suggestions
            semantic_suggestions = [
                s for s in semantic_suggestions if s not in fuzzy_suggestions
            ]

            # Log suggestions at INFO level
            if fuzzy_suggestions or semantic_suggestions:
                suggestion_msg = f"{field_type.title()} field '{field_name}' not found for resource '{self.resource_name}'."

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


def validate_search_request(
    resource_name: str, search_request: SearchRequest
) -> List[str]:
    """Convenience function to validate a search request.

    Args:
        resource_name: Name of the resource (accounts, donations, etc.)
        search_request: The search request to validate

    Returns:
        List of validation error messages (empty if valid)
    """
    validator = SearchRequestValidator(resource_name)
    return validator.validate_search_request(search_request)
