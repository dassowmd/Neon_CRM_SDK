"""Universal Field Manager for Standard and Custom Field Operations.

This module provides unified handling of both standard and custom fields
for migration operations, abstracting away the differences between field types.
"""

import logging
from typing import Any, Dict, List, Optional, Union, Set, TYPE_CHECKING
from dataclasses import dataclass
from enum import Enum

from ..custom_field_manager import CustomFieldValueManager
from ..custom_field_validation import CustomFieldValidator

if TYPE_CHECKING:
    from ..client import NeonClient

logger = logging.getLogger(__name__)


class FieldType(Enum):
    """Types of fields in Neon CRM."""

    STANDARD = "standard"
    CUSTOM = "custom"


@dataclass
class FieldMetadata:
    """Metadata about a field regardless of type."""

    name: str
    field_type: FieldType
    data_type: str
    is_searchable: bool
    is_output: bool
    is_required: bool = False
    is_multi_value: bool = False
    field_id: Optional[Union[int, str]] = None
    category: Optional[str] = None
    options: Optional[List[str]] = None


@dataclass
class UniversalFieldValue:
    """Represents a field value regardless of field type."""

    field_name: str
    field_type: FieldType
    value: Any
    raw_value: Any
    is_valid: bool = True
    validation_errors: Optional[List[str]] = None

    def __post_init__(self):
        """Initialize validation_errors if None."""
        if self.validation_errors is None:
            self.validation_errors = []


