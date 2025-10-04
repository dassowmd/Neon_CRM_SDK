"""Custom field type handling utilities.

This module provides utilities for mapping Neon CRM custom field types
to Python types and validation rules.
"""

from typing import Any, Dict, List, Optional, Type


class CustomFieldTypeMapper:
    """Maps Neon CRM custom field types to Python types."""

    # Mapping from displayType to Python type (comprehensive Neon CRM support)
    DISPLAY_TYPE_TO_PYTHON_TYPE = {
        # Text types
        "Text": str,
        "OneLineText": str,
        "MultiLineText": str,
        "Email": str,
        "URL": str,
        "Phone": str,
        "Password": str,  # Secure text input
        # Numeric types
        "Number": int,
        "Currency": float,
        "Percentage": float,
        # Date/Time types
        "Date": str,  # API returns dates as strings (ISO format)
        "DateTime": str,  # API returns datetimes as strings (ISO format)
        "Time": str,  # API returns times as strings (HH:MM format)
        # Boolean types
        "Checkbox": list,  # Multi-select checkboxes return lists
        "YesNo": bool,  # Single boolean checkbox
        # Selection types
        "DropDown": str,  # Single selection dropdown
        "Dropdown": str,  # Alternative spelling in API
        "MultiSelect": list,  # Multi-selection dropdown
        "RadioButton": str,  # Single selection radio buttons
        "Radio": str,  # Alternative spelling in API
        # File types
        "File": str,  # File URLs/paths as strings
        "Image": str,  # Image URLs/paths as strings
        # Special types
        "Account": str,  # Account lookup field (returns account ID as string)
    }

    # Mapping from dataType to Python type (comprehensive Neon CRM support)
    DATA_TYPE_TO_PYTHON_TYPE = {
        # Text types
        "String": str,
        "Text": str,
        "Email": str,
        "Phone": str,
        "Area_Code": str,
        "Name": str,
        # Numeric types
        "Integer": int,
        "Whole_Number": int,
        "Decimal": float,
        "Float": float,
        "Currency": float,
        # Boolean types
        "Boolean": bool,
        # Date/Time types
        "Date": str,
        "DateTime": str,
        "Time": str,
        # Collection types
        "Array": list,
    }

    @classmethod
    def get_python_type(cls, custom_field: Dict[str, Any]) -> Optional[Type]:
        """Get the Python type for a custom field based on its metadata.

        Args:
            custom_field: Custom field dictionary with metadata

        Returns:
            Python type class (str, int, float, bool, list) or None if unknown

        Example:
            >>> field = {
            ...     "id": "144",
            ...     "name": "If bringing, indicate the dish you will share.",
            ...     "displayType": "MultiLineText",
            ...     "dataType": None
            ... }
            >>> CustomFieldTypeMapper.get_python_type(field)
            <class 'str'>
        """
        # First try dataType if available
        data_type = custom_field.get("dataType")
        if data_type and data_type in cls.DATA_TYPE_TO_PYTHON_TYPE:
            return cls.DATA_TYPE_TO_PYTHON_TYPE[data_type]

        # Fall back to displayType
        display_type = custom_field.get("displayType")
        if display_type and display_type in cls.DISPLAY_TYPE_TO_PYTHON_TYPE:
            return cls.DISPLAY_TYPE_TO_PYTHON_TYPE[display_type]

        # Default fallback
        return str

    @classmethod
    def convert_value(cls, value: Any, custom_field: Dict[str, Any]) -> Any:
        """Convert a value to the appropriate Python type for a custom field.

        Args:
            value: The value to convert
            custom_field: Custom field metadata

        Returns:
            Converted value
        """
        if value is None:
            return None

        target_type = cls.get_python_type(custom_field)

        if target_type is None:
            return value

        # Handle special cases
        if target_type is bool:
            if isinstance(value, str):
                return value.lower() in ("true", "yes", "1", "on")
            return bool(value)

        if target_type is list:
            if isinstance(value, str):
                # Handle both pipe and comma separators for multi-value fields
                if "|" in value:
                    return [item.strip() for item in value.split("|") if item.strip()]
                else:
                    return [item.strip() for item in value.split(",") if item.strip()]
            elif isinstance(value, list):
                return value
            else:
                return [str(value)]

        # Standard type conversion
        try:
            return target_type(value)
        except (ValueError, TypeError):
            # If conversion fails, return original value
            return value

    @classmethod
    def is_numeric_type(cls, custom_field: Dict[str, Any]) -> bool:
        """Check if a custom field represents a numeric type.

        Args:
            custom_field: Custom field metadata

        Returns:
            True if the field is numeric, False otherwise
        """
        python_type = cls.get_python_type(custom_field)
        return python_type in (int, float)

    @classmethod
    def is_text_type(cls, custom_field: Dict[str, Any]) -> bool:
        """Check if a custom field represents a text type.

        Args:
            custom_field: Custom field metadata

        Returns:
            True if the field is text-based, False otherwise
        """
        python_type = cls.get_python_type(custom_field)
        return python_type is str

    @classmethod
    def get_field_info(cls, custom_field: Dict[str, Any]) -> Dict[str, Any]:
        """Get comprehensive information about a custom field.

        Args:
            custom_field: Custom field metadata

        Returns:
            Dictionary with field information including inferred type
        """
        python_type = cls.get_python_type(custom_field)

        return {
            "id": custom_field.get("id"),
            "name": custom_field.get("name"),
            "displayName": custom_field.get("displayName"),
            "dataType": custom_field.get("dataType"),
            "displayType": custom_field.get("displayType"),
            "pythonType": python_type,
            "pythonTypeName": python_type.__name__ if python_type else None,
            "isNumeric": cls.is_numeric_type(custom_field),
            "isText": cls.is_text_type(custom_field),
            "isMultiValue": cls.is_multivalue_type(custom_field),
            "isDate": cls.is_date_type(custom_field),
            "isFile": cls.is_file_type(custom_field),
            "status": custom_field.get("status"),
            "component": custom_field.get("component"),
            "requiresOptions": cls.requires_option_values(custom_field),
        }

    @classmethod
    def is_multivalue_type(cls, custom_field: Dict[str, Any]) -> bool:
        """Check if a custom field supports multiple values.

        Args:
            custom_field: Custom field metadata

        Returns:
            True if the field supports multiple values, False otherwise
        """
        display_type = custom_field.get("displayType", "")
        return display_type in ("Checkbox", "MultiSelect")

    @classmethod
    def is_date_type(cls, custom_field: Dict[str, Any]) -> bool:
        """Check if a custom field represents a date/time type.

        Args:
            custom_field: Custom field metadata

        Returns:
            True if the field is date/time-based, False otherwise
        """
        display_type = custom_field.get("displayType", "")
        data_type = custom_field.get("dataType", "")
        return display_type in ("Date", "DateTime", "Time") or data_type in (
            "Date",
            "DateTime",
            "Time",
        )

    @classmethod
    def is_file_type(cls, custom_field: Dict[str, Any]) -> bool:
        """Check if a custom field represents a file type.

        Args:
            custom_field: Custom field metadata

        Returns:
            True if the field is file-based, False otherwise
        """
        display_type = custom_field.get("displayType", "")
        return display_type in ("File", "Image")

    @classmethod
    def requires_option_values(cls, custom_field: Dict[str, Any]) -> bool:
        """Check if a custom field requires optionValues in the API payload.

        Args:
            custom_field: Custom field metadata

        Returns:
            True if the field should use optionValues format, False if it should use value format
        """
        display_type = custom_field.get("displayType", "")
        return display_type in (
            "Checkbox",
            "MultiSelect",
            "DropDown",
            "Dropdown",
            "RadioButton",
            "Radio",
        )

    @classmethod
    def get_payload_format(cls, custom_field: Dict[str, Any]) -> str:
        """Get the appropriate API payload format for a custom field.

        Args:
            custom_field: Custom field metadata

        Returns:
            "optionValues" for selection-based fields, "value" for text/numeric fields
        """
        return "optionValues" if cls.requires_option_values(custom_field) else "value"

    @classmethod
    def format_multivalue_string(cls, values: List[str], separator: str = "|") -> str:
        """Format a list of values into a multi-value string.

        Args:
            values: List of string values
            separator: Separator to use (default: "|")

        Returns:
            Formatted multi-value string
        """
        return separator.join(str(v).strip() for v in values if str(v).strip())

    @classmethod
    def parse_multivalue_string(cls, value_string: str) -> List[str]:
        """Parse a multi-value string into a list of values.

        Args:
            value_string: String with pipe or comma-separated values

        Returns:
            List of individual values
        """
        if not value_string:
            return []

        # Handle both pipe and comma separators
        if "|" in value_string:
            return [item.strip() for item in value_string.split("|") if item.strip()]
        else:
            return [item.strip() for item in value_string.split(",") if item.strip()]
