"""Fast Migration Plan Discovery System.

This module provides high-performance field discovery and migration plan generation
by using optimized search strategies instead of iterating through individual resources.
"""

import logging
import time
from typing import Dict, Any, List, Optional, Set, Union, Tuple
from dataclasses import dataclass
from collections import defaultdict
import concurrent.futures

from ..types import SearchRequest, SearchField
from .base import MigrationPlan, MigrationMapping, MigrationStrategy

logger = logging.getLogger(__name__)


@dataclass
class FieldDiscoveryResult:
    """Result of field discovery analysis."""

    field_name: str
    resource_count: int
    sample_values: List[Any]
    data_types: Set[str]
    is_empty: bool
    discovery_time: float


@dataclass
class MigrationOpportunity:
    """Represents a potential migration opportunity."""

    source_field: str
    potential_targets: List[str]
    affected_resources: int
    confidence_score: float
    sample_mappings: Dict[str, Any]
    recommended_strategy: MigrationStrategy


@dataclass
class DiscoveryReport:
    """Complete discovery analysis report."""

    total_resources_analyzed: int
    fields_with_data: List[FieldDiscoveryResult]
    fields_without_data: List[str]
    migration_opportunities: List[MigrationOpportunity]
    discovery_time: float
    recommendations: List[str]


