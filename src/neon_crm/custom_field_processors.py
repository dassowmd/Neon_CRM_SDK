"""Custom field value processors for different Neon CRM field types.

This module provides specialized processors for handling different types of custom fields,
including validation, formatting, and API payload preparation.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Union
from decimal import Decimal, InvalidOperation

from .custom_field_types import CustomFieldTypeMapper


class FieldProcessor(ABC):
    """Abstract base class for custom field processors."""

    @abstractmethod
    def validate(self, value: Any, field_metadata: Dict[str, Any]) -> bool:
        """Validate a value for this field type.

        Args:
            value: The value to validate
            field_metadata: Custom field metadata from API

        Returns:
            True if valid, False otherwise
        """
        pass

    @abstractmethod
    def format_for_api(
        self, value: Any, field_metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Format a value for API submission.

        Args:
            value: The value to format
            field_metadata: Custom field metadata from API

        Returns:
            Dictionary with formatted value for API payload
        """
        pass

    @abstractmethod
    def parse_from_api(self, api_value: Any, field_metadata: Dict[str, Any]) -> Any:
        """Parse a value from API response.

        Args:
            api_value: Value from API response
            field_metadata: Custom field metadata from API

        Returns:
            Parsed value in appropriate Python type
        """
        pass


class TextProcessor(FieldProcessor):
    """Processor for text-based custom fields."""

    def validate(self, value: Any, field_metadata: Dict[str, Any]) -> bool:
        """Validate text field value."""
        if value is None:
            return True

        if not isinstance(value, (str, int, float)):
            return False

        # Convert to string for length validation
        str_value = str(value)

        # Basic length validation (could be enhanced with field metadata)
        return len(str_value) <= 10000  # Reasonable default limit

    def format_for_api(
        self, value: Any, field_metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Format text value for API."""
        if value is None:
            str_value = ""
        else:
            str_value = str(value).strip()

        return {"name": field_metadata.get("name"), "value": str_value}

    def parse_from_api(self, api_value: Any, field_metadata: Dict[str, Any]) -> str:
        """Parse text value from API."""
        return str(api_value) if api_value is not None else ""


class MultiValueProcessor(FieldProcessor):
    """Processor for multi-value custom fields (Checkbox, MultiSelect)."""

    def validate(self, value: Any, field_metadata: Dict[str, Any]) -> bool:
        """Validate multi-value field."""
        if value is None:
            return True

        if isinstance(value, str):
            # Parse string value to list
            parsed_values = CustomFieldTypeMapper.parse_multivalue_string(value)
            value = parsed_values

        if not isinstance(value, list):
            return False

        # Validate against available options if provided
        available_options = field_metadata.get("optionValues", [])
        if available_options:
            available_names = {opt["name"] for opt in available_options}
            return all(v in available_names for v in value)

        return True

    def format_for_api(
        self, value: Any, field_metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Format multi-value for API."""
        if value is None:
            value = []
        elif isinstance(value, str):
            value = CustomFieldTypeMapper.parse_multivalue_string(value)
        elif not isinstance(value, list):
            value = [str(value)]

        # Convert to IdNamePair objects
        option_values_with_ids = []
        available_options = {
            opt["name"]: opt["id"] for opt in field_metadata.get("optionValues", [])
        }

        for val in value:
            val_str = str(val).strip()
            if val_str in available_options:
                option_values_with_ids.append(
                    {"id": available_options[val_str], "name": val_str}
                )

        return {"id": field_metadata.get("id"), "optionValues": option_values_with_ids}

    def parse_from_api(
        self, api_value: Any, field_metadata: Dict[str, Any]
    ) -> List[str]:
        """Parse multi-value from API."""
        if api_value is None:
            return []
        elif isinstance(api_value, str):
            return CustomFieldTypeMapper.parse_multivalue_string(api_value)
        elif isinstance(api_value, list):
            return [str(v) for v in api_value]
        else:
            return [str(api_value)]


class NumericProcessor(FieldProcessor):
    """Processor for numeric custom fields (Number, Currency, Percentage)."""

    def validate(self, value: Any, field_metadata: Dict[str, Any]) -> bool:
        """Validate numeric field value."""
        if value is None:
            return True

        try:
            float(value)
            return True
        except (ValueError, TypeError):
            return False

    def format_for_api(
        self, value: Any, field_metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Format numeric value for API."""
        if value is None:
            formatted_value = ""
        else:
            try:
                # Use Decimal for precision in currency/percentage fields
                display_type = field_metadata.get("displayType", "")
                if display_type in ("Currency", "Percentage"):
                    formatted_value = str(Decimal(str(value)))
                else:
                    formatted_value = str(float(value))
            except (ValueError, TypeError, InvalidOperation):
                formatted_value = str(value)

        return {"name": field_metadata.get("name"), "value": formatted_value}

    def parse_from_api(
        self, api_value: Any, field_metadata: Dict[str, Any]
    ) -> Union[int, float]:
        """Parse numeric value from API."""
        if api_value is None or api_value == "":
            return 0

        try:
            # Check if it should be an integer based on display type
            display_type = field_metadata.get("displayType", "")
            data_type = field_metadata.get("dataType", "")

            if display_type == "Number" and data_type in ("Integer", "Whole_Number"):
                return int(float(api_value))
            else:
                return float(api_value)
        except (ValueError, TypeError):
            return 0


class DateTimeProcessor(FieldProcessor):
    """Processor for date/time custom fields."""

    def validate(self, value: Any, field_metadata: Dict[str, Any]) -> bool:
        """Validate date/time field value."""
        if value is None:
            return True

        if isinstance(value, datetime):
            return True

        if isinstance(value, str):
            # Try to parse common date formats
            formats_to_try = [
                "%Y-%m-%d",  # 2023-12-25
                "%Y-%m-%dT%H:%M:%S",  # 2023-12-25T15:30:00
                "%Y-%m-%d %H:%M:%S",  # 2023-12-25 15:30:00
                "%m/%d/%Y",  # 12/25/2023
                "%d/%m/%Y",  # 25/12/2023
                "%H:%M:%S",  # 15:30:00 (time only)
                "%H:%M",  # 15:30 (time only)
            ]

            for fmt in formats_to_try:
                try:
                    datetime.strptime(value, fmt)
                    return True
                except ValueError:
                    continue

        return False

    def format_for_api(
        self, value: Any, field_metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Format date/time value for API."""
        if value is None:
            formatted_value = ""
        elif isinstance(value, datetime):
            display_type = field_metadata.get("displayType", "")
            if display_type == "Date":
                formatted_value = value.strftime("%Y-%m-%d")
            elif display_type == "Time":
                formatted_value = value.strftime("%H:%M:%S")
            else:  # DateTime
                formatted_value = value.isoformat()
        else:
            formatted_value = str(value)

        return {"name": field_metadata.get("name"), "value": formatted_value}

    def parse_from_api(self, api_value: Any, field_metadata: Dict[str, Any]) -> str:
        """Parse date/time value from API."""
        return str(api_value) if api_value is not None else ""


class BooleanProcessor(FieldProcessor):
    """Processor for boolean custom fields (YesNo)."""

    def validate(self, value: Any, field_metadata: Dict[str, Any]) -> bool:
        """Validate boolean field value."""
        return isinstance(value, bool) or value in (
            0,
            1,
            "true",
            "false",
            "True",
            "False",
            "yes",
            "no",
            "Yes",
            "No",
        )

    def format_for_api(
        self, value: Any, field_metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Format boolean value for API."""
        if isinstance(value, bool):
            bool_value = value
        elif isinstance(value, str):
            bool_value = value.lower() in ("true", "yes", "1", "on")
        elif isinstance(value, (int, float)):
            bool_value = bool(value)
        else:
            bool_value = False

        return {
            "name": field_metadata.get("name"),
            "value": "true" if bool_value else "false",
        }

    def parse_from_api(self, api_value: Any, field_metadata: Dict[str, Any]) -> bool:
        """Parse boolean value from API."""
        if isinstance(api_value, bool):
            return api_value
        elif isinstance(api_value, str):
            return api_value.lower() in ("true", "yes", "1", "on")
        elif isinstance(api_value, (int, float)):
            return bool(api_value)
        else:
            return False


class FileProcessor(FieldProcessor):
    """Processor for file custom fields (File, Image)."""

    def validate(self, value: Any, field_metadata: Dict[str, Any]) -> bool:
        """Validate file field value."""
        if value is None:
            return True

        # For now, just validate it's a string (URL or path)
        return isinstance(value, str)

    def format_for_api(
        self, value: Any, field_metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Format file value for API."""
        return {
            "name": field_metadata.get("name"),
            "value": str(value) if value is not None else "",
        }

    def parse_from_api(self, api_value: Any, field_metadata: Dict[str, Any]) -> str:
        """Parse file value from API."""
        return str(api_value) if api_value is not None else ""


class CustomFieldProcessorFactory:
    """Factory for creating appropriate processors for custom fields."""

    _processors = {
        # Text types
        "Text": TextProcessor(),
        "OneLineText": TextProcessor(),
        "MultiLineText": TextProcessor(),
        "Email": TextProcessor(),
        "URL": TextProcessor(),
        "Phone": TextProcessor(),
        "Password": TextProcessor(),
        "Account": TextProcessor(),  # Account lookup returns string ID
        # Multi-value types
        "Checkbox": MultiValueProcessor(),
        "MultiSelect": MultiValueProcessor(),
        # Single selection types (treated as text)
        "DropDown": TextProcessor(),
        "Dropdown": TextProcessor(),
        "RadioButton": TextProcessor(),
        "Radio": TextProcessor(),
        # Numeric types
        "Number": NumericProcessor(),
        "Currency": NumericProcessor(),
        "Percentage": NumericProcessor(),
        # Date/Time types
        "Date": DateTimeProcessor(),
        "DateTime": DateTimeProcessor(),
        "Time": DateTimeProcessor(),
        # Boolean types
        "YesNo": BooleanProcessor(),
        # File types
        "File": FileProcessor(),
        "Image": FileProcessor(),
    }

    @classmethod
    def get_processor(cls, field_metadata: Dict[str, Any]) -> FieldProcessor:
        """Get the appropriate processor for a custom field.

        Args:
            field_metadata: Custom field metadata from API

        Returns:
            Appropriate FieldProcessor instance
        """
        display_type = field_metadata.get("displayType", "Text")
        return cls._processors.get(display_type, TextProcessor())

    @classmethod
    def validate_field_value(cls, value: Any, field_metadata: Dict[str, Any]) -> bool:
        """Validate a value for a custom field.

        Args:
            value: Value to validate
            field_metadata: Custom field metadata from API

        Returns:
            True if valid, False otherwise
        """
        processor = cls.get_processor(field_metadata)
        return processor.validate(value, field_metadata)

    @classmethod
    def format_for_api(
        cls, value: Any, field_metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Format a value for API submission.

        Args:
            value: Value to format
            field_metadata: Custom field metadata from API

        Returns:
            Formatted API payload dictionary
        """
        processor = cls.get_processor(field_metadata)
        return processor.format_for_api(value, field_metadata)

    @classmethod
    def parse_from_api(cls, api_value: Any, field_metadata: Dict[str, Any]) -> Any:
        """Parse a value from API response.

        Args:
            api_value: Value from API response
            field_metadata: Custom field metadata from API

        Returns:
            Parsed value in appropriate Python type
        """
        processor = cls.get_processor(field_metadata)
        return processor.parse_from_api(api_value, field_metadata)
