"""High-Performance Bulk Migration Tools.

This module provides optimized migration strategies that significantly reduce
API calls and improve performance for large-scale migrations.
"""

import logging
import time
from typing import Dict, Any, List, Optional, Union, Tuple
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed
import asyncio
from collections import defaultdict

from .base import BaseMigrationManager, MigrationPlan, MigrationResult, MigrationMapping
from ..custom_field_manager import CustomFieldValueManager

logger = logging.getLogger(__name__)


@dataclass
class BulkOperationResult:
    """Result of a bulk operation."""

    total_operations: int
    successful_operations: int
    failed_operations: int
    api_calls_made: int
    time_taken: float
    errors: List[str]


@dataclass
class PerformanceMetrics:
    """Performance metrics for migration operations."""

    total_resources: int
    total_api_calls: int
    total_time: float
    avg_time_per_resource: float
    avg_time_per_api_call: float
    resources_per_second: float
    api_calls_per_second: float


class BulkMigrationManager(BaseMigrationManager):
    """Enhanced migration manager with bulk operation support."""

    def __init__(self, resource, client, resource_type: str):
        """Initialize the bulk migration manager."""
        super().__init__(resource, client, resource_type)
        self._batch_cache = {}
        self._field_metadata_cache = {}

    def execute_bulk_migration_plan(
        self, migration_plan: MigrationPlan, strategy: str = "auto"
    ) -> MigrationResult:
        """Execute migration plan using optimized bulk strategies.

        Args:
            migration_plan: Migration plan to execute
            strategy: Bulk strategy ('auto', 'put_batch', 'parallel', 'hybrid')

        Returns:
            MigrationResult with enhanced performance metrics
        """
        start_time = time.time()

        # Choose optimal strategy
        if strategy == "auto":
            strategy = self._choose_optimal_strategy(migration_plan)

        self._logger.info(f"Executing bulk migration with strategy: {strategy}")

        # Execute based on strategy
        if strategy == "put_batch":
            result = self._execute_put_batch_strategy(migration_plan)
        elif strategy == "parallel":
            result = self._execute_parallel_strategy(migration_plan)
        elif strategy == "hybrid":
            result = self._execute_hybrid_strategy(migration_plan)
        else:
            # Fallback to standard approach
            result = super().execute_migration_plan(migration_plan)

        # Add performance metrics
        end_time = time.time()
        result.detailed_results["performance_metrics"] = PerformanceMetrics(
            total_resources=result.total_resources,
            total_api_calls=result.detailed_results.get("api_calls", 0),
            total_time=end_time - start_time,
            avg_time_per_resource=(end_time - start_time)
            / max(result.total_resources, 1),
            avg_time_per_api_call=(end_time - start_time)
            / max(result.detailed_results.get("api_calls", 1), 1),
            resources_per_second=result.total_resources / (end_time - start_time),
            api_calls_per_second=result.detailed_results.get("api_calls", 0)
            / (end_time - start_time),
        )

        return result

    def _choose_optimal_strategy(self, migration_plan: MigrationPlan) -> str:
        """Choose the optimal bulk strategy based on migration characteristics."""

        resource_count = (
            len(migration_plan.resource_ids) if migration_plan.resource_ids else 1000
        )
        mapping_count = len(migration_plan.mappings)

        # Strategy selection logic
        if resource_count < 10:
            return "parallel"  # Small datasets benefit from parallel processing
        elif mapping_count > 5 and resource_count > 100:
            return "hybrid"  # Many mappings + many resources = hybrid approach
        elif resource_count > 50:
            return "put_batch"  # Large datasets benefit from PUT batching
        else:
            return "parallel"

    def _execute_put_batch_strategy(
        self, migration_plan: MigrationPlan
    ) -> MigrationResult:
        """Execute migration using PUT batch strategy.

        This strategy fetches each resource once, applies all migrations in memory,
        then PUTs the updated resource back. Significantly reduces API calls.
        """
        self._logger.info("Executing PUT batch strategy")

        total_successful = 0
        total_failed = 0
        total_skipped = 0
        errors = []
        api_calls = 0

        if not migration_plan.resource_ids:
            raise ValueError("PUT batch strategy requires specific resource IDs")

        # Process resources in batches to avoid memory issues
        batch_size = min(
            migration_plan.batch_size, 50
        )  # Limit batch size for PUT strategy

        for batch_start in range(0, len(migration_plan.resource_ids), batch_size):
            batch_end = min(batch_start + batch_size, len(migration_plan.resource_ids))
            batch_resource_ids = migration_plan.resource_ids[batch_start:batch_end]

            batch_result = self._execute_put_batch(
                batch_resource_ids, migration_plan.mappings, migration_plan.dry_run
            )

            total_successful += batch_result.successful_operations
            total_failed += batch_result.failed_operations
            api_calls += batch_result.api_calls_made
            errors.extend(batch_result.errors)

            self._logger.info(
                f"Batch {batch_start//batch_size + 1}: "
                f"{batch_result.successful_operations} successful, "
                f"{batch_result.failed_operations} failed, "
                f"{batch_result.api_calls_made} API calls"
            )

        return MigrationResult(
            total_resources=len(migration_plan.resource_ids),
            successful_migrations=total_successful,
            failed_migrations=total_failed,
            skipped_migrations=total_skipped,
            errors=errors,
            warnings=[],
            detailed_results={
                "strategy": "put_batch",
                "api_calls": api_calls,
                "api_call_reduction": f"{((len(migration_plan.resource_ids) * len(migration_plan.mappings) * 2) - api_calls) / (len(migration_plan.resource_ids) * len(migration_plan.mappings) * 2) * 100:.1f}%",
            },
        )

    def _execute_put_batch(
        self,
        resource_ids: List[Union[str, int]],
        mappings: List[MigrationMapping],
        dry_run: bool,
    ) -> BulkOperationResult:
        """Execute a batch of resources using PUT strategy."""

        successful = 0
        failed = 0
        api_calls = 0
        errors = []
        start_time = time.time()

        for resource_id in resource_ids:
            try:
                # Fetch resource once (1 API call)
                resource_data = self._resource.get(resource_id)
                api_calls += 1

                if not resource_data:
                    failed += 1
                    errors.append(f"Resource {resource_id} not found")
                    continue

                # Apply all migrations in memory
                updated_fields = {}
                migration_applied = False

                for mapping in mappings:
                    try:
                        # Get current source value
                        source_value = self._value_manager.get_custom_field_value(
                            resource_id, mapping.source_field
                        )

                        # Skip if no source data
                        if source_value is None or not str(source_value).strip():
                            continue

                        # Apply transformation
                        transformed_value = self._apply_transformation(
                            source_value, mapping
                        )
                        if transformed_value is None:
                            continue

                        # Prepare field update
                        if mapping.strategy.value == "add_option":
                            # For add_option, we need to handle multi-value fields
                            current_target = self._value_manager.get_custom_field_value(
                                resource_id, mapping.target_field
                            )
                            if isinstance(current_target, list):
                                if transformed_value not in current_target:
                                    updated_fields[mapping.target_field] = (
                                        current_target + [transformed_value]
                                    )
                                    migration_applied = True
                            else:
                                updated_fields[mapping.target_field] = [
                                    transformed_value
                                ]
                                migration_applied = True
                        else:
                            # For other strategies
                            updated_fields[mapping.target_field] = transformed_value
                            migration_applied = True

                        # Mark source for clearing if needed
                        if not mapping.preserve_source:
                            updated_fields[mapping.source_field] = None
                            migration_applied = True

                    except Exception as e:
                        self._logger.warning(
                            f"Failed to prepare migration for {mapping.source_field}: {e}"
                        )

                # Update resource if changes were made (1 API call)
                if migration_applied and updated_fields:
                    if not dry_run:
                        try:
                            # Use PATCH instead of PUT to only update changed fields
                            update_success = self._resource.patch(
                                resource_id, updated_fields
                            )
                            api_calls += 1

                            if update_success:
                                successful += 1
                            else:
                                failed += 1
                                errors.append(
                                    f"Failed to update resource {resource_id}"
                                )
                        except Exception as e:
                            failed += 1
                            errors.append(f"Error updating resource {resource_id}: {e}")
                            api_calls += 1  # Still count the failed API call
                    else:
                        # Dry run - just log what would be updated
                        self._logger.info(
                            f"[DRY RUN] Would update resource {resource_id} with fields: {list(updated_fields.keys())}"
                        )
                        successful += 1
                else:
                    # No changes needed
                    successful += 1

            except Exception as e:
                failed += 1
                errors.append(f"Error processing resource {resource_id}: {e}")

        return BulkOperationResult(
            total_operations=len(resource_ids),
            successful_operations=successful,
            failed_operations=failed,
            api_calls_made=api_calls,
            time_taken=time.time() - start_time,
            errors=errors,
        )

    def _execute_parallel_strategy(
        self, migration_plan: MigrationPlan
    ) -> MigrationResult:
        """Execute migration using parallel processing strategy."""

        self._logger.info("Executing parallel processing strategy")

        if not migration_plan.resource_ids:
            raise ValueError("Parallel strategy requires specific resource IDs")

        total_successful = 0
        total_failed = 0
        total_skipped = 0
        errors = []
        api_calls = 0

        # Use ThreadPoolExecutor for parallel processing
        max_workers = min(
            migration_plan.max_workers, 10
        )  # Limit to avoid overwhelming API

        def process_resource_parallel(resource_id):
            """Process a single resource with all its mappings."""
            resource_api_calls = 0
            resource_successful = 0
            resource_failed = 0
            resource_errors = []

            try:
                for mapping in migration_plan.mappings:
                    try:
                        # Standard single migration approach but in parallel
                        success = self._execute_single_migration(
                            resource_id, mapping, migration_plan.dry_run
                        )
                        resource_api_calls += (
                            2  # Estimate: 1 read + 1 write per migration
                        )

                        if success:
                            resource_successful += 1
                        else:
                            resource_failed += 1
                    except Exception as e:
                        resource_failed += 1
                        resource_errors.append(f"Migration {mapping.source_field}: {e}")

                return (
                    resource_successful,
                    resource_failed,
                    resource_api_calls,
                    resource_errors,
                )

            except Exception as e:
                return (
                    0,
                    len(migration_plan.mappings),
                    resource_api_calls,
                    [f"Resource error: {e}"],
                )

        # Process resources in parallel
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_resource = {
                executor.submit(process_resource_parallel, resource_id): resource_id
                for resource_id in migration_plan.resource_ids
            }

            for future in as_completed(future_to_resource):
                resource_id = future_to_resource[future]
                try:
                    successful, failed, calls, resource_errors = future.result()
                    total_successful += successful
                    total_failed += failed
                    api_calls += calls
                    errors.extend(
                        [f"Resource {resource_id}: {err}" for err in resource_errors]
                    )
                except Exception as e:
                    total_failed += len(migration_plan.mappings)
                    errors.append(f"Resource {resource_id} processing failed: {e}")

        return MigrationResult(
            total_resources=len(migration_plan.resource_ids),
            successful_migrations=total_successful,
            failed_migrations=total_failed,
            skipped_migrations=total_skipped,
            errors=errors,
            warnings=[],
            detailed_results={
                "strategy": "parallel",
                "api_calls": api_calls,
                "max_workers": max_workers,
            },
        )

    def _execute_hybrid_strategy(
        self, migration_plan: MigrationPlan
    ) -> MigrationResult:
        """Execute migration using hybrid strategy (PUT batch + parallel processing)."""

        self._logger.info("Executing hybrid strategy")

        # For small batches, use PUT batch strategy in parallel
        batch_size = min(migration_plan.batch_size // migration_plan.max_workers, 25)
        max_workers = min(migration_plan.max_workers, 5)

        total_successful = 0
        total_failed = 0
        total_skipped = 0
        errors = []
        total_api_calls = 0

        # Split resources into batches for parallel PUT processing
        resource_batches = [
            migration_plan.resource_ids[i : i + batch_size]
            for i in range(0, len(migration_plan.resource_ids), batch_size)
        ]

        def process_batch_parallel(batch_resource_ids):
            """Process a batch of resources using PUT strategy."""
            return self._execute_put_batch(
                batch_resource_ids, migration_plan.mappings, migration_plan.dry_run
            )

        # Process batches in parallel
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_batch = {
                executor.submit(process_batch_parallel, batch): i
                for i, batch in enumerate(resource_batches)
            }

            for future in as_completed(future_to_batch):
                batch_num = future_to_batch[future]
                try:
                    batch_result = future.result()
                    total_successful += batch_result.successful_operations
                    total_failed += batch_result.failed_operations
                    total_api_calls += batch_result.api_calls_made
                    errors.extend(
                        [f"Batch {batch_num}: {err}" for err in batch_result.errors]
                    )

                    self._logger.info(
                        f"Batch {batch_num} completed: "
                        f"{batch_result.successful_operations} successful, "
                        f"{batch_result.failed_operations} failed"
                    )
                except Exception as e:
                    batch_size_actual = len(resource_batches[batch_num])
                    total_failed += batch_size_actual * len(migration_plan.mappings)
                    errors.append(f"Batch {batch_num} processing failed: {e}")

        return MigrationResult(
            total_resources=len(migration_plan.resource_ids),
            successful_migrations=total_successful,
            failed_migrations=total_failed,
            skipped_migrations=total_skipped,
            errors=errors,
            warnings=[],
            detailed_results={
                "strategy": "hybrid",
                "api_calls": total_api_calls,
                "batch_size": batch_size,
                "max_workers": max_workers,
                "total_batches": len(resource_batches),
            },
        )

    def benchmark_migration_strategies(
        self, migration_plan: MigrationPlan, sample_size: int = 10
    ) -> Dict[str, PerformanceMetrics]:
        """Benchmark different migration strategies on a sample of resources.

        Args:
            migration_plan: Migration plan to benchmark
            sample_size: Number of resources to test with

        Returns:
            Performance metrics for each strategy
        """
        if (
            not migration_plan.resource_ids
            or len(migration_plan.resource_ids) < sample_size
        ):
            raise ValueError(
                f"Need at least {sample_size} resource IDs for benchmarking"
            )

        # Create sample plan
        sample_resource_ids = migration_plan.resource_ids[:sample_size]
        sample_plan = MigrationPlan(
            mappings=migration_plan.mappings,
            resource_ids=sample_resource_ids,
            dry_run=True,  # Always dry run for benchmarking
            batch_size=sample_size,
            max_workers=migration_plan.max_workers,
        )

        strategies = ["parallel", "put_batch", "hybrid"]
        results = {}

        self._logger.info(
            f"Benchmarking migration strategies with {sample_size} resources"
        )

        for strategy in strategies:
            self._logger.info(f"Testing strategy: {strategy}")
            start_time = time.time()

            try:
                result = self.execute_bulk_migration_plan(
                    sample_plan, strategy=strategy
                )
                end_time = time.time()

                results[strategy] = PerformanceMetrics(
                    total_resources=result.total_resources,
                    total_api_calls=result.detailed_results.get("api_calls", 0),
                    total_time=end_time - start_time,
                    avg_time_per_resource=(end_time - start_time)
                    / result.total_resources,
                    avg_time_per_api_call=(end_time - start_time)
                    / max(result.detailed_results.get("api_calls", 1), 1),
                    resources_per_second=result.total_resources
                    / (end_time - start_time),
                    api_calls_per_second=result.detailed_results.get("api_calls", 0)
                    / (end_time - start_time),
                )

                self._logger.info(
                    f"{strategy}: {results[strategy].resources_per_second:.1f} resources/sec, "
                    f"{result.detailed_results.get('api_calls', 0)} API calls"
                )

            except Exception as e:
                self._logger.error(f"Strategy {strategy} failed: {e}")
                results[strategy] = None

        return results

    def get_performance_recommendations(
        self, migration_plan: MigrationPlan
    ) -> Dict[str, Any]:
        """Get performance recommendations for a migration plan."""

        resource_count = (
            len(migration_plan.resource_ids) if migration_plan.resource_ids else 1000
        )
        mapping_count = len(migration_plan.mappings)
        estimated_api_calls = (
            resource_count * mapping_count * 2
        )  # Read + Write per mapping

        recommendations = {
            "recommended_strategy": self._choose_optimal_strategy(migration_plan),
            "estimated_api_calls": estimated_api_calls,
            "recommendations": [],
        }

        # Add specific recommendations
        if estimated_api_calls > 1000:
            recommendations["recommendations"].append(
                "Consider using PUT batch strategy to reduce API calls by ~50%"
            )

        if resource_count > 100:
            recommendations["recommendations"].append(
                "Use parallel processing with max_workers=3-5 for better throughput"
            )

        if mapping_count > 5:
            recommendations["recommendations"].append(
                "Multiple mappings detected - hybrid strategy may provide best performance"
            )

        if migration_plan.batch_size > 100:
            recommendations["recommendations"].append(
                "Consider smaller batch sizes (50-100) for better error handling"
            )

        return recommendations
