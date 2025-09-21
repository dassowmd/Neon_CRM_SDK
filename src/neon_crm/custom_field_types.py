"""Custom field type handling utilities.

This module provides utilities for mapping Neon CRM custom field types
to Python types and validation rules.
"""

from typing import Any, Dict, Optional, Type, Union


class CustomFieldTypeMapper:
    """Maps Neon CRM custom field types to Python types."""

    # Mapping from displayType to Python type
    DISPLAY_TYPE_TO_PYTHON_TYPE = {
        # Text types
        "Text": str,
        "MultiLineText": str,
        "Email": str,
        "URL": str,
        "Phone": str,
        # Numeric types
        "Number": int,
        "Currency": float,
        "Percentage": float,
        # Date/Time types
        "Date": str,  # API returns dates as strings
        "DateTime": str,  # API returns datetimes as strings
        "Time": str,  # API returns times as strings
        # Boolean types
        "Checkbox": bool,
        "YesNo": bool,
        # Selection types
        "DropDown": str,
        "MultiSelect": list,
        "RadioButton": str,
        # File types
        "File": str,  # File URLs/paths as strings
        "Image": str,  # Image URLs/paths as strings
    }

    # Mapping from dataType to Python type (when available)
    DATA_TYPE_TO_PYTHON_TYPE = {
        "String": str,
        "Integer": int,
        "Decimal": float,
        "Boolean": bool,
        "Date": str,
        "DateTime": str,
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
        if target_type == bool:
            if isinstance(value, str):
                return value.lower() in ("true", "yes", "1", "on")
            return bool(value)

        if target_type == list:
            if isinstance(value, str):
                # Assume comma-separated values for multi-select
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
        return python_type == str

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
            "status": custom_field.get("status"),
            "component": custom_field.get("component"),
        }
