"""Advanced validation for migration mappings.

This module provides comprehensive validation for migration mappings,
including field existence, type compatibility, strategy validation,
and business logic checks.
"""

import json
import os
import logging
from typing import Any, Dict, List, Optional, Tuple, Set, TYPE_CHECKING
from dataclasses import dataclass
from enum import Enum

from .base import MigrationMapping, MigrationStrategy
from .universal_field_manager import FieldType, FieldMetadata
from ..custom_field_validation import CustomFieldValidator

if TYPE_CHECKING:
    from .base import BaseMigrationManager

logger = logging.getLogger(__name__)


class ValidationSeverity(Enum):
    """Severity levels for validation issues."""

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class ValidationIssue:
    """Represents a validation issue."""

    severity: ValidationSeverity
    field_name: str
    issue_type: str
    message: str
    suggestion: Optional[str] = None
    context: Optional[Dict[str, Any]] = None


@dataclass
class MappingValidationResult:
    """Result of mapping validation."""

    is_valid: bool
    issues: List[ValidationIssue]
    warnings: List[str]
    suggestions: List[str]
    validated_mappings: List[MigrationMapping]

    def has_errors(self) -> bool:
        """Check if validation has any errors."""
        return any(issue.severity == ValidationSeverity.ERROR for issue in self.issues)

    def has_warnings(self) -> bool:
        """Check if validation has any warnings."""
        return any(
            issue.severity == ValidationSeverity.WARNING for issue in self.issues
        )

    def get_error_count(self) -> int:
        """Get count of error-level issues."""
        return sum(
            1 for issue in self.issues if issue.severity == ValidationSeverity.ERROR
        )

    def get_warning_count(self) -> int:
        """Get count of warning-level issues."""
        return sum(
            1 for issue in self.issues if issue.severity == ValidationSeverity.WARNING
        )


