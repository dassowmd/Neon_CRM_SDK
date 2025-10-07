"""Base migration tools for Neon CRM custom fields.

This module provides the foundational classes and functionality for resource-specific
migration managers.
"""

from typing import Any, Dict, List, Optional, Union, Callable, Iterator, TYPE_CHECKING
from dataclasses import dataclass
from enum import Enum
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

from ..custom_field_manager import (
    CustomFieldValueManager,
    BatchResult,
)
from ..custom_field_validation import CustomFieldValidator, ValidationResult
from ..custom_field_types import CustomFieldTypeMapper

if TYPE_CHECKING:
    from ..client import NeonClient


class MigrationStrategy(Enum):
    """Migration strategies for field data."""

    REPLACE = "replace"  # Replace target field value entirely
    MERGE = "merge"  # Merge with existing target field value
    ADD_OPTION = "add_option"  # Add to multi-value field
    COPY_IF_EMPTY = "copy_if_empty"  # Only copy if target is empty
    TRANSFORM = "transform"  # Apply custom transformation function


@dataclass
class MigrationMapping:
    """Defines how to migrate from one field to another."""

    source_field: str
    target_field: str
    strategy: MigrationStrategy
    transform_function: Optional[Callable[[Any], Any]] = None
    validation_required: bool = True
    preserve_source: bool = True  # Whether to keep the source field after migration


@dataclass
class MigrationPlan:
    """Represents a complete migration plan."""

    mappings: List[MigrationMapping]
    resource_filter: Optional[Dict[str, Any]] = (
        None  # Filter which resources to migrate
    )
    batch_size: int = 100
    max_workers: int = 5
    dry_run: bool = True


@dataclass
class MigrationResult:
    """Result of a migration operation."""

    total_resources: int
    successful_migrations: int
    failed_migrations: int
    skipped_migrations: int
    errors: List[str]
    warnings: List[str]
    detailed_results: Dict[str, Any]


@dataclass
class ConflictReport:
    """Report of migration conflicts."""

    field_conflicts: Dict[str, List[str]]
    type_conflicts: Dict[str, Dict[str, str]]
    value_conflicts: Dict[str, List[Dict[str, Any]]]
    resolution_suggestions: List[str]


