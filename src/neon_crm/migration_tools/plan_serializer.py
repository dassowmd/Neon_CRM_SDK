"""Migration Plan Serialization and Export/Import functionality.

This module provides functionality to export migration plans to human-readable formats,
validate them, and import them back for execution.
"""

import json
import yaml
import csv
from typing import Dict, Any, List, Optional, Union, Callable
from dataclasses import dataclass, asdict
from pathlib import Path
from datetime import datetime
import logging

from .base import MigrationPlan, MigrationMapping, MigrationStrategy, ConflictReport

logger = logging.getLogger(__name__)


@dataclass
class MigrationPlanExport:
    """Container for exported migration plan with metadata."""

    metadata: Dict[str, Any]
    plan: Dict[str, Any]
    conflicts: Optional[Dict[str, Any]] = None
    validation_results: Optional[Dict[str, Any]] = None


@dataclass
class ExportOptions:
    """Options for migration plan export."""

    format: str = "yaml"  # yaml, json, csv
    include_metadata: bool = True
    include_conflicts: bool = True
    include_validation: bool = True
    human_readable: bool = True
    include_comments: bool = True


class MigrationPlanSerializer:
    """Handles serialization and deserialization of migration plans."""

    def __init__(self, migration_manager=None):
        """Initialize the serializer.

        Args:
            migration_manager: Optional migration manager for validation
        """
        self.migration_manager = migration_manager
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    def export_plan(
        self,
        migration_plan: MigrationPlan,
        output_path: Union[str, Path],
        options: Optional[ExportOptions] = None,
        conflicts: Optional[ConflictReport] = None,
    ) -> Path:
        """Export a migration plan to a file.

        Args:
            migration_plan: The migration plan to export
            output_path: Path where to save the exported plan
            options: Export options
            conflicts: Optional conflict report to include

        Returns:
            Path to the exported file
        """
        if options is None:
            options = ExportOptions()

        output_path = Path(output_path)

        # Create export container
        export_data = self._create_export_data(migration_plan, options, conflicts)

        # Export based on format
        if options.format.lower() == "yaml":
            self._export_yaml(export_data, output_path, options)
        elif options.format.lower() == "json":
            self._export_json(export_data, output_path, options)
        elif options.format.lower() == "csv":
            self._export_csv(export_data, output_path, options)
        else:
            raise ValueError(f"Unsupported export format: {options.format}")

        self.logger.info(f"Migration plan exported to {output_path}")
        return output_path

    def import_plan(self, file_path: Union[str, Path]) -> MigrationPlan:
        """Import a migration plan from a file.

        Args:
            file_path: Path to the exported migration plan file

        Returns:
            Reconstructed MigrationPlan object
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"Migration plan file not found: {file_path}")

        # Determine format from file extension
        suffix = file_path.suffix.lower()

        if suffix in [".yaml", ".yml"]:
            export_data = self._import_yaml(file_path)
        elif suffix == ".json":
            export_data = self._import_json(file_path)
        elif suffix == ".csv":
            export_data = self._import_csv(file_path)
        else:
            raise ValueError(f"Unsupported import format: {suffix}")

        # Reconstruct migration plan
        migration_plan = self._reconstruct_migration_plan(export_data)

        self.logger.info(f"Migration plan imported from {file_path}")
        return migration_plan

    def validate_imported_plan(
        self,
        migration_plan: MigrationPlan,
        original_export_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Validate an imported migration plan.

        Args:
            migration_plan: The imported migration plan
            original_export_data: Original export data for comparison

        Returns:
            Validation results dictionary
        """
        validation_results = {
            "valid": True,
            "warnings": [],
            "errors": [],
            "field_checks": {},
            "timestamp_check": None,
        }

        # Basic structure validation
        if not migration_plan.mappings:
            validation_results["errors"].append("No mappings found in migration plan")
            validation_results["valid"] = False

        # Field existence validation (if migration manager available)
        if self.migration_manager:
            field_checks = self._validate_field_existence(migration_plan)
            validation_results["field_checks"] = field_checks

            if field_checks.get("missing_fields"):
                validation_results["errors"].extend(
                    [
                        f"Missing field: {field}"
                        for field in field_checks["missing_fields"]
                    ]
                )
                validation_results["valid"] = False

        # Timestamp validation (if original data available)
        if original_export_data and "metadata" in original_export_data:
            timestamp_check = self._validate_timestamp_freshness(
                original_export_data["metadata"]
            )
            validation_results["timestamp_check"] = timestamp_check

            if timestamp_check.get("stale"):
                validation_results["warnings"].append(
                    f"Migration plan is {timestamp_check['age_hours']:.1f} hours old"
                )

        return validation_results

    def _create_export_data(
        self,
        migration_plan: MigrationPlan,
        options: ExportOptions,
        conflicts: Optional[ConflictReport] = None,
    ) -> MigrationPlanExport:
        """Create the export data structure."""

        # Create metadata
        metadata = {
            "export_timestamp": datetime.now().isoformat(),
            "plan_summary": {
                "total_mappings": len(migration_plan.mappings),
                "resource_filter": migration_plan.resource_filter,
                "resource_ids_count": len(migration_plan.resource_ids)
                if migration_plan.resource_ids
                else 0,
                "dry_run": migration_plan.dry_run,
                "cleanup_only": migration_plan.cleanup_only,
                "smart_migration": migration_plan.smart_migration,
            },
            "export_options": asdict(options),
        }

        # Convert migration plan to dict, handling transform functions
        plan_dict = self._serialize_migration_plan(migration_plan)

        export_data = MigrationPlanExport(metadata=metadata, plan=plan_dict)

        # Add conflicts if available and requested
        if conflicts and options.include_conflicts:
            export_data.conflicts = self._serialize_conflict_report(conflicts)

        # Add validation if requested and manager available
        if options.include_validation and self.migration_manager:
            export_data.validation_results = self._run_validation_for_export(
                migration_plan
            )

        return export_data

    def _serialize_migration_plan(
        self, migration_plan: MigrationPlan
    ) -> Dict[str, Any]:
        """Serialize migration plan to dictionary, handling special cases."""

        plan_dict = asdict(migration_plan)

        # Handle transform functions and enums in mappings
        for i, mapping in enumerate(plan_dict["mappings"]):
            # Convert enum to string
            mapping["strategy"] = migration_plan.mappings[i].strategy.value

            if migration_plan.mappings[i].transform_function:
                # Store function metadata instead of the function itself
                mapping["transform_function"] = {
                    "has_function": True,
                    "function_name": getattr(
                        migration_plan.mappings[i].transform_function,
                        "__name__",
                        "anonymous_function",
                    ),
                    "note": "Transform function cannot be serialized - will need to be recreated on import",
                }
            else:
                mapping["transform_function"] = None

        return plan_dict

    def _serialize_conflict_report(self, conflicts: ConflictReport) -> Dict[str, Any]:
        """Serialize conflict report to dictionary."""
        return asdict(conflicts)

    def _export_yaml(
        self,
        export_data: MigrationPlanExport,
        output_path: Path,
        options: ExportOptions,
    ):
        """Export to YAML format."""

        # Convert to dict for YAML serialization
        data = asdict(export_data)

        with open(output_path, "w") as f:
            if options.include_comments:
                # Add helpful comments
                f.write("# Neon CRM Migration Plan Export\n")
                f.write(f"# Generated: {export_data.metadata['export_timestamp']}\n")
                f.write("# \n")
                f.write(
                    "# IMPORTANT: Review this plan carefully before importing and executing!\n"
                )
                f.write("# \n")
                f.write("# To import and execute:\n")
                f.write("#   serializer = MigrationPlanSerializer(migration_manager)\n")
                f.write("#   plan = serializer.import_plan('this_file.yaml')\n")
                f.write("#   result = migration_manager.execute_migration_plan(plan)\n")
                f.write("# \n\n")

            yaml.dump(data, f, default_flow_style=False, indent=2, sort_keys=False)

    def _export_json(
        self,
        export_data: MigrationPlanExport,
        output_path: Path,
        options: ExportOptions,
    ):
        """Export to JSON format."""

        data = asdict(export_data)

        with open(output_path, "w") as f:
            json.dump(data, f, indent=2 if options.human_readable else None)

    def _export_csv(
        self,
        export_data: MigrationPlanExport,
        output_path: Path,
        options: ExportOptions,
    ):
        """Export to CSV format (mappings only)."""

        with open(output_path, "w", newline="") as f:
            writer = csv.writer(f)

            # Header
            writer.writerow(
                [
                    "source_field",
                    "target_field",
                    "strategy",
                    "preserve_source",
                    "validation_required",
                    "has_transform_function",
                    "notes",
                ]
            )

            # Mappings
            for mapping in export_data.plan["mappings"]:
                has_transform = mapping.get("transform_function") and mapping[
                    "transform_function"
                ].get("has_function", False)

                writer.writerow(
                    [
                        mapping["source_field"],
                        mapping["target_field"],
                        mapping["strategy"],
                        mapping["preserve_source"],
                        mapping["validation_required"],
                        has_transform,
                        "Requires transform function recreation"
                        if has_transform
                        else "",
                    ]
                )

            # Add metadata as comments at the end
            if options.include_metadata:
                writer.writerow([])
                writer.writerow(["# Metadata"])
                writer.writerow(
                    ["# Export timestamp:", export_data.metadata["export_timestamp"]]
                )
                writer.writerow(
                    [
                        "# Total mappings:",
                        export_data.metadata["plan_summary"]["total_mappings"],
                    ]
                )
                writer.writerow(
                    ["# Dry run:", export_data.metadata["plan_summary"]["dry_run"]]
                )

    def _import_yaml(self, file_path: Path) -> Dict[str, Any]:
        """Import from YAML format."""
        with open(file_path) as f:
            return yaml.safe_load(f)

    def _import_json(self, file_path: Path) -> Dict[str, Any]:
        """Import from JSON format."""
        with open(file_path) as f:
            return json.load(f)

    def _import_csv(self, file_path: Path) -> Dict[str, Any]:
        """Import from CSV format."""
        mappings = []

        with open(file_path) as f:
            reader = csv.DictReader(f)

            for row in reader:
                # Skip comment rows
                if row.get("source_field", "").startswith("#"):
                    continue

                mapping = {
                    "source_field": row["source_field"],
                    "target_field": row["target_field"],
                    "strategy": row["strategy"],
                    "preserve_source": row["preserve_source"].lower() == "true",
                    "validation_required": row["validation_required"].lower() == "true",
                    "transform_function": None,
                }

                # Handle transform function indication
                if row.get("has_transform_function", "").lower() == "true":
                    mapping["transform_function"] = {
                        "has_function": True,
                        "note": "Transform function needs to be recreated",
                    }

                mappings.append(mapping)

        # Create minimal export structure for CSV imports
        return {
            "metadata": {
                "export_timestamp": datetime.now().isoformat(),
                "plan_summary": {"total_mappings": len(mappings)},
            },
            "plan": {
                "mappings": mappings,
                "resource_filter": None,
                "resource_ids": None,
                "cleanup_only": False,
                "smart_migration": False,
                "batch_size": 100,
                "max_workers": 5,
                "dry_run": True,
            },
        }

    def _reconstruct_migration_plan(self, export_data: Dict[str, Any]) -> MigrationPlan:
        """Reconstruct MigrationPlan from exported data."""

        plan_data = export_data["plan"]

        # Reconstruct mappings
        mappings = []
        for mapping_data in plan_data["mappings"]:
            mapping = MigrationMapping(
                source_field=mapping_data["source_field"],
                target_field=mapping_data["target_field"],
                strategy=MigrationStrategy(mapping_data["strategy"]),
                transform_function=None,  # Will need to be recreated
                validation_required=mapping_data["validation_required"],
                preserve_source=mapping_data["preserve_source"],
            )

            # Log warning if transform function was present
            if mapping_data.get("transform_function") and mapping_data[
                "transform_function"
            ].get("has_function"):
                self.logger.warning(
                    f"Mapping {mapping.source_field} -> {mapping.target_field} "
                    "had a transform function that needs to be recreated"
                )

            mappings.append(mapping)

        # Reconstruct migration plan
        migration_plan = MigrationPlan(
            mappings=mappings,
            resource_filter=plan_data.get("resource_filter"),
            resource_ids=plan_data.get("resource_ids"),
            cleanup_only=plan_data.get("cleanup_only", False),
            smart_migration=plan_data.get("smart_migration", False),
            batch_size=plan_data.get("batch_size", 100),
            max_workers=plan_data.get("max_workers", 5),
            dry_run=plan_data.get("dry_run", True),
        )

        return migration_plan

    def _validate_field_existence(
        self, migration_plan: MigrationPlan
    ) -> Dict[str, Any]:
        """Validate that all fields in the plan exist."""

        missing_fields = []
        field_info = {}

        for mapping in migration_plan.mappings:
            # Check source field
            try:
                source_field = (
                    self.migration_manager._resource.find_custom_field_by_name(
                        mapping.source_field
                    )
                )
                if not source_field:
                    missing_fields.append(f"source: {mapping.source_field}")
                else:
                    field_info[mapping.source_field] = source_field
            except Exception as e:
                missing_fields.append(f"source: {mapping.source_field} (error: {e})")

            # Check target field
            try:
                target_field = (
                    self.migration_manager._resource.find_custom_field_by_name(
                        mapping.target_field
                    )
                )
                if not target_field:
                    missing_fields.append(f"target: {mapping.target_field}")
                else:
                    field_info[mapping.target_field] = target_field
            except Exception as e:
                missing_fields.append(f"target: {mapping.target_field} (error: {e})")

        return {
            "missing_fields": missing_fields,
            "found_fields": list(field_info.keys()),
            "field_info": field_info,
        }

    def _validate_timestamp_freshness(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Check if the exported plan is stale."""

        export_time_str = metadata.get("export_timestamp")
        if not export_time_str:
            return {"stale": False, "reason": "No timestamp found"}

        try:
            export_time = datetime.fromisoformat(export_time_str)
            age = datetime.now() - export_time
            age_hours = age.total_seconds() / 3600

            # Consider stale if older than 24 hours
            stale = age_hours > 24

            return {
                "stale": stale,
                "age_hours": age_hours,
                "export_time": export_time_str,
            }
        except Exception as e:
            return {"stale": False, "reason": f"Invalid timestamp: {e}"}

    def _run_validation_for_export(
        self, migration_plan: MigrationPlan
    ) -> Dict[str, Any]:
        """Run validation for export purposes."""

        try:
            conflicts = self.migration_manager.analyze_migration_conflicts(
                migration_plan
            )

            return {
                "has_field_conflicts": bool(conflicts.field_conflicts),
                "has_type_conflicts": bool(conflicts.type_conflicts),
                "has_value_conflicts": bool(conflicts.value_conflicts),
                "total_suggestions": len(conflicts.resolution_suggestions),
                "validation_timestamp": datetime.now().isoformat(),
            }
        except Exception as e:
            return {
                "validation_error": str(e),
                "validation_timestamp": datetime.now().isoformat(),
            }


def create_migration_plan_template(
    source_fields: List[str], target_field_mapping: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """Create a template migration plan that can be manually edited.

    Args:
        source_fields: List of source field names
        target_field_mapping: Optional mapping of source -> target fields

    Returns:
        Dictionary template for migration plan
    """

    mappings = []

    for source_field in source_fields:
        target_field = (
            target_field_mapping.get(source_field, "TODO_SPECIFY_TARGET")
            if target_field_mapping
            else "TODO_SPECIFY_TARGET"
        )

        mapping = {
            "source_field": source_field,
            "target_field": target_field,
            "strategy": "COPY_IF_EMPTY",  # Safe default
            "preserve_source": True,  # Safe default
            "validation_required": True,
            "transform_function": None,
            "notes": "TODO: Review and configure this mapping",
        }
        mappings.append(mapping)

    template = {
        "metadata": {
            "created_timestamp": datetime.now().isoformat(),
            "template_version": "1.0",
            "notes": [
                "This is a migration plan template",
                "Review and update all TODO items before importing",
                "Test with dry_run=True first",
            ],
        },
        "plan": {
            "mappings": mappings,
            "resource_filter": None,
            "resource_ids": None,
            "cleanup_only": False,
            "smart_migration": False,
            "batch_size": 100,
            "max_workers": 5,
            "dry_run": True,
        },
    }

    return template