class MappingDictionaryValidator:
    """Comprehensive validator for migration mapping dictionaries."""

    def __init__(self, migration_manager: "BaseMigrationManager"):
        """Initialize the mapping validator.

        Args:
            migration_manager: The migration manager instance to validate against
        """
        self._migration_manager = migration_manager
        self._resource_type = migration_manager._resource_type
        self._logger = logging.getLogger(f"mapping_validator.{self._resource_type}")

        # Load field definitions
        self._field_definitions = self._load_field_definitions()

        # Cache for field metadata
        self._field_metadata_cache: Dict[str, FieldMetadata] = {}

    def validate_mapping_dictionary(
        self,
        mapping_dict: Dict[str, str],
        default_strategy: MigrationStrategy = MigrationStrategy.REPLACE,
        validate_field_existence: bool = True,
        validate_type_compatibility: bool = True,
        validate_business_logic: bool = True,
    ) -> MappingValidationResult:
        """Validate a mapping dictionary comprehensively.

        Args:
            mapping_dict: Dictionary mapping source fields to target fields
            default_strategy: Default migration strategy to use
            validate_field_existence: Whether to validate field existence
            validate_type_compatibility: Whether to validate type compatibility
            validate_business_logic: Whether to validate business logic

        Returns:
            MappingValidationResult with validation results
        """
        issues = []
        warnings = []
        suggestions = []
        validated_mappings = []

        self._logger.info(
            f"Validating mapping dictionary with {len(mapping_dict)} mappings"
        )

        for source_field, target_field in mapping_dict.items():
            # Create migration mapping
            mapping = MigrationMapping(
                source_field=source_field,
                target_field=target_field,
                strategy=default_strategy,
            )

            # Validate individual mapping
            mapping_issues = self._validate_single_mapping(
                mapping,
                validate_field_existence,
                validate_type_compatibility,
                validate_business_logic,
            )

            issues.extend(mapping_issues)
            validated_mappings.append(mapping)

        # Validate mapping set as a whole
        set_issues = self._validate_mapping_set(validated_mappings)
        issues.extend(set_issues)

        # Generate suggestions
        suggestions.extend(self._generate_suggestions(issues, validated_mappings))

        # Determine overall validity
        is_valid = not any(
            issue.severity == ValidationSeverity.ERROR for issue in issues
        )

        return MappingValidationResult(
            is_valid=is_valid,
            issues=issues,
            warnings=[
                issue.message
                for issue in issues
                if issue.severity == ValidationSeverity.WARNING
            ],
            suggestions=suggestions,
            validated_mappings=validated_mappings,
        )

    def validate_migration_mappings(
        self,
        mappings: List[MigrationMapping],
        validate_field_existence: bool = True,
        validate_type_compatibility: bool = True,
        validate_business_logic: bool = True,
    ) -> MappingValidationResult:
        """Validate a list of migration mappings.

        Args:
            mappings: List of migration mappings to validate
            validate_field_existence: Whether to validate field existence
            validate_type_compatibility: Whether to validate type compatibility
            validate_business_logic: Whether to validate business logic

        Returns:
            MappingValidationResult with validation results
        """
        issues = []
        suggestions = []

        self._logger.info(f"Validating {len(mappings)} migration mappings")

        for mapping in mappings:
            mapping_issues = self._validate_single_mapping(
                mapping,
                validate_field_existence,
                validate_type_compatibility,
                validate_business_logic,
            )
            issues.extend(mapping_issues)

        # Validate mapping set as a whole
        set_issues = self._validate_mapping_set(mappings)
        issues.extend(set_issues)

        # Generate suggestions
        suggestions.extend(self._generate_suggestions(issues, mappings))

        # Determine overall validity
        is_valid = not any(
            issue.severity == ValidationSeverity.ERROR for issue in issues
        )

        return MappingValidationResult(
            is_valid=is_valid,
            issues=issues,
            warnings=[
                issue.message
                for issue in issues
                if issue.severity == ValidationSeverity.WARNING
            ],
            suggestions=suggestions,
            validated_mappings=mappings,
        )

    def _validate_single_mapping(
        self,
        mapping: MigrationMapping,
        validate_field_existence: bool,
        validate_type_compatibility: bool,
        validate_business_logic: bool,
    ) -> List[ValidationIssue]:
        """Validate a single migration mapping."""
        issues = []

        # Field existence validation
        if validate_field_existence:
            issues.extend(self._validate_field_existence(mapping))

        # Type compatibility validation
        if validate_type_compatibility:
            issues.extend(self._validate_type_compatibility(mapping))

        # Strategy validation
        issues.extend(self._validate_strategy(mapping))

        # Business logic validation
        if validate_business_logic:
            issues.extend(self._validate_business_logic(mapping))

        return issues

    def _validate_field_existence(
        self, mapping: MigrationMapping
    ) -> List[ValidationIssue]:
        """Validate that source and target fields exist."""
        issues = []

        # Check source field
        source_metadata = self._get_field_metadata(mapping.source_field)
        if not source_metadata:
            issues.append(
                ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    field_name=mapping.source_field,
                    issue_type="field_not_found",
                    message=f"Source field '{mapping.source_field}' does not exist",
                    suggestion=f"Check field name spelling or create custom field '{mapping.source_field}'",
                )
            )

        # Check target field
        target_metadata = self._get_field_metadata(mapping.target_field)
        if not target_metadata:
            issues.append(
                ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    field_name=mapping.target_field,
                    issue_type="field_not_found",
                    message=f"Target field '{mapping.target_field}' does not exist",
                    suggestion=f"Check field name spelling or create custom field '{mapping.target_field}'",
                )
            )

        return issues

    def _validate_type_compatibility(
        self, mapping: MigrationMapping
    ) -> List[ValidationIssue]:
        """Validate that source and target field types are compatible."""
        issues = []

        source_metadata = self._get_field_metadata(mapping.source_field)
        target_metadata = self._get_field_metadata(mapping.target_field)

        if not source_metadata or not target_metadata:
            return issues  # Field existence issues will be caught elsewhere

        # Check basic type compatibility
        compatibility_issues = self._check_type_compatibility(
            source_metadata, target_metadata, mapping.strategy
        )
        issues.extend(compatibility_issues)

        # Check multi-value compatibility
        if source_metadata.is_multi_value != target_metadata.is_multi_value:
            if mapping.strategy != MigrationStrategy.TRANSFORM:
                issues.append(
                    ValidationIssue(
                        severity=ValidationSeverity.WARNING,
                        field_name=f"{mapping.source_field} -> {mapping.target_field}",
                        issue_type="multi_value_mismatch",
                        message=f"Multi-value mismatch: {mapping.source_field} ({'multi' if source_metadata.is_multi_value else 'single'}) -> {mapping.target_field} ({'multi' if target_metadata.is_multi_value else 'single'})",
                        suggestion="Consider using TRANSFORM strategy with custom conversion function",
                    )
                )

        return issues

    def _validate_strategy(self, mapping: MigrationMapping) -> List[ValidationIssue]:
        """Validate the migration strategy for the mapping."""
        issues = []

        target_metadata = self._get_field_metadata(mapping.target_field)
        if not target_metadata:
            return issues

        # Validate strategy appropriateness
        if mapping.strategy == MigrationStrategy.ADD_OPTION:
            if not target_metadata.is_multi_value:
                issues.append(
                    ValidationIssue(
                        severity=ValidationSeverity.WARNING,
                        field_name=mapping.target_field,
                        issue_type="strategy_mismatch",
                        message=f"ADD_OPTION strategy used on single-value field '{mapping.target_field}'",
                        suggestion="Consider using REPLACE or MERGE strategy for single-value fields",
                    )
                )

        # Validate TRANSFORM strategy
        if mapping.strategy == MigrationStrategy.TRANSFORM:
            if not mapping.transform_function:
                issues.append(
                    ValidationIssue(
                        severity=ValidationSeverity.ERROR,
                        field_name=f"{mapping.source_field} -> {mapping.target_field}",
                        issue_type="missing_transform_function",
                        message="TRANSFORM strategy requires a transform_function",
                        suggestion="Provide a transform_function or use a different strategy",
                    )
                )

        return issues

    def _validate_business_logic(
        self, mapping: MigrationMapping
    ) -> List[ValidationIssue]:
        """Validate business logic rules for the mapping."""
        issues = []

        source_metadata = self._get_field_metadata(mapping.source_field)
        target_metadata = self._get_field_metadata(mapping.target_field)

        if not source_metadata or not target_metadata:
            return issues

        # Check for self-mapping
        if mapping.source_field == mapping.target_field:
            issues.append(
                ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    field_name=mapping.source_field,
                    issue_type="self_mapping",
                    message=f"Field '{mapping.source_field}' maps to itself",
                    suggestion="Self-mappings are usually unnecessary unless using TRANSFORM strategy",
                )
            )

        # Check for required field overwrites
        if (
            target_metadata.is_required
            and mapping.strategy == MigrationStrategy.REPLACE
        ):
            issues.append(
                ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    field_name=mapping.target_field,
                    issue_type="required_field_overwrite",
                    message=f"Required field '{mapping.target_field}' will be overwritten",
                    suggestion="Consider using MERGE or COPY_IF_EMPTY strategy for required fields",
                )
            )

        # Check for standard field migrations
        if (
            source_metadata.field_type == FieldType.STANDARD
            and target_metadata.field_type == FieldType.CUSTOM
        ):
            issues.append(
                ValidationIssue(
                    severity=ValidationSeverity.INFO,
                    field_name=f"{mapping.source_field} -> {mapping.target_field}",
                    issue_type="standard_to_custom",
                    message=f"Migrating from standard field '{mapping.source_field}' to custom field '{mapping.target_field}'",
                    suggestion="Ensure this migration aligns with your data organization strategy",
                )
            )

        return issues

    def _validate_mapping_set(
        self, mappings: List[MigrationMapping]
    ) -> List[ValidationIssue]:
        """Validate the mapping set as a whole."""
        issues = []

        # Check for duplicate targets
        target_counts = {}
        for mapping in mappings:
            target_counts[mapping.target_field] = (
                target_counts.get(mapping.target_field, 0) + 1
            )

        for target_field, count in target_counts.items():
            if count > 1:
                issues.append(
                    ValidationIssue(
                        severity=ValidationSeverity.WARNING,
                        field_name=target_field,
                        issue_type="duplicate_target",
                        message=f"Target field '{target_field}' is used in {count} mappings",
                        suggestion="Consider using MERGE strategy or separate target fields",
                    )
                )

        # Check for circular mappings
        circular_chains = self._detect_circular_mappings(mappings)
        for chain in circular_chains:
            issues.append(
                ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    field_name=" -> ".join(chain),
                    issue_type="circular_mapping",
                    message=f"Circular mapping detected: {' -> '.join(chain)}",
                    suggestion="Remove circular dependencies in your mapping configuration",
                )
            )

        return issues

    def _check_type_compatibility(
        self,
        source_metadata: FieldMetadata,
        target_metadata: FieldMetadata,
        strategy: MigrationStrategy,
    ) -> List[ValidationIssue]:
        """Check type compatibility between source and target fields."""
        issues = []

        # Define type compatibility matrix
        compatible_types = {
            "text": ["text", "email", "phone", "unknown"],
            "email": ["text", "email"],
            "phone": ["text", "phone"],
            "number": ["number", "currency", "text"],
            "currency": ["number", "currency", "text"],
            "date": ["date", "text"],
            "boolean": ["boolean", "text"],
            "enum": ["enum", "text"],
            "unknown": ["text", "unknown"],
        }

        source_type = source_metadata.data_type.lower()
        target_type = target_metadata.data_type.lower()

        # Get compatible types for source
        source_compatible = compatible_types.get(source_type, ["text"])

        if target_type not in source_compatible:
            severity = ValidationSeverity.WARNING
            if strategy == MigrationStrategy.REPLACE:
                severity = ValidationSeverity.ERROR

            issues.append(
                ValidationIssue(
                    severity=severity,
                    field_name=f"{source_metadata.name} -> {target_metadata.name}",
                    issue_type="type_incompatibility",
                    message=f"Type mismatch: {source_type} -> {target_type}",
                    suggestion="Consider using TRANSFORM strategy with type conversion function",
                )
            )

        return issues

    def _detect_circular_mappings(
        self, mappings: List[MigrationMapping]
    ) -> List[List[str]]:
        """Detect circular mapping dependencies."""
        # Build mapping graph
        graph = {}
        for mapping in mappings:
            if mapping.source_field not in graph:
                graph[mapping.source_field] = []
            graph[mapping.source_field].append(mapping.target_field)

        # Detect cycles using DFS
        visited = set()
        rec_stack = set()
        cycles = []

        def dfs(node, path):
            if node in rec_stack:
                # Found cycle
                cycle_start = path.index(node)
                cycles.append(path[cycle_start:] + [node])
                return

            if node in visited:
                return

            visited.add(node)
            rec_stack.add(node)

            if node in graph:
                for neighbor in graph[node]:
                    dfs(neighbor, path + [neighbor])

            rec_stack.remove(node)

        for node in graph:
            if node not in visited:
                dfs(node, [node])

        return cycles

    def _generate_suggestions(
        self, issues: List[ValidationIssue], mappings: List[MigrationMapping]
    ) -> List[str]:
        """Generate general suggestions based on validation issues."""
        suggestions = []

        error_count = sum(
            1 for issue in issues if issue.severity == ValidationSeverity.ERROR
        )
        warning_count = sum(
            1 for issue in issues if issue.severity == ValidationSeverity.WARNING
        )

        if error_count > 0:
            suggestions.append(
                f"Fix {error_count} error(s) before proceeding with migration"
            )

        if warning_count > 0:
            suggestions.append(
                f"Review {warning_count} warning(s) to ensure expected behavior"
            )

        # Strategy suggestions
        transform_needed = any(
            issue.issue_type in ["type_incompatibility", "multi_value_mismatch"]
            for issue in issues
        )
        if transform_needed:
            suggestions.append(
                "Consider using TRANSFORM strategy for type or structure conversions"
            )

        # Field creation suggestions
        missing_fields = [
            issue.field_name
            for issue in issues
            if issue.issue_type == "field_not_found"
        ]
        if missing_fields:
            suggestions.append(
                f"Create missing fields: {', '.join(set(missing_fields))}"
            )

        return suggestions

    def _get_field_metadata(self, field_name: str) -> Optional[FieldMetadata]:
        """Get field metadata with caching."""
        if field_name in self._field_metadata_cache:
            return self._field_metadata_cache[field_name]

        metadata = self._migration_manager.get_universal_field_metadata(field_name)
        if metadata:
            self._field_metadata_cache[field_name] = metadata

        return metadata

    def _load_field_definitions(self) -> Dict[str, Any]:
        """Load field definitions from JSON file."""
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            sdk_root = os.path.dirname(os.path.dirname(current_dir))
            field_def_path = os.path.join(
                sdk_root, "src", "neon_crm", "field_definitions.json"
            )

            with open(field_def_path) as f:
                return json.load(f)
        except Exception as e:
            self._logger.warning(f"Could not load field definitions: {e}")
            return {}

    def suggest_field_mappings(
        self, source_fields: List[str], target_pattern: Optional[str] = None
    ) -> Dict[str, List[str]]:
        """Suggest target fields for source fields based on similarity.

        Args:
            source_fields: List of source field names
            target_pattern: Optional pattern to filter target fields

        Returns:
            Dictionary mapping source fields to suggested target fields
        """
        suggestions = {}

        # Get all available fields
        all_fields = self._migration_manager.list_all_universal_fields()

        # Filter target fields by pattern if provided
        if target_pattern:
            target_fields = self._migration_manager.find_universal_fields_by_pattern(
                target_pattern
            )
        else:
            target_fields = all_fields

        target_names = [f.name for f in target_fields]

        for source_field in source_fields:
            # Find similar field names
            similar_fields = self._find_similar_fields(source_field, target_names)
            suggestions[source_field] = similar_fields[:3]  # Top 3 suggestions

        return suggestions

    def _find_similar_fields(
        self, source_field: str, target_fields: List[str]
    ) -> List[str]:
        """Find fields similar to the source field."""
        similar = []

        source_lower = source_field.lower()
        source_words = source_lower.replace("-", " ").replace("_", " ").split()

        for target_field in target_fields:
            if target_field == source_field:
                continue  # Skip self

            target_lower = target_field.lower()
            target_words = target_lower.replace("-", " ").replace("_", " ").split()

            # Calculate similarity score
            score = 0

            # Exact match bonus
            if source_lower == target_lower:
                score += 100

            # Contains all words bonus
            if all(word in target_lower for word in source_words):
                score += 50

            # Word overlap bonus
            common_words = set(source_words) & set(target_words)
            score += len(common_words) * 10

            # Substring bonus
            if source_lower in target_lower or target_lower in source_lower:
                score += 20

            if score > 0:
                similar.append((target_field, score))

        # Sort by score and return field names
        similar.sort(key=lambda x: x[1], reverse=True)
        return [field for field, score in similar]
