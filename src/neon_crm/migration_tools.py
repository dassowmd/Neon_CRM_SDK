"""Migration and bulk operation tools for Neon CRM custom fields.

This module provides tools for migrating custom field data, performing bulk operations,
and managing data transformations based on learnings from the notebook migrations.
"""

from typing import Any, Dict, List, Optional, Union, Callable, Iterator, TYPE_CHECKING
from dataclasses import dataclass
from enum import Enum
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

from .custom_field_manager import (
    CustomFieldValueManager,
    CustomFieldUpdate,
    BatchResult,
)
from .custom_field_validation import CustomFieldValidator, ValidationResult
from .custom_field_types import CustomFieldTypeMapper

if TYPE_CHECKING:
    from .client import NeonClient


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


class CustomFieldMigrationManager:
    """Advanced manager for custom field migrations and bulk operations."""

    def __init__(self, client: "NeonClient", resource_type: str):
        """Initialize the migration manager.

        Args:
            client: Neon CRM client instance
            resource_type: Type of resource (accounts, donations, etc.)
        """
        self._client = client
        self._resource_type = resource_type
        self._resource = getattr(client, resource_type)
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
            sample_resources = self._get_sample_resources(
                migration_plan.resource_filter, limit=10
            )
        else:
            sample_resources = self._get_sample_resources({}, limit=10)

        for resource in sample_resources:
            resource_id = resource.get(
                "Account ID" if self._resource_type == "accounts" else "ID"
            )
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

    def execute_migration_plan(self, migration_plan: MigrationPlan) -> MigrationResult:
        """Execute a complete migration plan.

        Args:
            migration_plan: Migration plan to execute

        Returns:
            MigrationResult with execution statistics and details
        """
        self._logger.info(
            f"Starting migration plan execution (dry_run={migration_plan.dry_run})"
        )

        resources = self._prepare_resources_for_migration(migration_plan)
        if not resources:
            return MigrationResult(
                0, 0, 0, 0, ["No resources found matching filter criteria"], [], {}
            )

        execution_stats = self._execute_migration_batches(migration_plan, resources)
        detailed_results = self._create_detailed_results(
            migration_plan, execution_stats
        )

        return MigrationResult(
            len(resources),
            execution_stats["successful"],
            execution_stats["failed"],
            execution_stats["skipped"],
            execution_stats["errors"],
            execution_stats["warnings"],
            detailed_results,
        )

    def _prepare_resources_for_migration(
        self, migration_plan: MigrationPlan
    ) -> List[Dict[str, Any]]:
        """Prepare and validate resources for migration."""
        return list(self._get_resources_for_migration(migration_plan))

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

    def bulk_add_option_to_multivalue(
        self,
        field_name: str,
        new_option: str,
        resource_filter: Optional[Dict[str, Any]] = None,
        dry_run: bool = True,
    ) -> MigrationResult:
        """Add an option to a multi-value field for multiple resources.

        Args:
            field_name: Name of the multi-value field
            new_option: Option to add
            resource_filter: Filter for which resources to update
            dry_run: Whether to perform a dry run

        Returns:
            MigrationResult with execution statistics
        """
        self._logger.info(
            f"Bulk adding '{new_option}' to field '{field_name}' (dry_run={dry_run})"
        )

        resources = self._filter_resources_for_option_addition(
            field_name, new_option, resource_filter
        )
        execution_results = self._execute_bulk_option_addition(
            resources, field_name, new_option, dry_run
        )

        return MigrationResult(
            total_resources=len(resources),
            successful_migrations=execution_results["successful"],
            failed_migrations=execution_results["failed"],
            skipped_migrations=0,
            errors=execution_results["errors"],
            warnings=[],
            detailed_results={
                "operation": "bulk_add_option",
                "field": field_name,
                "option": new_option,
            },
        )

    def _filter_resources_for_option_addition(
        self,
        field_name: str,
        new_option: str,
        resource_filter: Optional[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Filter resources that need the option added (don't already have it)."""
        resources = []
        for resource in self._get_resources_for_migration(
            {"resource_filter": resource_filter}
        ):
            resource_id = resource.get(
                "Account ID" if self._resource_type == "accounts" else "ID"
            )
            if not resource_id:
                continue

            if self._resource_needs_option_added(resource_id, field_name, new_option):
                resources.append(resource)

        return resources

    def _resource_needs_option_added(
        self, resource_id: Union[int, str], field_name: str, new_option: str
    ) -> bool:
        """Check if a resource needs the option added to the field."""
        current_value = self._value_manager.get_custom_field_value(
            resource_id, field_name
        )

        if isinstance(current_value, list):
            current_options = current_value
        elif isinstance(current_value, str):
            current_options = CustomFieldTypeMapper.parse_multivalue_string(
                current_value
            )
        else:
            current_options = []

        return new_option not in current_options

    def _execute_bulk_option_addition(
        self,
        resources: List[Dict[str, Any]],
        field_name: str,
        new_option: str,
        dry_run: bool,
    ) -> Dict[str, Any]:
        """Execute the bulk option addition for the filtered resources."""
        successful = 0
        failed = 0
        errors = []

        for resource in resources:
            resource_id = resource.get(
                "Account ID" if self._resource_type == "accounts" else "ID"
            )

            try:
                if not dry_run:
                    success = self._value_manager.add_to_multivalue_field(
                        resource_id, field_name, new_option
                    )
                    if success:
                        successful += 1
                    else:
                        failed += 1
                        errors.append(f"Failed to add option to resource {resource_id}")
                else:
                    successful += 1  # In dry run, assume success

            except Exception as e:
                failed += 1
                errors.append(f"Error processing resource {resource_id}: {str(e)}")

        return {"successful": successful, "failed": failed, "errors": errors}

    def bulk_validate_custom_field_values(
        self,
        field_value_pairs: List[Dict[str, Any]],
        resource_filter: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, ValidationResult]:
        """Validate custom field values for multiple resources.

        Args:
            field_value_pairs: List of dictionaries with field names and values to validate
            resource_filter: Filter for which resources to validate

        Returns:
            Dictionary mapping resource IDs to validation results
        """
        results = {}

        # Get field metadata for validation
        field_names = set()
        for pair in field_value_pairs:
            field_names.update(pair.keys())

        field_metadata = {}
        for field_name in field_names:
            metadata = self._resource.find_custom_field_by_name(field_name)
            if metadata:
                field_metadata[field_name] = metadata

        # Validate for each resource
        for resource in self._get_resources_for_migration(
            {"resource_filter": resource_filter}
        ):
            resource_id = resource.get(
                "Account ID" if self._resource_type == "accounts" else "ID"
            )
            if not resource_id:
                continue

            resource_results = {}
            for field_values in field_value_pairs:
                for field_name, value in field_values.items():
                    if field_name in field_metadata:
                        validation_result = CustomFieldValidator.validate_field_value(
                            value, field_metadata[field_name]
                        )
                        resource_results[field_name] = validation_result

            if resource_results:
                results[resource_id] = resource_results

        return results

    def create_migration_plan_from_notebook_mapping(
        self, notebook_mapping: Dict[str, Any]
    ) -> MigrationPlan:
        """Create a migration plan from notebook-style mapping configuration.

        Args:
            notebook_mapping: Mapping dictionary from notebook format

        Returns:
            MigrationPlan object
        """
        mappings = []

        for old_field, mapping_config in notebook_mapping.items():
            if mapping_config == "TODO":
                continue

            target_field = mapping_config["field"]

            if "option" in mapping_config:
                # This is mapping to a specific option in a multi-value field
                strategy = MigrationStrategy.ADD_OPTION

                # Create a transform function to extract the specific option
                option_value = mapping_config["option"]
                transform_fn = (
                    lambda x, opt=option_value: opt
                )  # Closure to capture option_value

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

    def _get_resources_for_migration(
        self, config: Dict[str, Any]
    ) -> Iterator[Dict[str, Any]]:
        """Get resources that should be included in the migration."""
        resource_filter = config.get("resource_filter")

        if resource_filter:
            # Use search with the provided filter
            search_request = {
                "searchFields": [
                    {"field": key, "operator": "EQUAL", "value": value}
                    for key, value in resource_filter.items()
                ],
                "outputFields": ["*"],
            }
            yield from self._resource.search(search_request)
        else:
            # Get all resources (limited for safety)
            yield from self._resource.list(limit=1000)

    def _get_sample_resources(
        self, resource_filter: Dict[str, Any], limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get a small sample of resources for conflict analysis."""
        resources = []
        count = 0

        for resource in self._get_resources_for_migration(
            {"resource_filter": resource_filter}
        ):
            resources.append(resource)
            count += 1
            if count >= limit:
                break

        return resources

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
            resource_id = resource.get(
                "Account ID" if self._resource_type == "accounts" else "ID"
            )
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

    def iterate_all_mappings(
        self, account_id: Union[int, str], dry_run: bool = True
    ) -> Dict[str, Any]:
        """Iterate through all available field mappings for a specific account.

        Args:
            account_id: ID of the account to process
            dry_run: Whether to perform a dry run (default True)

        Returns:
            Dictionary containing mapping results and statistics
        """
        self._logger.info(
            f"Iterating through all mappings for account {account_id} (dry_run={dry_run})"
        )

        custom_fields = self._get_custom_fields_for_resource()
        if not custom_fields:
            return self._create_empty_mapping_result(account_id)

        mappings = self._generate_all_field_mappings(custom_fields)
        mapping_results = self._process_all_mappings(account_id, mappings, dry_run)

        self._log_mapping_completion(account_id, mapping_results)

        return self._create_mapping_result(
            account_id, mappings, mapping_results, dry_run
        )

    def _get_custom_fields_for_resource(self) -> List[Dict[str, Any]]:
        """Get all custom fields for the current resource type."""
        return self._resource.list_custom_fields()

    def _create_empty_mapping_result(
        self, account_id: Union[int, str]
    ) -> Dict[str, Any]:
        """Create an empty result when no custom fields are found."""
        return {
            "account_id": account_id,
            "total_mappings": 0,
            "processed_mappings": 0,
            "successful_mappings": 0,
            "failed_mappings": 0,
            "errors": ["No custom fields found for resource type"],
            "mappings_detail": {},
        }

    def _generate_all_field_mappings(
        self, custom_fields: List[Dict[str, Any]]
    ) -> List[MigrationMapping]:
        """Generate all possible field-to-field mappings."""
        field_names = [
            field.get("name", "") for field in custom_fields if field.get("name")
        ]
        mappings = []

        for i, source_field in enumerate(field_names):
            for j, target_field in enumerate(field_names):
                if i != j:  # Don't map a field to itself
                    mappings.append(
                        MigrationMapping(
                            source_field=source_field,
                            target_field=target_field,
                            strategy=MigrationStrategy.COPY_IF_EMPTY,
                            validation_required=True,
                            preserve_source=True,
                        )
                    )

        return mappings

    def _process_all_mappings(
        self,
        account_id: Union[int, str],
        mappings: List[MigrationMapping],
        dry_run: bool,
    ) -> Dict[str, Any]:
        """Process all mappings and return aggregated results."""
        successful_mappings = 0
        failed_mappings = 0
        errors = []
        mappings_detail = {}

        for mapping in mappings:
            mapping_key = f"{mapping.source_field} -> {mapping.target_field}"
            result = self._process_single_mapping(account_id, mapping, dry_run)

            mappings_detail[mapping_key] = result["detail"]

            if result["status"] == "success":
                successful_mappings += 1
            elif result["status"] == "failed":
                failed_mappings += 1
            elif result["status"] == "error":
                failed_mappings += 1
                errors.append(result["error"])

        return {
            "successful": successful_mappings,
            "failed": failed_mappings,
            "processed": len(mappings),
            "errors": errors,
            "details": mappings_detail,
        }

    def _process_single_mapping(
        self, account_id: Union[int, str], mapping: MigrationMapping, dry_run: bool
    ) -> Dict[str, Any]:
        """Process a single mapping and return its result."""
        mapping_key = f"{mapping.source_field} -> {mapping.target_field}"

        try:
            source_value = self._value_manager.get_custom_field_value(
                account_id, mapping.source_field
            )
            if source_value is None:
                return {
                    "status": "skipped",
                    "detail": {
                        "status": "skipped",
                        "reason": "No source value",
                        "source_value": None,
                        "target_value": None,
                    },
                }

            target_value = self._value_manager.get_custom_field_value(
                account_id, mapping.target_field
            )
            success = self._execute_single_migration(account_id, mapping, dry_run)

            if success:
                return {
                    "status": "success",
                    "detail": {
                        "status": "success",
                        "source_value": source_value,
                        "target_value": target_value,
                        "dry_run": dry_run,
                    },
                }
            else:
                return {
                    "status": "failed",
                    "detail": {
                        "status": "failed",
                        "source_value": source_value,
                        "target_value": target_value,
                        "reason": "Migration execution failed",
                    },
                }

        except Exception as e:
            error_msg = f"Error processing mapping {mapping_key}: {str(e)}"
            return {
                "status": "error",
                "error": error_msg,
                "detail": {"status": "error", "error": str(e)},
            }

    def _log_mapping_completion(
        self, account_id: Union[int, str], mapping_results: Dict[str, Any]
    ) -> None:
        """Log the completion of mapping iteration."""
        skipped = (
            mapping_results["processed"]
            - mapping_results["successful"]
            - mapping_results["failed"]
        )
        self._logger.info(
            f"Completed mapping iteration for account {account_id}: "
            f"{mapping_results['successful']} successful, {mapping_results['failed']} failed, "
            f"{skipped} skipped"
        )

    def _create_mapping_result(
        self,
        account_id: Union[int, str],
        mappings: List[MigrationMapping],
        mapping_results: Dict[str, Any],
        dry_run: bool,
    ) -> Dict[str, Any]:
        """Create the final mapping result dictionary."""
        return {
            "account_id": account_id,
            "total_mappings": len(mappings),
            "processed_mappings": mapping_results["processed"],
            "successful_mappings": mapping_results["successful"],
            "failed_mappings": mapping_results["failed"],
            "errors": mapping_results["errors"],
            "mappings_detail": mapping_results["details"],
            "dry_run": dry_run,
        }

    def _execute_single_migration(
        self, resource_id: Union[int, str], mapping: MigrationMapping, dry_run: bool
    ) -> bool:
        """Execute a single field migration."""
        try:
            source_value = self._get_and_validate_source_value(resource_id, mapping)
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
