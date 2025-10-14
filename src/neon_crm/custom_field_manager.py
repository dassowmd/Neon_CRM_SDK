"""Advanced custom field value management for Neon CRM.

This module provides high-level operations for managing custom field values,
including multi-value field operations, validation, and batch processing.
"""

from typing import Any, Dict, List, Union, TYPE_CHECKING
from dataclasses import dataclass

from .custom_field_processors import CustomFieldProcessorFactory
from .custom_field_types import CustomFieldTypeMapper

if TYPE_CHECKING:
    from .client import NeonClient


@dataclass
class ValidationResult:
    """Result of field validation operation."""

    is_valid: bool
    errors: List[str]
    warnings: List[str]

    def __bool__(self) -> bool:
        """Allow using ValidationResult in boolean context."""
        return self.is_valid


@dataclass
class CustomFieldUpdate:
    """Represents a custom field update operation."""

    resource_id: Union[int, str]
    field_name: str
    value: Any
    operation: str = "replace"  # replace, add, remove, append
    validate: bool = True


@dataclass
class BatchResult:
    """Result of batch custom field operations."""

    successful: int
    failed: int
    errors: List[str]
    warnings: List[str]


class CustomFieldValueManager:
    """Advanced manager for custom field value operations."""

    def __init__(self, client: "NeonClient", resource_type: str):
        """Initialize the custom field value manager.

        Args:
            client: Neon CRM client instance
            resource_type: Type of resource (accounts, donations, etc.)
        """
        self._client = client
        self._resource_type = resource_type
        self._resource = getattr(client, resource_type)

    def validate_field_value(self, field_name: str, value: Any) -> ValidationResult:
        """Validate a value for a custom field.

        Args:
            field_name: Name of the custom field
            value: Value to validate

        Returns:
            ValidationResult with validation status and messages
        """
        errors = []
        warnings = []

        try:
            # Get field metadata
            field_metadata = self._resource.find_custom_field_by_name(field_name)
            if not field_metadata:
                return ValidationResult(
                    False, [f"Custom field '{field_name}' not found"], []
                )

            # Use processor to validate
            is_valid = CustomFieldProcessorFactory.validate_field_value(
                value, field_metadata
            )

            if not is_valid:
                errors.append(f"Invalid value for field '{field_name}': {value}")

            return ValidationResult(is_valid, errors, warnings)

        except Exception as e:
            return ValidationResult(False, [f"Validation error: {str(e)}"], [])

    def get_custom_field_value(
        self, resource_id: Union[int, str], field_name: str
    ) -> Any:
        """Get the current value of a custom field for a resource.

        Args:
            resource_id: ID of the resource
            field_name: Name of the custom field

        Returns:
            Current field value, parsed to appropriate Python type
        """
        try:
            # Use search to get the field value
            search_request = {
                "searchFields": [
                    {
                        "field": (
                            "Account ID" if self._resource_type == "accounts" else "ID"
                        ),
                        "operator": "EQUAL",
                        "value": str(resource_id),
                    }
                ],
                "outputFields": [field_name],
            }

            results = list(self._resource.search(search_request))
            if not results:
                return None

            api_value = results[0].get(field_name)
            if api_value is None:
                return None

            # Get field metadata and parse value
            field_metadata = self._resource.find_custom_field_by_name(field_name)
            if field_metadata:
                return CustomFieldProcessorFactory.parse_from_api(
                    api_value, field_metadata
                )

            return api_value

        except Exception:
            return None

    def set_custom_field_value(
        self,
        resource_id: Union[int, str],
        field_name: str,
        value: Any,
        validate: bool = True,
    ) -> bool:
        """Set a custom field value for a resource.

        Args:
            resource_id: ID of the resource
            field_name: Name of the custom field
            value: Value to set
            validate: Whether to validate the value before setting

        Returns:
            True if successful, False otherwise
        """
        try:
            # Validate if requested
            if validate:
                validation = self.validate_field_value(field_name, value)
                if not validation.is_valid:
                    return False

            # Get field metadata
            field_metadata = self._resource.find_custom_field_by_name(field_name)
            if not field_metadata:
                return False

            # Format for API
            formatted_field = CustomFieldProcessorFactory.format_for_api(
                value, field_metadata
            )

            # Determine payload structure based on field type
            if CustomFieldTypeMapper.requires_option_values(field_metadata):
                # Use accountCustomFields for option-based fields
                update_payload = {
                    f"{self._get_account_type()}": {
                        "accountCustomFields": [formatted_field]
                    }
                }
            else:
                # Use customFieldResponses for text/numeric fields
                update_payload = {
                    f"{self._get_account_type()}": {
                        "customFieldResponses": [formatted_field]
                    }
                }

            # Update the resource
            self._resource.update(resource_id, update_payload)
            return True

        except Exception:
            return False

    def add_to_multivalue_field(
        self, resource_id: Union[int, str], field_name: str, new_option: str
    ) -> bool:
        """Add an option to a multi-value field without losing existing values.

        Args:
            resource_id: ID of the resource
            field_name: Name of the multi-value custom field
            new_option: Option to add

        Returns:
            True if successful, False otherwise
        """
        try:
            # Get current value
            current_value = self.get_custom_field_value(resource_id, field_name)

            # Parse current values
            if isinstance(current_value, list):
                current_options = current_value
            elif isinstance(current_value, str):
                current_options = CustomFieldTypeMapper.parse_multivalue_string(
                    current_value
                )
            else:
                current_options = []

            # Add new option if not already present
            if new_option not in current_options:
                current_options.append(new_option)

            # Set the updated value
            return self.set_custom_field_value(resource_id, field_name, current_options)

        except Exception:
            return False

    def remove_from_multivalue_field(
        self, resource_id: Union[int, str], field_name: str, option_to_remove: str
    ) -> bool:
        """Remove an option from a multi-value field.

        Args:
            resource_id: ID of the resource
            field_name: Name of the multi-value custom field
            option_to_remove: Option to remove

        Returns:
            True if successful, False otherwise
        """
        try:
            # Get current value
            current_value = self.get_custom_field_value(resource_id, field_name)

            # Parse current values
            if isinstance(current_value, list):
                current_options = current_value
            elif isinstance(current_value, str):
                current_options = CustomFieldTypeMapper.parse_multivalue_string(
                    current_value
                )
            else:
                current_options = []

            # Remove option if present
            if option_to_remove in current_options:
                current_options.remove(option_to_remove)

            # Set the updated value
            return self.set_custom_field_value(resource_id, field_name, current_options)

        except Exception:
            return False

    def append_to_text_field(
        self,
        resource_id: Union[int, str],
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
        """
        try:
            # Get current value
            current_value = self.get_custom_field_value(resource_id, field_name)
            current_text = str(current_value) if current_value else ""

            # Append new text
            if current_text:
                new_value = current_text + separator + additional_text
            else:
                new_value = additional_text

            # Set the updated value
            return self.set_custom_field_value(resource_id, field_name, new_value)

        except Exception:
            return False

    def clear_custom_field_value(
        self, resource_id: Union[int, str], field_name: str
    ) -> bool:
        """Clear a custom field value.

        For checkbox/multi-select fields: removes the field entirely from the resource.
        For text/numeric fields: sets the field to an empty value.

        Args:
            resource_id: ID of the resource
            field_name: Name of the custom field

        Returns:
            True if successful, False otherwise
        """
        try:
            # Get field metadata to determine the clearing approach
            field_metadata = self._resource.find_custom_field_by_name(field_name)
            if not field_metadata:
                # If we can't get field metadata due to server errors, fall back to text field approach
                return self.set_custom_field_value(
                    resource_id, field_name, "", validate=False
                )

            # For checkbox/multi-select fields, we need to remove them entirely
            if CustomFieldTypeMapper.requires_option_values(field_metadata):
                return self._clear_option_field(resource_id, field_name)
            else:
                # For text/numeric fields, set to empty value
                return self.set_custom_field_value(
                    resource_id, field_name, "", validate=False
                )

        except Exception as e:
            # Log the specific error for debugging
            import logging

            logger = logging.getLogger(__name__)
            logger.warning(
                f"Error in clear_custom_field_value for field '{field_name}': {e}"
            )

            # Fall back to simple text field clearing approach
            try:
                return self.set_custom_field_value(
                    resource_id, field_name, "", validate=False
                )
            except Exception:
                return False

    def _clear_option_field(
        self, resource_id: Union[int, str], field_name: str
    ) -> bool:
        """Clear a checkbox/multi-select field by removing it entirely from the resource.

        This method gets the full resource, removes the specified field from
        accountCustomFields, and puts the entire resource back - which is how
        the Neon CRM UI clears these fields.

        Args:
            resource_id: ID of the resource
            field_name: Name of the field to clear

        Returns:
            True if successful, False otherwise
        """
        try:
            # Get fresh resource data (avoid concurrency issues)
            resource_data = self._resource.get(resource_id)
            if not resource_data:
                return False

            # Handle both individual and company accounts
            account_key = None
            if (
                "individualAccount" in resource_data
                and resource_data["individualAccount"]
            ):
                account_key = "individualAccount"
            elif "companyAccount" in resource_data and resource_data["companyAccount"]:
                account_key = "companyAccount"
            else:
                return False

            # Remove the target field from accountCustomFields
            if "accountCustomFields" in resource_data[account_key]:
                original_fields = resource_data[account_key]["accountCustomFields"]
                filtered_fields = [
                    field
                    for field in original_fields
                    if field.get("name") != field_name
                ]
                resource_data[account_key]["accountCustomFields"] = filtered_fields

            # PUT the entire resource back (without the cleared field)
            # Use update_type="full" to force PUT instead of PATCH for complete replacement
            self._resource.update(resource_id, resource_data, update_type="full")
            return True

        except Exception:
            return False

    def set_multiple_custom_field_values(
        self,
        resource_id: Union[int, str],
        field_values: Dict[str, Any],
        validate: bool = True,
    ) -> BatchResult:
        """Set multiple custom field values in a single operation.

        Args:
            resource_id: ID of the resource
            field_values: Dictionary mapping field names to values
            validate: Whether to validate values before setting

        Returns:
            BatchResult with operation statistics
        """
        successful = 0
        failed = 0
        errors = []
        warnings = []

        for field_name, value in field_values.items():
            try:
                if self.set_custom_field_value(
                    resource_id, field_name, value, validate
                ):
                    successful += 1
                else:
                    failed += 1
                    errors.append(f"Failed to set {field_name}")
            except Exception as e:
                failed += 1
                errors.append(f"Error setting {field_name}: {str(e)}")

        return BatchResult(successful, failed, errors, warnings)

    def batch_update_custom_fields(
        self, updates: List[CustomFieldUpdate]
    ) -> BatchResult:
        """Perform batch updates on custom fields.

        Args:
            updates: List of CustomFieldUpdate objects

        Returns:
            BatchResult with operation statistics
        """
        successful = 0
        failed = 0
        errors = []
        warnings = []

        for update in updates:
            try:
                success = False

                if update.operation == "replace":
                    success = self.set_custom_field_value(
                        update.resource_id,
                        update.field_name,
                        update.value,
                        update.validate,
                    )
                elif update.operation == "add" and isinstance(update.value, str):
                    success = self.add_to_multivalue_field(
                        update.resource_id, update.field_name, update.value
                    )
                elif update.operation == "remove" and isinstance(update.value, str):
                    success = self.remove_from_multivalue_field(
                        update.resource_id, update.field_name, update.value
                    )
                elif update.operation == "append" and isinstance(update.value, str):
                    success = self.append_to_text_field(
                        update.resource_id, update.field_name, update.value
                    )

                if success:
                    successful += 1
                else:
                    failed += 1
                    errors.append(
                        f"Failed {update.operation} on {update.field_name} for resource {update.resource_id}"
                    )

            except Exception as e:
                failed += 1
                errors.append(f"Error in {update.operation} operation: {str(e)}")

        return BatchResult(successful, failed, errors, warnings)

    def _get_account_type(self) -> str:
        """Get the appropriate account type for API payloads."""
        # For now, assume individual accounts - this could be enhanced
        # to detect account type or accept it as a parameter
        return "individualAccount"