class FastDiscoveryManager:
    """High-performance discovery manager for migration planning."""

    def __init__(self, resource, client, resource_type: str):
        """Initialize the fast discovery manager.

        Args:
            resource: The resource instance (e.g., client.accounts)
            client: Neon CRM client instance
            resource_type: Type of resource (accounts, donations, etc.)
        """
        self._resource = resource
        self._client = client
        self._resource_type = resource_type
        self._logger = logging.getLogger(f"discovery.{resource_type}")

    def fast_field_discovery(
        self, field_names: List[str], sample_size: int = 100, parallel: bool = True
    ) -> DiscoveryReport:
        """Perform fast field discovery analysis.

        Uses optimized search queries instead of iterating through resources.

        Args:
            field_names: List of field names to analyze
            sample_size: Maximum number of sample values per field
            parallel: Whether to run discovery in parallel

        Returns:
            DiscoveryReport with analysis results
        """
        start_time = time.time()
        self._logger.info(f"Starting fast discovery for {len(field_names)} fields")

        # Discover fields with data
        if parallel and len(field_names) > 3:
            fields_with_data = self._parallel_field_discovery(field_names, sample_size)
        else:
            fields_with_data = self._sequential_field_discovery(
                field_names, sample_size
            )

        # Find fields without data
        fields_without_data = [
            field
            for field in field_names
            if not any(f.field_name == field for f in fields_with_data)
        ]

        # Calculate total resources analyzed
        total_resources = max(
            (result.resource_count for result in fields_with_data), default=0
        )

        # Generate migration opportunities
        migration_opportunities = self._identify_migration_opportunities(
            fields_with_data
        )

        # Generate recommendations
        recommendations = self._generate_recommendations(
            fields_with_data, migration_opportunities
        )

        discovery_time = time.time() - start_time
        self._logger.info(f"Discovery completed in {discovery_time:.2f}s")

        return DiscoveryReport(
            total_resources_analyzed=total_resources,
            fields_with_data=fields_with_data,
            fields_without_data=fields_without_data,
            migration_opportunities=migration_opportunities,
            discovery_time=discovery_time,
            recommendations=recommendations,
        )

    def generate_migration_plan_from_discovery(
        self,
        discovery_report: DiscoveryReport,
        target_field_mapping: Optional[Dict[str, str]] = None,
        resource_filter: Optional[Dict[str, Any]] = None,
    ) -> MigrationPlan:
        """Generate an optimized migration plan from discovery results.

        Args:
            discovery_report: Results from fast_field_discovery
            target_field_mapping: Optional mapping of source -> target fields
            resource_filter: Optional filter for which resources to migrate

        Returns:
            Optimized MigrationPlan
        """
        mappings = []

        # Use migration opportunities if no explicit mapping provided
        if not target_field_mapping:
            target_field_mapping = {}
            for opportunity in discovery_report.migration_opportunities:
                if opportunity.confidence_score > 0.7 and opportunity.potential_targets:
                    target_field_mapping[opportunity.source_field] = (
                        opportunity.potential_targets[0]
                    )

        # Create mappings for fields with data
        for field_result in discovery_report.fields_with_data:
            source_field = field_result.field_name
            target_field = target_field_mapping.get(source_field)

            if not target_field:
                self._logger.warning(f"No target field specified for {source_field}")
                continue

            # Choose strategy based on data characteristics
            strategy = self._choose_optimal_strategy(field_result)

            mapping = MigrationMapping(
                source_field=source_field,
                target_field=target_field,
                strategy=strategy,
                preserve_source=False,  # Default to cleanup
                validation_required=True,
            )

            mappings.append(mapping)

        # Optimize batch size based on discovered data volume
        optimal_batch_size = self._calculate_optimal_batch_size(discovery_report)

        return MigrationPlan(
            mappings=mappings,
            resource_filter=resource_filter,
            batch_size=optimal_batch_size,
            max_workers=3,  # Conservative default
            dry_run=True,  # Always start with dry run
        )

    def _parallel_field_discovery(
        self, field_names: List[str], sample_size: int
    ) -> List[FieldDiscoveryResult]:
        """Perform field discovery in parallel."""

        results = []

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            # Submit all field discovery tasks
            future_to_field = {
                executor.submit(
                    self._discover_single_field, field_name, sample_size
                ): field_name
                for field_name in field_names
            }

            # Collect results
            for future in concurrent.futures.as_completed(future_to_field):
                field_name = future_to_field[future]
                try:
                    result = future.result()
                    if result and not result.is_empty:
                        results.append(result)
                except Exception as e:
                    self._logger.warning(
                        f"Discovery failed for field {field_name}: {e}"
                    )

        return results

    def _sequential_field_discovery(
        self, field_names: List[str], sample_size: int
    ) -> List[FieldDiscoveryResult]:
        """Perform field discovery sequentially."""

        results = []

        for field_name in field_names:
            try:
                result = self._discover_single_field(field_name, sample_size)
                if result and not result.is_empty:
                    results.append(result)
            except Exception as e:
                self._logger.warning(f"Discovery failed for field {field_name}: {e}")

        return results

    def _discover_single_field(
        self, field_name: str, sample_size: int
    ) -> Optional[FieldDiscoveryResult]:
        """Discover data for a single field using optimized search."""

        start_time = time.time()

        try:
            # Use search to find resources with data in this field
            search_request = SearchRequest(
                searchFields=[SearchField(field=field_name, operator="NOT_BLANK")],
                outputFields=[self._get_resource_id_field(), field_name],
                pagination={"currentPage": 0, "pageSize": min(sample_size, 200)},
            )

            # Execute search
            search_results = list(self._resource.search(search_request))

            if not search_results:
                return FieldDiscoveryResult(
                    field_name=field_name,
                    resource_count=0,
                    sample_values=[],
                    data_types=set(),
                    is_empty=True,
                    discovery_time=time.time() - start_time,
                )

            # Extract sample values and analyze data types
            sample_values = []
            data_types = set()

            for result in search_results[:sample_size]:
                value = result.get(field_name)
                if value is not None:
                    sample_values.append(value)
                    data_types.add(type(value).__name__)

            # Get total count using a separate count query if needed
            resource_count = len(search_results)

            # If we got the max results, there might be more
            if len(search_results) >= min(sample_size, 200):
                # Try to get a better count estimate with a larger page size query
                try:
                    count_request = SearchRequest(
                        searchFields=[
                            SearchField(field=field_name, operator="NOT_BLANK")
                        ],
                        outputFields=[self._get_resource_id_field()],
                        pagination={"currentPage": 0, "pageSize": 1000},
                    )
                    count_results = list(self._resource.search(count_request))
                    resource_count = len(count_results)
                except Exception:
                    # Fallback to what we have
                    pass

            return FieldDiscoveryResult(
                field_name=field_name,
                resource_count=resource_count,
                sample_values=sample_values[:sample_size],
                data_types=data_types,
                is_empty=False,
                discovery_time=time.time() - start_time,
            )

        except Exception as e:
            self._logger.error(f"Error discovering field {field_name}: {e}")
            return None

    def _identify_migration_opportunities(
        self, fields_with_data: List[FieldDiscoveryResult]
    ) -> List[MigrationOpportunity]:
        """Identify potential migration opportunities based on field patterns."""

        opportunities = []

        # Group fields by common patterns
        field_groups = defaultdict(list)

        for field_result in fields_with_data:
            field_name = field_result.field_name

            # Identify common prefixes (e.g., V-, Custom-, etc.)
            if "-" in field_name:
                prefix = field_name.split("-")[0]
                field_groups[prefix].append(field_result)
            else:
                field_groups["ungrouped"].append(field_result)

        # Analyze each group for migration opportunities
        for group_name, group_fields in field_groups.items():
            if len(group_fields) < 2:  # Need at least 2 fields to suggest consolidation
                continue

            # Look for consolidation opportunities
            total_resources = sum(f.resource_count for f in group_fields)
            avg_resources = total_resources / len(group_fields)

            # Suggest consolidation if fields have similar patterns
            for field_result in group_fields:
                # Suggest potential target fields based on naming patterns
                potential_targets = self._suggest_target_fields(
                    field_result.field_name, group_name
                )

                confidence_score = min(
                    field_result.resource_count
                    / max(avg_resources, 1),  # Resource density
                    len(potential_targets) * 0.3,  # Target availability
                )

                # Choose strategy based on data characteristics
                strategy = self._choose_optimal_strategy(field_result)

                opportunity = MigrationOpportunity(
                    source_field=field_result.field_name,
                    potential_targets=potential_targets,
                    affected_resources=field_result.resource_count,
                    confidence_score=min(confidence_score, 1.0),
                    sample_mappings=self._create_sample_mappings(field_result),
                    recommended_strategy=strategy,
                )

                opportunities.append(opportunity)

        # Sort by confidence score and resource impact
        opportunities.sort(
            key=lambda x: (x.confidence_score, x.affected_resources), reverse=True
        )

        return opportunities

    def _suggest_target_fields(self, source_field: str, group_name: str) -> List[str]:
        """Suggest potential target fields based on naming patterns."""

        suggestions = []

        # Common consolidation patterns
        if group_name == "V":
            # V-field consolidation patterns - using standardized field names
            if any(
                keyword in source_field.lower()
                for keyword in [
                    "skill",
                    "talent",
                    "ability",
                    "data",
                    "entry",
                    "admin",
                    "office",
                    "technology",
                    "tech",
                ]
            ):
                suggestions.append("V-Volunteer Skills")
            elif any(
                keyword in source_field.lower()
                for keyword in [
                    "interest",
                    "want",
                    "like",
                    "event",
                    "planning",
                    "food",
                    "hospitality",
                ]
            ):
                suggestions.append("V-Volunteer Interests")
            elif any(
                keyword in source_field.lower()
                for keyword in [
                    "campaign",
                    "election",
                    "vote",
                    "canvass",
                    "phone",
                    "text",
                    "banking",
                ]
            ):
                suggestions.append("V-Volunteer Campaign & Election Activities")
            elif any(
                keyword in source_field.lower()
                for keyword in ["availability", "time", "schedule"]
            ):
                suggestions.append("V-Volunteer Availability")
            else:
                # Generic V-field suggestions - primary standardized categories
                suggestions.extend(
                    [
                        "V-Volunteer Skills",
                        "V-Volunteer Campaign & Election Activities",
                        "V-Volunteer Interests",
                        "V-Volunteer Availability",
                    ]
                )

        elif group_name == "Custom":
            # Custom field consolidation
            suggestions.append(f"{group_name}-Consolidated")

        else:
            # Generic suggestions
            suggestions.append(f"{group_name}-Consolidated")

        return suggestions[:3]  # Limit to top 3 suggestions

    def _create_sample_mappings(
        self, field_result: FieldDiscoveryResult
    ) -> Dict[str, Any]:
        """Create sample mappings to show how data would be transformed."""

        mappings = {}

        # Take first few sample values
        for i, value in enumerate(field_result.sample_values[:3]):
            if value is not None and str(value).strip():
                mappings[f"sample_{i+1}"] = {
                    "source_value": value,
                    "suggested_target": self._transform_value_for_consolidation(
                        value, field_result.field_name
                    ),
                }

        return mappings

    def _transform_value_for_consolidation(self, value: Any, source_field: str) -> str:
        """Suggest how a value might be transformed for consolidation."""

        # For V-fields, often the source field name becomes the option value
        if source_field.startswith("V-"):
            # Convert field name to a clean option name
            clean_name = source_field[2:]  # Remove V- prefix
            clean_name = clean_name.replace("_", " ").replace("-", " ")
            return clean_name

        # For boolean-like values, use the field name as the option
        if str(value).lower() in ["true", "1", "yes", "checked"]:
            return (
                source_field.split("-", 1)[-1] if "-" in source_field else source_field
            )

        # For text values, might keep as-is or use field name
        return str(value) if len(str(value)) < 50 else source_field

    def _choose_optimal_strategy(
        self, field_result: FieldDiscoveryResult
    ) -> MigrationStrategy:
        """Choose the optimal migration strategy based on field characteristics."""

        # Analyze sample values to determine best strategy
        value_types = field_result.data_types

        # If values are boolean-like, use ADD_OPTION strategy
        boolean_indicators = ["bool", "boolean"]
        if any(dtype.lower() in boolean_indicators for dtype in value_types):
            return MigrationStrategy.ADD_OPTION

        # If values are text and varied, might be good for ADD_OPTION consolidation
        if "str" in value_types or "string" in value_types:
            unique_values = len(
                {str(v) for v in field_result.sample_values if v is not None}
            )
            if unique_values < len(field_result.sample_values) * 0.5:  # Low diversity
                return MigrationStrategy.ADD_OPTION
            else:
                return MigrationStrategy.COPY_IF_EMPTY

        # Default strategy
        return MigrationStrategy.COPY_IF_EMPTY

    def _calculate_optimal_batch_size(self, discovery_report: DiscoveryReport) -> int:
        """Calculate optimal batch size based on discovered data characteristics."""

        # Consider total resources and field complexity
        total_resources = discovery_report.total_resources_analyzed
        field_count = len(discovery_report.fields_with_data)

        # Base batch size on resource count
        if total_resources < 100:
            base_batch_size = 25
        elif total_resources < 1000:
            base_batch_size = 50
        else:
            base_batch_size = 100

        # Adjust for field complexity
        if field_count > 10:
            base_batch_size = max(25, base_batch_size // 2)
        elif field_count > 5:
            base_batch_size = max(50, int(base_batch_size * 0.75))

        return base_batch_size

    def _generate_recommendations(
        self,
        fields_with_data: List[FieldDiscoveryResult],
        migration_opportunities: List[MigrationOpportunity],
    ) -> List[str]:
        """Generate actionable recommendations based on discovery results."""

        recommendations = []

        # Resource volume recommendations
        total_resources = max((f.resource_count for f in fields_with_data), default=0)
        if total_resources > 1000:
            recommendations.append(
                f"Large dataset detected ({total_resources} resources). "
                "Consider using bulk migration strategies for better performance."
            )

        # Field consolidation recommendations
        high_confidence_opportunities = [
            opp for opp in migration_opportunities if opp.confidence_score > 0.7
        ]

        if high_confidence_opportunities:
            recommendations.append(
                f"Found {len(high_confidence_opportunities)} high-confidence migration opportunities. "
                "Review suggested field consolidations."
            )

        # Performance recommendations
        if len(fields_with_data) > 10:
            recommendations.append(
                "Many fields detected. Consider splitting migration into phases for better error handling."
            )

        # Data quality recommendations
        mixed_type_fields = [f for f in fields_with_data if len(f.data_types) > 1]

        if mixed_type_fields:
            recommendations.append(
                f"{len(mixed_type_fields)} fields have mixed data types. "
                "Review data quality before migration."
            )

        # Empty field cleanup
        if not recommendations:
            recommendations.append(
                "Discovery completed successfully. Ready for migration planning."
            )

        return recommendations

    def _get_resource_id_field(self) -> str:
        """Get the resource ID field name for this resource type."""

        # Resource-specific ID field mappings
        id_field_map = {
            "accounts": "Account ID",
            "donations": "Donation ID",
            "events": "Event ID",
            "activities": "Activity ID",
            "campaigns": "Campaign ID",
            "volunteers": "Volunteer ID",
            "memberships": "Membership ID",
        }

        return id_field_map.get(self._resource_type, "ID")

    def bulk_resource_discovery(
        self, field_patterns: List[str], max_fields_per_pattern: int = 50
    ) -> Dict[str, List[str]]:
        """Discover fields matching patterns across the resource.

        Args:
            field_patterns: List of patterns to search for (e.g., ['V-*', 'Custom-*'])
            max_fields_per_pattern: Maximum fields to discover per pattern

        Returns:
            Dictionary mapping patterns to discovered field names
        """
        self._logger.info(
            f"Starting bulk field discovery for patterns: {field_patterns}"
        )

        discovered_fields = {}

        try:
            # Get all available custom fields for this resource
            all_custom_fields = list(self._resource.list_custom_fields())

            for pattern in field_patterns:
                matching_fields = []

                # Simple pattern matching (could be enhanced with regex)
                pattern_prefix = pattern.replace("*", "")

                for field in all_custom_fields:
                    field_name = field.get("name", "")
                    if field_name.startswith(pattern_prefix):
                        matching_fields.append(field_name)

                        if len(matching_fields) >= max_fields_per_pattern:
                            break

                discovered_fields[pattern] = matching_fields
                self._logger.info(
                    f"Pattern '{pattern}': found {len(matching_fields)} fields"
                )

        except Exception as e:
            self._logger.error(f"Bulk field discovery failed: {e}")
            # Fallback to empty results
            discovered_fields = {pattern: [] for pattern in field_patterns}

        return discovered_fields