class BaseMigrationManager:
    """Base class for resource-specific migration managers."""

    def __init__(self, resource, client: "NeonClient", resource_type: str):
        """Initialize the base migration manager.

        Args:
            resource: The resource instance (e.g., client.accounts)
            client: Neon CRM client instance
            resource_type: Type of resource (accounts, donations, etc.)
        """
        self._resource = resource
        self._client = client
        self._resource_type = resource_type
        self._value_manager = CustomFieldValueManager(client, resource_type)
        self._logger = logging.getLogger(f"migration.{resource_type}")

    def analyze_migration_conflicts(
        self, migration_plan: MigrationPlan
    ) -> ConflictReport:
        """Analyze potential conflicts in a migration plan.

        Args:
            migration_plan: Migration plan to analyze

        Returns:
            ConflictReport with detected conflicts and suggestions
        """
        field_conflicts = self._check_field_existence_conflicts(migration_plan.mappings)
        type_conflicts, suggestions = self._check_type_compatibility_conflicts(
            migration_plan.mappings
        )
        value_conflicts = self._check_value_conflicts(migration_plan)

        return ConflictReport(
            field_conflicts, type_conflicts, value_conflicts, suggestions
        )

    def execute_migration_plan(self, migration_plan: MigrationPlan) -> MigrationResult:
        """Execute a complete migration plan using mapping-first approach.

        Args:
            migration_plan: Migration plan to execute

        Returns:
            MigrationResult with execution statistics and details
        """
        self._logger.info(
            f"Starting migration plan execution (dry_run={migration_plan.dry_run})"
        )

        # New approach: iterate through mappings first, then find relevant resources
        execution_stats = self._execute_mapping_first_migration(migration_plan)
        detailed_results = self._create_detailed_results(
            migration_plan, execution_stats
        )

        return MigrationResult(
            execution_stats["total_resources"],
            execution_stats["successful"],
            execution_stats["failed"],
            execution_stats["skipped"],
            execution_stats["errors"],
            execution_stats["warnings"],
            detailed_results,
        )

    def _execute_mapping_first_migration(
        self, migration_plan: MigrationPlan
    ) -> Dict[str, Any]:
        """Execute migration by iterating through mappings first, then finding relevant resources.

        This is more efficient because it only processes resources that have data to migrate.
        """
        total_resources = 0
        successful = 0
        failed = 0
        skipped = 0
        errors = []
        warnings = []

        for mapping in migration_plan.mappings:
            self._logger.info(
                f"Processing mapping: {mapping.source_field} -> {mapping.target_field}"
            )

            # Find resources that have data in the source field
            resources_with_data = self._find_resources_with_source_data(
                mapping.source_field, migration_plan.resource_filter
            )

            mapping_stats = self._execute_mapping_on_resources(
                mapping, resources_with_data, migration_plan.dry_run
            )

            total_resources += mapping_stats["processed"]
            successful += mapping_stats["successful"]
            failed += mapping_stats["failed"]
            skipped += mapping_stats["skipped"]
            errors.extend(mapping_stats["errors"])
            warnings.extend(mapping_stats["warnings"])

            self._logger.info(
                f"Completed mapping {mapping.source_field}: "
                f"{mapping_stats['successful']} successful, {mapping_stats['failed']} failed"
            )

        return {
            "total_resources": total_resources,
            "successful": successful,
            "failed": failed,
            "skipped": skipped,
            "errors": errors,
            "warnings": warnings,
        }

    def create_migration_plan_from_mapping(
        self, field_mapping: Dict[str, Any]
    ) -> MigrationPlan:
        """Create a migration plan from field mapping configuration.

        Args:
            field_mapping: Dictionary mapping source fields to target field configurations

        Returns:
            MigrationPlan object
        """
        mappings = []

        for old_field, mapping_config in field_mapping.items():
            if mapping_config == "TODO":
                continue

            target_field = mapping_config["field"]

            if "option" in mapping_config:
                # This is mapping to a specific option in a multi-value field
                strategy = MigrationStrategy.ADD_OPTION

                # Create a transform function to extract the specific option
                option_value = mapping_config["option"]

                def transform_fn(source_value, opt=option_value):
                    # For option mappings, if source has ANY value, return the target option
                    if source_value is not None and str(source_value).strip():
                        return opt
                    return None  # Return actual None if source is empty

                mappings.append(
                    MigrationMapping(
                        source_field=old_field,
                        target_field=target_field,
                        strategy=strategy,
                        transform_function=transform_fn,
                    )
                )
            else:
                # Direct field-to-field migration
                strategy = MigrationStrategy.COPY_IF_EMPTY

                mappings.append(
                    MigrationMapping(
                        source_field=old_field,
                        target_field=target_field,
                        strategy=strategy,
                    )
                )

        return MigrationPlan(mappings=mappings, dry_run=True)

    def create_migration_plan_from_notebook_mapping(
        self, notebook_mapping: Dict[str, Any]
    ) -> MigrationPlan:
        """Create a migration plan from field mapping configuration.

        DEPRECATED: Use create_migration_plan_from_mapping() instead.
        This method name is kept for backward compatibility.

        Args:
            notebook_mapping: Dictionary mapping source fields to target field configurations

        Returns:
            MigrationPlan object
        """
        import warnings

        warnings.warn(
            "create_migration_plan_from_notebook_mapping is deprecated. "
            "Use create_migration_plan_from_mapping instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.create_migration_plan_from_mapping(notebook_mapping)

    def migrate_field_values(
        self,
        source_field: str,
        target_field: str,
        strategy: MigrationStrategy = MigrationStrategy.REPLACE,
        resource_filter: Optional[Dict[str, Any]] = None,
        transform_function: Optional[Callable[[Any], Any]] = None,
        dry_run: bool = True,
    ) -> MigrationResult:
        """Migrate values from one field to another.

        Args:
            source_field: Name of the source field
            target_field: Name of the target field
            strategy: Migration strategy to use
            resource_filter: Filter for which resources to migrate
            transform_function: Optional transformation to apply to values
            dry_run: Whether to perform a dry run

        Returns:
            MigrationResult with execution statistics
        """
        mapping = MigrationMapping(
            source_field=source_field,
            target_field=target_field,
            strategy=strategy,
            transform_function=transform_function,
        )

        plan = MigrationPlan(
            mappings=[mapping], resource_filter=resource_filter, dry_run=dry_run
        )

        return self.execute_migration_plan(plan)

    # Abstract methods to be implemented by subclasses
    def get_sample_resources(
        self, resource_filter: Dict[str, Any], limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get a small sample of resources for conflict analysis.

        This method should be implemented by each resource-specific manager
        to handle resource-specific parameters.
        """
        raise NotImplementedError("Subclasses must implement get_sample_resources")

    def get_resources_for_migration(
        self, config: Dict[str, Any]
    ) -> Iterator[Dict[str, Any]]:
        """Get resources that should be included in the migration.

        This method should be implemented by each resource-specific manager
        to handle resource-specific parameters.
        """
        raise NotImplementedError(
            "Subclasses must implement get_resources_for_migration"
        )

    def get_resource_id_field(self) -> str:
        """Get the field name used for resource IDs.

        This method should be implemented by each resource-specific manager
        to return the appropriate ID field name.
        """
        raise NotImplementedError("Subclasses must implement get_resource_id_field")

    def _find_resources_with_source_data(
        self, source_field: str, resource_filter: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Find resources that have data in the specified source field.

        This method should be implemented by each resource-specific manager
        to efficiently search for resources with data in specific fields.
        """
        raise NotImplementedError(
            "Subclasses must implement _find_resources_with_source_data"
        )

    def _execute_mapping_on_resources(
        self, mapping: MigrationMapping, resources: List[Dict[str, Any]], dry_run: bool
    ) -> Dict[str, Any]:
        """Execute a specific mapping on a list of resources.

        Returns:
            Dict with keys: processed, successful, failed, skipped, errors, warnings
        """
        processed = len(resources)
        successful = 0
        failed = 0
        skipped = 0
        errors = []
        warnings = []

        for resource in resources:
            resource_id = resource.get(self.get_resource_id_field())
            if not resource_id:
                skipped += 1
                continue

            try:
                success = self._execute_single_migration(resource_id, mapping, dry_run)
                if success:
                    successful += 1
                else:
                    failed += 1
            except Exception as e:
                failed += 1
                errors.append(
                    f"Error migrating {mapping.source_field} for resource {resource_id}: {str(e)}"
                )

        return {
            "processed": processed,
            "successful": successful,
            "failed": failed,
            "skipped": skipped,
            "errors": errors,
            "warnings": warnings,
        }

    # Shared implementation methods
    def _check_field_existence_conflicts(
        self, mappings: List[MigrationMapping]
    ) -> Dict[str, List[str]]:
        """Check for missing source or target fields."""
        field_conflicts = {}

        for mapping in mappings:
            source_field = self._resource.find_custom_field_by_name(
                mapping.source_field
            )
            target_field = self._resource.find_custom_field_by_name(
                mapping.target_field
            )

            if not source_field:
                field_conflicts.setdefault("missing_source", []).append(
                    mapping.source_field
                )

            if not target_field:
                field_conflicts.setdefault("missing_target", []).append(
                    mapping.target_field
                )

        return field_conflicts

    def _check_type_compatibility_conflicts(
        self, mappings: List[MigrationMapping]
    ) -> tuple[Dict[str, Dict[str, str]], List[str]]:
        """Check for type compatibility issues between source and target fields."""
        type_conflicts = {}
        suggestions = []

        for mapping in mappings:
            source_field = self._resource.find_custom_field_by_name(
                mapping.source_field
            )
            target_field = self._resource.find_custom_field_by_name(
                mapping.target_field
            )

            if not source_field or not target_field:
                continue

            source_type = source_field.get("displayType", "")
            target_type = target_field.get("displayType", "")

            if source_type != target_type:
                type_conflicts[f"{mapping.source_field} -> {mapping.target_field}"] = {
                    "source_type": source_type,
                    "target_type": target_type,
                }

                if source_type in ("OneLineText", "MultiLineText") and target_type in (
                    "Checkbox",
                    "MultiSelect",
                ):
                    suggestions.append(
                        f"Migration from {source_type} to {target_type} may require text parsing. "
                        f"Consider using a transform function for {mapping.source_field} -> {mapping.target_field}"
                    )

        return type_conflicts, suggestions

    def _check_value_conflicts(
        self, migration_plan: MigrationPlan
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Check for value conflicts in sample resources."""
        value_conflicts = {}

        if migration_plan.resource_filter:
            sample_resources = self.get_sample_resources(
                migration_plan.resource_filter, limit=10
            )
        else:
            sample_resources = self.get_sample_resources({}, limit=10)

        for resource in sample_resources:
            resource_id = resource.get(self.get_resource_id_field())
            if not resource_id:
                continue

            for mapping in migration_plan.mappings:
                source_value = self._value_manager.get_custom_field_value(
                    resource_id, mapping.source_field
                )
                target_value = self._value_manager.get_custom_field_value(
                    resource_id, mapping.target_field
                )

                if (
                    source_value
                    and target_value
                    and mapping.strategy == MigrationStrategy.REPLACE
                ):
                    conflict_key = f"{mapping.source_field} -> {mapping.target_field}"
                    value_conflicts.setdefault(conflict_key, []).append(
                        {
                            "resource_id": resource_id,
                            "source_value": source_value,
                            "target_value": target_value,
                        }
                    )

        return value_conflicts

    def _prepare_resources_for_migration(
        self, migration_plan: MigrationPlan
    ) -> List[Dict[str, Any]]:
        """Prepare and validate resources for migration."""
        config = {"resource_filter": migration_plan.resource_filter}
        return list(self.get_resources_for_migration(config))

    def _execute_migration_batches(
        self, migration_plan: MigrationPlan, resources: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Execute migration in batches and aggregate results."""
        successful = 0
        failed = 0
        skipped = 0
        errors = []
        warnings = []
        total_resources = len(resources)

        for batch_start in range(0, total_resources, migration_plan.batch_size):
            batch_end = min(batch_start + migration_plan.batch_size, total_resources)
            batch_resources = resources[batch_start:batch_end]

            batch_result = self._execute_migration_batch(
                batch_resources,
                migration_plan.mappings,
                migration_plan.dry_run,
                migration_plan.max_workers,
            )

            successful += batch_result.successful
            failed += batch_result.failed
            errors.extend(batch_result.errors)
            warnings.extend(batch_result.warnings)

            self._log_batch_completion(
                batch_start, migration_plan.batch_size, batch_result
            )

        return {
            "successful": successful,
            "failed": failed,
            "skipped": skipped,
            "errors": errors,
            "warnings": warnings,
        }

    def _execute_migration_batch(
        self,
        resources: List[Dict[str, Any]],
        mappings: List[MigrationMapping],
        dry_run: bool,
        max_workers: int,
    ) -> BatchResult:
        """Execute a batch of migrations with optional parallelization."""
        successful = 0
        failed = 0
        errors = []
        warnings = []

        def process_resource(resource):
            resource_id = resource.get(self.get_resource_id_field())
            resource_errors = []
            resource_successful = 0

            for mapping in mappings:
                try:
                    success = self._execute_single_migration(
                        resource_id, mapping, dry_run
                    )
                    if success:
                        resource_successful += 1
                    else:
                        resource_errors.append(
                            f"Failed migration {mapping.source_field} -> {mapping.target_field}"
                        )
                except Exception as e:
                    resource_errors.append(
                        f"Error in migration {mapping.source_field} -> {mapping.target_field}: {str(e)}"
                    )

            return resource_successful, resource_errors

        # Use ThreadPoolExecutor for parallel processing if max_workers > 1
        if max_workers > 1:
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_to_resource = {
                    executor.submit(process_resource, resource): resource
                    for resource in resources
                }

                for future in as_completed(future_to_resource):
                    try:
                        resource_successful, resource_errors = future.result()
                        if resource_errors:
                            failed += 1
                            errors.extend(resource_errors)
                        else:
                            successful += 1
                    except Exception as e:
                        failed += 1
                        errors.append(f"Thread execution error: {str(e)}")
        else:
            # Sequential processing
            for resource in resources:
                resource_successful, resource_errors = process_resource(resource)
                if resource_errors:
                    failed += 1
                    errors.extend(resource_errors)
                else:
                    successful += 1

        return BatchResult(successful, failed, errors, warnings)

    def _execute_single_migration(
        self, resource_id: Union[int, str], mapping: MigrationMapping, dry_run: bool
    ) -> bool:
        """Execute a single field migration."""
        try:
            source_value = self._get_and_validate_source_value(resource_id, mapping)

            # For ADD_OPTION strategy, always try to apply transformation even if source is None
            if mapping.strategy == MigrationStrategy.ADD_OPTION:
                transformed_value = self._apply_transformation(source_value, mapping)
                if transformed_value is None:
                    return False  # Skip if transform says to skip
            else:
                # For other strategies, skip if no source value
                if source_value is None:
                    return False
                transformed_value = self._apply_transformation(source_value, mapping)

            if not self._validate_transformed_value(transformed_value, mapping):
                return False

            if dry_run:
                return True

            return self._execute_migration_strategy(
                resource_id, mapping, transformed_value
            )

        except Exception:
            return False

    def _get_and_validate_source_value(
        self, resource_id: Union[int, str], mapping: MigrationMapping
    ) -> Optional[Any]:
        """Get source value and validate it exists."""
        source_value = self._value_manager.get_custom_field_value(
            resource_id, mapping.source_field
        )
        return source_value if source_value is not None else None

    def _apply_transformation(
        self, source_value: Any, mapping: MigrationMapping
    ) -> Any:
        """Apply transformation function if provided."""
        if mapping.transform_function:
            return mapping.transform_function(source_value)
        return source_value

    def _validate_transformed_value(
        self, transformed_value: Any, mapping: MigrationMapping
    ) -> bool:
        """Validate the transformed value if validation is required."""
        if not mapping.validation_required:
            return True

        field_metadata = self._resource.find_custom_field_by_name(mapping.target_field)
        if not field_metadata:
            return True

        validation = CustomFieldValidator.validate_field_value(
            transformed_value, field_metadata
        )
        return validation.is_valid

    def _execute_migration_strategy(
        self,
        resource_id: Union[int, str],
        mapping: MigrationMapping,
        transformed_value: Any,
    ) -> bool:
        """Execute migration based on the specified strategy."""
        if mapping.strategy == MigrationStrategy.REPLACE:
            return self._execute_replace_strategy(
                resource_id, mapping.target_field, transformed_value
            )

        elif mapping.strategy == MigrationStrategy.ADD_OPTION:
            return self._execute_add_option_strategy(
                resource_id, mapping.target_field, transformed_value
            )

        elif mapping.strategy == MigrationStrategy.COPY_IF_EMPTY:
            return self._execute_copy_if_empty_strategy(
                resource_id, mapping.target_field, transformed_value
            )

        elif mapping.strategy == MigrationStrategy.MERGE:
            return self._execute_merge_strategy(
                resource_id, mapping.target_field, transformed_value
            )

        return False

    def _execute_replace_strategy(
        self, resource_id: Union[int, str], target_field: str, value: Any
    ) -> bool:
        """Execute replace migration strategy."""
        return self._value_manager.set_custom_field_value(
            resource_id, target_field, value
        )

    def _execute_add_option_strategy(
        self, resource_id: Union[int, str], target_field: str, value: Any
    ) -> bool:
        """Execute add option migration strategy."""
        if isinstance(value, str):
            return self._value_manager.add_to_multivalue_field(
                resource_id, target_field, value
            )
        return False

    def _execute_copy_if_empty_strategy(
        self, resource_id: Union[int, str], target_field: str, value: Any
    ) -> bool:
        """Execute copy if empty migration strategy."""
        current_target = self._value_manager.get_custom_field_value(
            resource_id, target_field
        )
        if not current_target:
            return self._value_manager.set_custom_field_value(
                resource_id, target_field, value
            )
        return True  # Skip if target already has value

    def _execute_merge_strategy(
        self, resource_id: Union[int, str], target_field: str, transformed_value: Any
    ) -> bool:
        """Execute merge migration strategy."""
        current_target = self._value_manager.get_custom_field_value(
            resource_id, target_field
        )
        if not current_target:
            return self._value_manager.set_custom_field_value(
                resource_id, target_field, transformed_value
            )

        merged_value = self._merge_values(current_target, transformed_value)
        return self._value_manager.set_custom_field_value(
            resource_id, target_field, merged_value
        )

    def _merge_values(self, current_value: Any, new_value: Any) -> Any:
        """Merge two values based on their types."""
        # For text fields, append
        if isinstance(current_value, str) and isinstance(new_value, str):
            return current_value + " " + new_value

        # For multi-value fields, combine lists
        elif isinstance(current_value, list) and isinstance(new_value, list):
            return list(set(current_value + new_value))

        # Default: use new value
        return new_value

    def _log_batch_completion(
        self, batch_start: int, batch_size: int, batch_result: BatchResult
    ) -> None:
        """Log completion of a migration batch."""
        batch_number = batch_start // batch_size + 1
        self._logger.info(
            f"Completed batch {batch_number}: "
            f"{batch_result.successful} successful, {batch_result.failed} failed"
        )

    def _create_detailed_results(
        self, migration_plan: MigrationPlan, execution_stats: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create detailed results dictionary."""
        return {
            "mappings_processed": len(migration_plan.mappings),
            "execution_time": time.time(),
            "dry_run": migration_plan.dry_run,
        }