class UniversalFieldManager:
    """Manager for both standard and custom field operations."""

    def __init__(self, resource, client: "NeonClient", resource_type: str):
        """Initialize the universal field manager.

        Args:
            resource: The resource instance (e.g., client.accounts)
            client: Neon CRM client instance
            resource_type: Type of resource (accounts, donations, etc.)
        """
        self._resource = resource
        self._client = client
        self._resource_type = resource_type
        self._logger = logging.getLogger(f"universal_fields.{resource_type}")

        # Initialize custom field manager for custom field operations
        self._custom_field_manager = CustomFieldValueManager(client, resource_type)

        # Cache for field metadata
        self._field_metadata_cache: Dict[str, FieldMetadata] = {}
        self._standard_fields_cache: Optional[Dict[str, Any]] = None
        self._custom_fields_cache: Optional[Dict[str, Any]] = None

    def get_field_value(
        self, resource_id: Union[str, int], field_name: str
    ) -> Optional[UniversalFieldValue]:
        """Get a field value regardless of whether it's standard or custom.

        Args:
            resource_id: ID of the resource
            field_name: Name of the field

        Returns:
            UniversalFieldValue object or None if field doesn't exist
        """
        try:
            # Determine field type
            field_metadata = self.get_field_metadata(field_name)
            if not field_metadata:
                self._logger.warning(f"Field {field_name} not found")
                return None

            if field_metadata.field_type == FieldType.CUSTOM:
                # Use custom field manager
                value = self._custom_field_manager.get_custom_field_value(
                    resource_id, field_name
                )
                return UniversalFieldValue(
                    field_name=field_name,
                    field_type=FieldType.CUSTOM,
                    value=value,
                    raw_value=value,
                )
            else:
                # Handle standard field
                return self._get_standard_field_value(
                    resource_id, field_name, field_metadata
                )

        except Exception as e:
            self._logger.error(f"Error getting field value for {field_name}: {e}")
            return None

    def set_field_value(
        self,
        resource_id: Union[str, int],
        field_name: str,
        value: Any,
        validate: bool = True,
    ) -> bool:
        """Set a field value regardless of whether it's standard or custom.

        Args:
            resource_id: ID of the resource
            field_name: Name of the field
            value: Value to set
            validate: Whether to validate the value

        Returns:
            True if successful, False otherwise
        """
        try:
            # Determine field type
            field_metadata = self.get_field_metadata(field_name)
            if not field_metadata:
                self._logger.error(f"Field {field_name} not found")
                return False

            if field_metadata.field_type == FieldType.CUSTOM:
                # Use custom field manager
                return self._custom_field_manager.set_custom_field_value(
                    resource_id, field_name, value
                )
            else:
                # Handle standard field
                return self._set_standard_field_value(
                    resource_id, field_name, value, field_metadata, validate
                )

        except Exception as e:
            self._logger.error(f"Error setting field value for {field_name}: {e}")
            return False

    def clear_field_value(self, resource_id: Union[str, int], field_name: str) -> bool:
        """Clear a field value regardless of whether it's standard or custom.

        Args:
            resource_id: ID of the resource
            field_name: Name of the field

        Returns:
            True if successful, False otherwise
        """
        try:
            # Determine field type
            field_metadata = self.get_field_metadata(field_name)
            if not field_metadata:
                self._logger.error(f"Field {field_name} not found")
                return False

            if field_metadata.field_type == FieldType.CUSTOM:
                # Use custom field manager
                return self._custom_field_manager.clear_custom_field_value(
                    resource_id, field_name
                )
            else:
                # Handle standard field - set to None or empty string based on field type
                return self._clear_standard_field_value(
                    resource_id, field_name, field_metadata
                )

        except Exception as e:
            self._logger.error(f"Error clearing field value for {field_name}: {e}")
            return False

    def get_field_metadata(self, field_name: str) -> Optional[FieldMetadata]:
        """Get metadata for a field regardless of type.

        Args:
            field_name: Name of the field

        Returns:
            FieldMetadata object or None if field doesn't exist
        """
        # Check cache first
        if field_name in self._field_metadata_cache:
            return self._field_metadata_cache[field_name]

        # Try to find as custom field first
        custom_field = self._find_custom_field_metadata(field_name)
        if custom_field:
            self._field_metadata_cache[field_name] = custom_field
            return custom_field

        # Try to find as standard field
        standard_field = self._find_standard_field_metadata(field_name)
        if standard_field:
            self._field_metadata_cache[field_name] = standard_field
            return standard_field

        return None

    def list_all_fields(self) -> List[FieldMetadata]:
        """List all available fields (both standard and custom).

        Returns:
            List of FieldMetadata objects for all available fields
        """
        fields = []

        # Get standard fields
        standard_fields = self._get_standard_fields_metadata()
        fields.extend(standard_fields)

        # Get custom fields
        custom_fields = self._get_custom_fields_metadata()
        fields.extend(custom_fields)

        return fields

    def find_fields_by_pattern(self, pattern: str) -> List[FieldMetadata]:
        """Find fields matching a pattern.

        Args:
            pattern: Pattern to match (supports * wildcard)

        Returns:
            List of matching FieldMetadata objects
        """
        all_fields = self.list_all_fields()
        matching_fields = []

        # Simple pattern matching (could be enhanced with regex)
        pattern_prefix = pattern.replace("*", "")

        for field in all_fields:
            if pattern == "*" or field.name.startswith(pattern_prefix):
                matching_fields.append(field)

        return matching_fields

    def bulk_get_field_values(
        self, resource_id: Union[str, int], field_names: List[str]
    ) -> Dict[str, UniversalFieldValue]:
        """Get multiple field values efficiently.

        Args:
            resource_id: ID of the resource
            field_names: List of field names to get

        Returns:
            Dictionary mapping field names to UniversalFieldValue objects
        """
        result = {}

        # Separate standard and custom fields for efficient batch operations
        standard_fields = []
        custom_fields = []

        for field_name in field_names:
            field_metadata = self.get_field_metadata(field_name)
            if field_metadata:
                if field_metadata.field_type == FieldType.CUSTOM:
                    custom_fields.append(field_name)
                else:
                    standard_fields.append(field_name)

        # Get standard field values (requires resource fetch)
        if standard_fields:
            try:
                resource_data = self._resource.get(resource_id)
                if resource_data:
                    for field_name in standard_fields:
                        value = resource_data.get(field_name)
                        if value is not None:
                            result[field_name] = UniversalFieldValue(
                                field_name=field_name,
                                field_type=FieldType.STANDARD,
                                value=value,
                                raw_value=value,
                            )
            except Exception as e:
                self._logger.warning(f"Error getting standard fields: {e}")

        # Get custom field values
        for field_name in custom_fields:
            field_value = self.get_field_value(resource_id, field_name)
            if field_value:
                result[field_name] = field_value

        return result

    def bulk_set_field_values(
        self,
        resource_id: Union[str, int],
        field_values: Dict[str, Any],
        validate: bool = True,
    ) -> Dict[str, bool]:
        """Set multiple field values efficiently.

        Args:
            resource_id: ID of the resource
            field_values: Dictionary of field names to values
            validate: Whether to validate values

        Returns:
            Dictionary mapping field names to success status
        """
        result = {}

        # Separate standard and custom fields
        standard_updates = {}
        custom_updates = {}

        for field_name, value in field_values.items():
            field_metadata = self.get_field_metadata(field_name)
            if field_metadata:
                if field_metadata.field_type == FieldType.CUSTOM:
                    custom_updates[field_name] = value
                else:
                    standard_updates[field_name] = value

        # Update standard fields in batch (single API call)
        if standard_updates:
            try:
                success = self._bulk_update_standard_fields(
                    resource_id, standard_updates, validate
                )
                for field_name in standard_updates.keys():
                    result[field_name] = success
            except Exception as e:
                self._logger.error(f"Error updating standard fields: {e}")
                for field_name in standard_updates.keys():
                    result[field_name] = False

        # Update custom fields individually
        for field_name, value in custom_updates.items():
            success = self.set_field_value(resource_id, field_name, value, validate)
            result[field_name] = success

        return result

    def _get_standard_field_value(
        self,
        resource_id: Union[str, int],
        field_name: str,
        field_metadata: FieldMetadata,
    ) -> Optional[UniversalFieldValue]:
        """Get a standard field value."""
        try:
            # For standard fields, we need to fetch the full resource
            resource_data = self._resource.get(resource_id)
            if not resource_data:
                return None

            value = resource_data.get(field_name)
            return UniversalFieldValue(
                field_name=field_name,
                field_type=FieldType.STANDARD,
                value=value,
                raw_value=value,
            )
        except Exception as e:
            self._logger.error(f"Error getting standard field {field_name}: {e}")
            return None

    def _set_standard_field_value(
        self,
        resource_id: Union[str, int],
        field_name: str,
        value: Any,
        field_metadata: FieldMetadata,
        validate: bool,
    ) -> bool:
        """Set a standard field value."""
        try:
            # For standard fields, we update the resource directly
            update_data = {field_name: value}

            # Use PATCH to update only the specific field
            if hasattr(self._resource, "patch"):
                return self._resource.patch(resource_id, update_data)
            else:
                # Fallback to update method
                return self._resource.update(resource_id, update_data)
        except Exception as e:
            self._logger.error(f"Error setting standard field {field_name}: {e}")
            return False

    def _clear_standard_field_value(
        self,
        resource_id: Union[str, int],
        field_name: str,
        field_metadata: FieldMetadata,
    ) -> bool:
        """Clear a standard field value."""
        try:
            # For standard fields, set to None or appropriate empty value
            empty_value = self._get_empty_value_for_field_type(field_metadata.data_type)
            return self._set_standard_field_value(
                resource_id, field_name, empty_value, field_metadata, False
            )
        except Exception as e:
            self._logger.error(f"Error clearing standard field {field_name}: {e}")
            return False

    def _bulk_update_standard_fields(
        self,
        resource_id: Union[str, int],
        field_updates: Dict[str, Any],
        validate: bool,
    ) -> bool:
        """Update multiple standard fields in a single API call."""
        try:
            # Use PATCH for efficient updates
            if hasattr(self._resource, "patch"):
                return self._resource.patch(resource_id, field_updates)
            else:
                # Fallback to update method
                return self._resource.update(resource_id, field_updates)
        except Exception as e:
            self._logger.error(f"Error bulk updating standard fields: {e}")
            return False

    def _find_custom_field_metadata(self, field_name: str) -> Optional[FieldMetadata]:
        """Find metadata for a custom field."""
        try:
            custom_field = self._resource.find_custom_field_by_name(field_name)
            if not custom_field:
                return None

            return FieldMetadata(
                name=field_name,
                field_type=FieldType.CUSTOM,
                data_type=custom_field.get("displayType", "unknown"),
                is_searchable=True,  # Custom fields are generally searchable
                is_output=True,  # Custom fields are generally in output
                is_required=custom_field.get("required", False),
                is_multi_value=custom_field.get("displayType")
                in ["MultiSelect", "Checkbox"],
                field_id=custom_field.get("id"),
                category=custom_field.get("category"),
                options=custom_field.get("options", []),
            )
        except Exception as e:
            self._logger.debug(f"Custom field {field_name} not found: {e}")
            return None

    def _find_standard_field_metadata(self, field_name: str) -> Optional[FieldMetadata]:
        """Find metadata for a standard field."""
        try:
            # Check if field is in search fields
            search_fields = self._get_search_fields()
            output_fields = self._get_output_fields()

            is_searchable = any(f.get("fieldName") == field_name for f in search_fields)
            is_output = any(f.get("fieldName") == field_name for f in output_fields)

            if not is_searchable and not is_output:
                return None

            # Get data type from field definitions
            data_type = self._infer_standard_field_data_type(field_name)

            return FieldMetadata(
                name=field_name,
                field_type=FieldType.STANDARD,
                data_type=data_type,
                is_searchable=is_searchable,
                is_output=is_output,
                is_required=self._is_standard_field_required(field_name),
                is_multi_value=False,  # Standard fields are generally single-value
                field_id=field_name,  # Standard fields use name as ID
                category=self._resource_type,
            )
        except Exception as e:
            self._logger.debug(f"Standard field {field_name} not found: {e}")
            return None

    def _get_standard_fields_metadata(self) -> List[FieldMetadata]:
        """Get metadata for all standard fields."""
        if self._standard_fields_cache:
            return self._standard_fields_cache

        fields = []

        try:
            # Get all search and output fields
            search_fields = self._get_search_fields()
            output_fields = self._get_output_fields()

            # Combine and deduplicate
            all_field_names = set()
            for field in search_fields:
                all_field_names.add(field.get("fieldName"))
            for field in output_fields:
                all_field_names.add(field.get("fieldName"))

            # Create metadata for each field
            for field_name in all_field_names:
                if field_name:  # Skip None values
                    metadata = self._find_standard_field_metadata(field_name)
                    if metadata:
                        fields.append(metadata)

            self._standard_fields_cache = fields

        except Exception as e:
            self._logger.warning(f"Error getting standard fields metadata: {e}")

        return fields

    def _get_custom_fields_metadata(self) -> List[FieldMetadata]:
        """Get metadata for all custom fields."""
        if self._custom_fields_cache:
            return self._custom_fields_cache

        fields = []

        try:
            custom_fields = list(self._resource.list_custom_fields())

            for custom_field in custom_fields:
                field_name = custom_field.get("name")
                if field_name:
                    metadata = FieldMetadata(
                        name=field_name,
                        field_type=FieldType.CUSTOM,
                        data_type=custom_field.get("displayType", "unknown"),
                        is_searchable=True,
                        is_output=True,
                        is_required=custom_field.get("required", False),
                        is_multi_value=custom_field.get("displayType")
                        in ["MultiSelect", "Checkbox"],
                        field_id=custom_field.get("id"),
                        category=custom_field.get("category"),
                        options=custom_field.get("options", []),
                    )
                    fields.append(metadata)

            self._custom_fields_cache = fields

        except Exception as e:
            self._logger.warning(f"Error getting custom fields metadata: {e}")

        return fields

    def _get_search_fields(self) -> List[Dict[str, Any]]:
        """Get search fields for this resource."""
        try:
            result = self._resource.get_search_fields()
            return result.get("standardFields", [])
        except Exception as e:
            self._logger.warning(f"Error getting search fields: {e}")
            return []

    def _get_output_fields(self) -> List[Dict[str, Any]]:
        """Get output fields for this resource."""
        try:
            result = self._resource.get_output_fields()
            return result.get("standardFields", [])
        except Exception as e:
            self._logger.warning(f"Error getting output fields: {e}")
            return []

    def _infer_standard_field_data_type(self, field_name: str) -> str:
        """Infer data type for a standard field based on naming patterns."""
        field_name_lower = field_name.lower()

        # Common patterns
        if "date" in field_name_lower:
            return "date"
        elif "email" in field_name_lower:
            return "email"
        elif "phone" in field_name_lower:
            return "phone"
        elif "amount" in field_name_lower or "fee" in field_name_lower:
            return "currency"
        elif field_name_lower in ["id", "accountid", "donationid", "eventid"]:
            return "number"
        elif "type" in field_name_lower:
            return "text"
        else:
            return "text"  # Default

    def _is_standard_field_required(self, field_name: str) -> bool:
        """Check if a standard field is required."""
        # Common required fields by resource type
        required_fields = {
            "accounts": ["firstName", "lastName", "accountType"],
            "donations": ["accountId", "amount", "date"],
            "events": ["name", "startDate"],
        }

        return field_name in required_fields.get(self._resource_type, [])

    def _get_empty_value_for_field_type(self, data_type: str) -> Any:
        """Get appropriate empty value for a field type."""
        empty_values = {
            "text": "",
            "number": None,
            "date": None,
            "email": "",
            "phone": "",
            "currency": None,
            "boolean": False,
        }

        return empty_values.get(data_type, None)
