"""Advanced validation system for Neon CRM custom fields.

This module provides comprehensive validation for custom field values,
including type checking, range validation, and business rule validation.
"""

from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
import re

from .custom_field_types import CustomFieldTypeMapper


@dataclass
class ValidationError:
    """Represents a validation error."""

    field_name: str
    error_type: str
    message: str
    severity: str = "error"  # error, warning, info


@dataclass
class ValidationResult:
    """Comprehensive validation result."""

    is_valid: bool
    errors: List[ValidationError]
    warnings: List[ValidationError]
    field_info: Optional[Dict[str, Any]] = None

    def __bool__(self) -> bool:
        """Allow using ValidationResult in boolean context."""
        return self.is_valid

    @property
    def all_issues(self) -> List[ValidationError]:
        """Get all issues (errors and warnings) combined."""
        return self.errors + self.warnings

    def has_errors(self) -> bool:
        """Check if there are any errors."""
        return len(self.errors) > 0

    def has_warnings(self) -> bool:
        """Check if there are any warnings."""
        return len(self.warnings) > 0


class CustomFieldValidator:
    """Advanced validator for custom field values."""

    # Email regex pattern
    EMAIL_PATTERN = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")

    # URL regex pattern
    URL_PATTERN = re.compile(
        r"^https?://"  # http:// or https://
        r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|"  # domain
        r"localhost|"  # localhost
        r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"  # IP
        r"(?::\d+)?"  # optional port
        r"(?:/?|[/?]\S+)$",
        re.IGNORECASE,
    )

    # Phone regex patterns (flexible)
    PHONE_PATTERNS = [
        re.compile(
            r"^\+?1?[-.\s]?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})$"
        ),  # US format
        re.compile(r"^\+?[1-9]\d{1,14}$"),  # International format (E.164)
        re.compile(r"^[0-9\-\.\s\(\)\+]+$"),  # Flexible format
    ]

    @classmethod
    def validate_field_value(
        cls, value: Any, field_metadata: Dict[str, Any]
    ) -> ValidationResult:
        """Validate a custom field value comprehensively.

        Args:
            value: Value to validate
            field_metadata: Custom field metadata from API

        Returns:
            ValidationResult with detailed validation information
        """
        field_name = field_metadata.get("name", "unknown")
        display_type = field_metadata.get("displayType", "")

        errors = []
        warnings = []

        # Basic null/empty validation
        if value is None or value == "":
            # Check if field is required (this would need to be in metadata)
            required = field_metadata.get("required", False)
            if required:
                errors.append(
                    ValidationError(
                        field_name,
                        "required",
                        f"Field '{field_name}' is required but was empty",
                    )
                )
            # Empty values are generally valid for optional fields
            return ValidationResult(len(errors) == 0, errors, warnings, field_metadata)

        # Type-specific validation
        try:
            if display_type in ("OneLineText", "MultiLineText", "Text"):
                cls._validate_text_field(value, field_metadata, errors, warnings)
            elif display_type == "Email":
                cls._validate_email_field(value, field_metadata, errors, warnings)
            elif display_type == "URL":
                cls._validate_url_field(value, field_metadata, errors, warnings)
            elif display_type == "Phone":
                cls._validate_phone_field(value, field_metadata, errors, warnings)
            elif display_type in ("Number", "Currency", "Percentage"):
                cls._validate_numeric_field(value, field_metadata, errors, warnings)
            elif display_type in ("Date", "DateTime", "Time"):
                cls._validate_datetime_field(value, field_metadata, errors, warnings)
            elif display_type == "YesNo":
                cls._validate_boolean_field(value, field_metadata, errors, warnings)
            elif display_type in ("Checkbox", "MultiSelect"):
                cls._validate_multivalue_field(value, field_metadata, errors, warnings)
            elif display_type in ("DropDown", "Dropdown", "RadioButton", "Radio"):
                cls._validate_single_select_field(
                    value, field_metadata, errors, warnings
                )
            elif display_type in ("File", "Image"):
                cls._validate_file_field(value, field_metadata, errors, warnings)
            elif display_type == "Account":
                cls._validate_account_field(value, field_metadata, errors, warnings)
            else:
                warnings.append(
                    ValidationError(
                        field_name,
                        "unknown_type",
                        f"Unknown field type '{display_type}' - basic validation only",
                        "warning",
                    )
                )

        except Exception as e:
            errors.append(
                ValidationError(
                    field_name, "validation_error", f"Validation error: {str(e)}"
                )
            )

        return ValidationResult(len(errors) == 0, errors, warnings, field_metadata)

    @classmethod
    def _validate_text_field(
        cls, value: Any, field_metadata: Dict[str, Any], errors: List, warnings: List
    ):
        """Validate text fields."""
        field_name = field_metadata.get("name", "unknown")

        # Convert to string
        str_value = str(value)

        # Length validation (reasonable defaults)
        max_length = field_metadata.get("maxLength", 10000)  # Default max length
        if len(str_value) > max_length:
            errors.append(
                ValidationError(
                    field_name,
                    "max_length",
                    f"Text exceeds maximum length of {max_length} characters",
                )
            )

        # Check for potentially problematic characters
        if any(ord(c) < 32 and c not in "\t\n\r" for c in str_value):
            warnings.append(
                ValidationError(
                    field_name,
                    "control_chars",
                    "Text contains control characters that may cause display issues",
                    "warning",
                )
            )

    @classmethod
    def _validate_email_field(
        cls, value: Any, field_metadata: Dict[str, Any], errors: List, warnings: List
    ):
        """Validate email fields."""
        field_name = field_metadata.get("name", "unknown")
        email_str = str(value).strip()

        if not cls.EMAIL_PATTERN.match(email_str):
            errors.append(
                ValidationError(
                    field_name,
                    "invalid_format",
                    f"'{email_str}' is not a valid email address",
                )
            )

        # Additional checks
        if len(email_str) > 254:  # RFC 5321 limit
            errors.append(
                ValidationError(
                    field_name,
                    "too_long",
                    "Email address exceeds maximum length of 254 characters",
                )
            )

    @classmethod
    def _validate_url_field(
        cls, value: Any, field_metadata: Dict[str, Any], errors: List, warnings: List
    ):
        """Validate URL fields."""
        field_name = field_metadata.get("name", "unknown")
        url_str = str(value).strip()

        if not cls.URL_PATTERN.match(url_str):
            errors.append(
                ValidationError(
                    field_name, "invalid_format", f"'{url_str}' is not a valid URL"
                )
            )

        if len(url_str) > 2000:  # Reasonable URL length limit
            warnings.append(
                ValidationError(
                    field_name,
                    "very_long",
                    "URL is very long and may cause issues in some contexts",
                    "warning",
                )
            )

    @classmethod
    def _validate_phone_field(
        cls, value: Any, field_metadata: Dict[str, Any], errors: List, warnings: List
    ):
        """Validate phone number fields."""
        field_name = field_metadata.get("name", "unknown")
        phone_str = str(value).strip()

        # Try to match any of the phone patterns
        valid_format = any(pattern.match(phone_str) for pattern in cls.PHONE_PATTERNS)

        if not valid_format:
            errors.append(
                ValidationError(
                    field_name,
                    "invalid_format",
                    f"'{phone_str}' is not a valid phone number format",
                )
            )

    @classmethod
    def _validate_numeric_field(
        cls, value: Any, field_metadata: Dict[str, Any], errors: List, warnings: List
    ):
        """Validate numeric fields."""
        field_name = field_metadata.get("name", "unknown")
        display_type = field_metadata.get("displayType", "")

        try:
            if isinstance(value, str):
                # Remove common formatting characters
                cleaned_value = (
                    value.replace(",", "").replace("$", "").replace("%", "").strip()
                )
                numeric_value = float(cleaned_value)
            else:
                numeric_value = float(value)
        except (ValueError, TypeError):
            errors.append(
                ValidationError(
                    field_name, "invalid_format", f"'{value}' is not a valid number"
                )
            )
            return

        # Range validation for specific types
        if display_type == "Percentage":
            if numeric_value < 0 or numeric_value > 100:
                warnings.append(
                    ValidationError(
                        field_name,
                        "range_warning",
                        f"Percentage value {numeric_value} is outside typical range (0-100)",
                        "warning",
                    )
                )

        if display_type == "Currency" and numeric_value < 0:
            warnings.append(
                ValidationError(
                    field_name,
                    "negative_currency",
                    "Negative currency amounts may indicate data entry errors",
                    "warning",
                )
            )

    @classmethod
    def _validate_datetime_field(
        cls, value: Any, field_metadata: Dict[str, Any], errors: List, warnings: List
    ):
        """Validate date/time fields."""
        field_name = field_metadata.get("name", "unknown")
        display_type = field_metadata.get("displayType", "")

        if isinstance(value, datetime):
            # Already a datetime object
            return

        # Try to parse string dates
        str_value = str(value).strip()
        formats_to_try = [
            "%Y-%m-%d",  # 2023-12-25
            "%Y-%m-%dT%H:%M:%S",  # 2023-12-25T15:30:00
            "%Y-%m-%d %H:%M:%S",  # 2023-12-25 15:30:00
            "%m/%d/%Y",  # 12/25/2023
            "%d/%m/%Y",  # 25/12/2023
            "%H:%M:%S",  # 15:30:00 (time only)
            "%H:%M",  # 15:30 (time only)
        ]

        parsed_date = None
        for fmt in formats_to_try:
            try:
                parsed_date = datetime.strptime(str_value, fmt)
                break
            except ValueError:
                continue

        if parsed_date is None:
            errors.append(
                ValidationError(
                    field_name,
                    "invalid_format",
                    f"'{str_value}' is not a valid {display_type.lower()} format",
                )
            )
        else:
            # Additional date validation
            if display_type == "Date" and parsed_date.year < 1900:
                warnings.append(
                    ValidationError(
                        field_name,
                        "old_date",
                        f"Date {str_value} is very old and may be a data entry error",
                        "warning",
                    )
                )

    @classmethod
    def _validate_boolean_field(
        cls, value: Any, field_metadata: Dict[str, Any], errors: List, warnings: List
    ):
        """Validate boolean fields."""
        field_name = field_metadata.get("name", "unknown")

        valid_boolean_values = [
            True,
            False,
            "true",
            "false",
            "True",
            "False",
            "yes",
            "no",
            "Yes",
            "No",
            1,
            0,
            "1",
            "0",
        ]

        if value not in valid_boolean_values:
            errors.append(
                ValidationError(
                    field_name,
                    "invalid_format",
                    f"'{value}' is not a valid boolean value",
                )
            )

    @classmethod
    def _validate_multivalue_field(
        cls, value: Any, field_metadata: Dict[str, Any], errors: List, warnings: List
    ):
        """Validate multi-value fields (Checkbox, MultiSelect)."""
        field_name = field_metadata.get("name", "unknown")

        # Parse value into list
        if isinstance(value, str):
            parsed_values = CustomFieldTypeMapper.parse_multivalue_string(value)
        elif isinstance(value, list):
            parsed_values = [str(v) for v in value]
        else:
            parsed_values = [str(value)]

        # Validate against available options
        available_options = field_metadata.get("optionValues", [])
        if available_options:
            available_names = {opt.get("name", "") for opt in available_options}
            invalid_options = [v for v in parsed_values if v not in available_names]

            if invalid_options:
                errors.append(
                    ValidationError(
                        field_name,
                        "invalid_options",
                        f"Invalid options: {', '.join(invalid_options)}. Valid options: {', '.join(sorted(available_names))}",
                    )
                )

        # Check for duplicates
        if len(parsed_values) != len(set(parsed_values)):
            warnings.append(
                ValidationError(
                    field_name,
                    "duplicates",
                    "Duplicate values detected in multi-value field",
                    "warning",
                )
            )

    @classmethod
    def _validate_single_select_field(
        cls, value: Any, field_metadata: Dict[str, Any], errors: List, warnings: List
    ):
        """Validate single selection fields (DropDown, RadioButton)."""
        field_name = field_metadata.get("name", "unknown")
        str_value = str(value).strip()

        # Validate against available options
        available_options = field_metadata.get("optionValues", [])
        if available_options:
            available_names = {opt.get("name", "") for opt in available_options}
            if str_value not in available_names:
                errors.append(
                    ValidationError(
                        field_name,
                        "invalid_option",
                        f"'{str_value}' is not a valid option. Valid options: {', '.join(sorted(available_names))}",
                    )
                )

    @classmethod
    def _validate_file_field(
        cls, value: Any, field_metadata: Dict[str, Any], errors: List, warnings: List
    ):
        """Validate file fields."""
        field_name = field_metadata.get("name", "unknown")

        # For now, just validate it's a string (URL or path)
        if not isinstance(value, str):
            errors.append(
                ValidationError(
                    field_name,
                    "invalid_type",
                    "File field value must be a string (URL or file path)",
                )
            )

    @classmethod
    def _validate_account_field(
        cls, value: Any, field_metadata: Dict[str, Any], errors: List, warnings: List
    ):
        """Validate account lookup fields."""
        field_name = field_metadata.get("name", "unknown")

        # Account fields should contain account IDs
        try:
            int(value)  # Should be convertible to integer
        except (ValueError, TypeError):
            errors.append(
                ValidationError(
                    field_name,
                    "invalid_format",
                    f"Account field value '{value}' must be a valid account ID (integer)",
                )
            )

    @classmethod
    def validate_multiple_fields(
        cls, field_values: Dict[str, Any], field_metadata_list: List[Dict[str, Any]]
    ) -> Dict[str, ValidationResult]:
        """Validate multiple fields at once.

        Args:
            field_values: Dictionary mapping field names to values
            field_metadata_list: List of field metadata dictionaries

        Returns:
            Dictionary mapping field names to ValidationResult objects
        """
        # Create metadata lookup
        metadata_by_name = {meta.get("name"): meta for meta in field_metadata_list}

        results = {}
        for field_name, value in field_values.items():
            field_metadata = metadata_by_name.get(field_name)
            if field_metadata:
                results[field_name] = cls.validate_field_value(value, field_metadata)
            else:
                results[field_name] = ValidationResult(
                    False,
                    [
                        ValidationError(
                            field_name,
                            "field_not_found",
                            f"Field '{field_name}' not found",
                        )
                    ],
                    [],
                )

        return results

    @classmethod
    def get_validation_summary(
        cls, results: Dict[str, ValidationResult]
    ) -> Dict[str, Any]:
        """Get a summary of validation results.

        Args:
            results: Dictionary of field validation results

        Returns:
            Summary dictionary with statistics and issues
        """
        total_fields = len(results)
        valid_fields = sum(1 for r in results.values() if r.is_valid)
        total_errors = sum(len(r.errors) for r in results.values())
        total_warnings = sum(len(r.warnings) for r in results.values())

        all_errors = []
        all_warnings = []

        for field_name, result in results.items():
            all_errors.extend(result.errors)
            all_warnings.extend(result.warnings)

        return {
            "total_fields": total_fields,
            "valid_fields": valid_fields,
            "invalid_fields": total_fields - valid_fields,
            "total_errors": total_errors,
            "total_warnings": total_warnings,
            "all_errors": all_errors,
            "all_warnings": all_warnings,
            "overall_valid": total_errors == 0,
        }
