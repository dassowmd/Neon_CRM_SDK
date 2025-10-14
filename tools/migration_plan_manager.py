#!/usr/bin/env python3
"""Migration Plan Manager - Export, Import, and Validate Migration Plans.

This utility provides command-line functionality to:
1. Export migration plans to human-readable formats (YAML, JSON, CSV)
2. Import and validate migration plans
3. Create migration plan templates
4. Show plan differences and conflicts
"""

import sys
import os
import argparse
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from neon_crm import NeonClient
from neon_crm.migration_tools.base import (
    MigrationPlan,
    MigrationMapping,
    MigrationStrategy,
)
from neon_crm.migration_tools.plan_serializer import (
    MigrationPlanSerializer,
    ExportOptions,
    create_migration_plan_template,
)
from neon_crm.migration_tools.accounts import AccountsMigrationManager

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def create_sample_migration_plan() -> MigrationPlan:
    """Create a sample migration plan for testing."""
    mappings = [
        MigrationMapping(
            source_field="V-Canvassing",
            target_field="V-Volunteer Campaign & Election Activities",
            strategy=MigrationStrategy.ADD_OPTION,
            preserve_source=False,
            transform_function=lambda x: "Canvassing/literature Drop" if x else None,
        ),
        MigrationMapping(
            source_field="V-Data Entry",
            target_field="V-Volunteer Skills",
            strategy=MigrationStrategy.ADD_OPTION,
            preserve_source=False,
            transform_function=lambda x: "Data Entry" if x else None,
        ),
        MigrationMapping(
            source_field="V-Phone Banking",
            target_field="V-Volunteer Campaign & Election Activities",
            strategy=MigrationStrategy.ADD_OPTION,
            preserve_source=False,
            transform_function=lambda x: "Phone Banking" if x else None,
        ),
        MigrationMapping(
            source_field="V-Text Banking",
            target_field="V-Volunteer Campaign & Election Activities",
            strategy=MigrationStrategy.ADD_OPTION,
            preserve_source=False,
            transform_function=lambda x: "Text Banking" if x else None,
        ),
    ]

    return MigrationPlan(
        mappings=mappings,
        resource_ids=[6488, 1234, 5678],  # Example resource IDs
        cleanup_only=False,
        smart_migration=True,
        batch_size=50,
        max_workers=3,
        dry_run=True,
    )


def export_migration_plan(args):
    """Export a migration plan to a file."""
    print(f"🔄 Exporting migration plan...")

    # For demo, create a sample plan
    # In real usage, this would come from your migration analysis
    migration_plan = create_sample_migration_plan()

    # Setup export options
    options = ExportOptions(
        format=args.format,
        include_metadata=args.include_metadata,
        include_conflicts=args.include_conflicts,
        include_validation=args.include_validation,
        human_readable=args.human_readable,
        include_comments=args.include_comments,
    )

    # Initialize serializer
    serializer = MigrationPlanSerializer()

    # Add conflicts if available (for demo, create sample conflicts)
    conflicts = None
    if args.include_conflicts and args.validate:
        try:
            # Connect to Neon CRM for validation
            client = NeonClient()
            migration_manager = AccountsMigrationManager(
                client.accounts, client, "accounts"
            )
            serializer = MigrationPlanSerializer(migration_manager)

            conflicts = migration_manager.analyze_migration_conflicts(migration_plan)
            print(
                f"✅ Analyzed conflicts: {len(conflicts.field_conflicts)} field conflicts found"
            )
        except Exception as e:
            print(f"⚠️  Could not analyze conflicts: {e}")

    # Export the plan
    output_path = serializer.export_plan(
        migration_plan=migration_plan,
        output_path=args.output,
        options=options,
        conflicts=conflicts,
    )

    print(f"✅ Migration plan exported to: {output_path}")
    print(f"📊 Plan summary:")
    print(f"   - Mappings: {len(migration_plan.mappings)}")
    print(
        f"   - Resource IDs: {len(migration_plan.resource_ids) if migration_plan.resource_ids else 'All'}"
    )
    print(f"   - Dry run: {migration_plan.dry_run}")
    print(f"   - Smart migration: {migration_plan.smart_migration}")

    # Show file size
    file_size = output_path.stat().st_size
    print(f"   - File size: {file_size} bytes")

    return output_path


def import_migration_plan(args):
    """Import a migration plan from a file."""
    print(f"📥 Importing migration plan from: {args.input}")

    # Check file exists
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"❌ File not found: {input_path}")
        return None

    # Initialize serializer
    serializer = MigrationPlanSerializer()

    if args.validate:
        try:
            client = NeonClient()
            migration_manager = AccountsMigrationManager(
                client.accounts, client, "accounts"
            )
            serializer = MigrationPlanSerializer(migration_manager)
        except Exception as e:
            print(f"⚠️  Could not connect to Neon CRM for validation: {e}")

    # Import the plan
    try:
        migration_plan = serializer.import_plan(input_path)
        print(f"✅ Migration plan imported successfully")

        # Validate if requested
        if args.validate and serializer.migration_manager:
            print(f"🔍 Validating imported plan...")
            validation_results = serializer.validate_imported_plan(migration_plan)

            if validation_results["valid"]:
                print(f"✅ Plan validation passed")
            else:
                print(f"❌ Plan validation failed:")
                for error in validation_results["errors"]:
                    print(f"   - {error}")

            if validation_results["warnings"]:
                print(f"⚠️  Warnings:")
                for warning in validation_results["warnings"]:
                    print(f"   - {warning}")

        # Show plan summary
        print(f"📊 Imported plan summary:")
        print(f"   - Mappings: {len(migration_plan.mappings)}")
        for i, mapping in enumerate(migration_plan.mappings[:5], 1):
            print(
                f"     {i}. {mapping.source_field} -> {mapping.target_field} ({mapping.strategy.value})"
            )
        if len(migration_plan.mappings) > 5:
            print(f"     ... and {len(migration_plan.mappings) - 5} more mappings")

        print(
            f"   - Resource IDs: {len(migration_plan.resource_ids) if migration_plan.resource_ids else 'All'}"
        )
        print(f"   - Dry run: {migration_plan.dry_run}")
        print(f"   - Smart migration: {migration_plan.smart_migration}")

        return migration_plan

    except Exception as e:
        print(f"❌ Failed to import migration plan: {e}")
        return None


def create_template(args):
    """Create a migration plan template."""
    print(f"📝 Creating migration plan template...")

    # Example source fields (in real usage, these would come from field discovery)
    # Using standardized field names from field_name_standards.md
    source_fields = [
        "V-Canvassing",
        "V-Data Entry",
        "V-Phone Banking",
        "V-Text Banking",
        "V-Graphic Design",
        "V-Event Planning",
        "V-Transportation",
        "V-Food & Hospitality",
        "V-Office Support",
        "V-Technology Support",
    ]

    # Create template
    template = create_migration_plan_template(source_fields)

    # Save to file
    output_path = Path(args.output)

    if output_path.suffix.lower() in [".yaml", ".yml"]:
        import yaml

        with open(output_path, "w") as f:
            f.write("# Migration Plan Template\n")
            f.write("# \n")
            f.write("# TODO: Review and update all mappings before using\n")
            f.write("# TODO: Update target field names\n")
            f.write("# TODO: Configure strategies and options\n")
            f.write("# \n\n")
            yaml.dump(template, f, default_flow_style=False, indent=2, sort_keys=False)
    else:
        import json

        with open(output_path, "w") as f:
            json.dump(template, f, indent=2)

    print(f"✅ Template created: {output_path}")
    print(f"📊 Template includes:")
    print(f"   - {len(source_fields)} source fields to map")
    print(f"   - Placeholder target fields (need configuration)")
    print(f"   - Safe default settings (dry_run=True, preserve_source=True)")

    print(f"\n📝 Next steps:")
    print(f"   1. Edit {output_path} to configure target fields")
    print(f"   2. Review and update mapping strategies")
    print(
        f"   3. Import and validate: python {__file__} import --input {output_path} --validate"
    )

    return output_path


def show_plan_info(args):
    """Show information about a migration plan file."""
    print(f"ℹ️  Analyzing migration plan: {args.input}")

    # Import the plan
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"❌ File not found: {input_path}")
        return

    serializer = MigrationPlanSerializer()

    try:
        migration_plan = serializer.import_plan(input_path)

        print(f"📊 Migration Plan Analysis")
        print(f"{'='*50}")
        print(f"File: {input_path}")
        print(f"Size: {input_path.stat().st_size} bytes")
        print(f"")

        print(f"📋 Plan Configuration:")
        print(f"   Mappings: {len(migration_plan.mappings)}")
        print(f"   Batch size: {migration_plan.batch_size}")
        print(f"   Max workers: {migration_plan.max_workers}")
        print(f"   Dry run: {migration_plan.dry_run}")
        print(f"   Cleanup only: {migration_plan.cleanup_only}")
        print(f"   Smart migration: {migration_plan.smart_migration}")

        if migration_plan.resource_ids:
            print(
                f"   Target resources: {len(migration_plan.resource_ids)} specific IDs"
            )
        elif migration_plan.resource_filter:
            print(f"   Target resources: Filtered resources")
        else:
            print(f"   Target resources: All resources")

        print(f"")
        print(f"🔀 Field Mappings:")
        for i, mapping in enumerate(migration_plan.mappings, 1):
            preserve = "preserve" if mapping.preserve_source else "clear"
            validation = "validate" if mapping.validation_required else "no-validate"
            transform = "transform" if mapping.transform_function else "direct"

            print(f"   {i:2d}. {mapping.source_field}")
            print(f"       -> {mapping.target_field}")
            print(
                f"       -> Strategy: {mapping.strategy.value}, {preserve}, {validation}, {transform}"
            )

        # Strategy breakdown
        strategy_counts = {}
        for mapping in migration_plan.mappings:
            strategy = mapping.strategy.value
            strategy_counts[strategy] = strategy_counts.get(strategy, 0) + 1

        print(f"")
        print(f"📈 Strategy Breakdown:")
        for strategy, count in strategy_counts.items():
            print(f"   {strategy}: {count} mappings")

        # Source preservation analysis
        preserve_count = sum(1 for m in migration_plan.mappings if m.preserve_source)
        clear_count = len(migration_plan.mappings) - preserve_count

        print(f"")
        print(f"🗑️  Source Field Handling:")
        print(f"   Preserve: {preserve_count} fields")
        print(f"   Clear: {clear_count} fields")

    except Exception as e:
        print(f"❌ Failed to analyze plan: {e}")


def main():
    """Main command-line interface."""
    parser = argparse.ArgumentParser(
        description="Migration Plan Manager - Export, Import, and Validate Migration Plans"
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Export command
    export_parser = subparsers.add_parser("export", help="Export a migration plan")
    export_parser.add_argument("--output", "-o", required=True, help="Output file path")
    export_parser.add_argument(
        "--format",
        "-f",
        default="yaml",
        choices=["yaml", "json", "csv"],
        help="Export format (default: yaml)",
    )
    export_parser.add_argument(
        "--no-metadata",
        dest="include_metadata",
        action="store_false",
        help="Exclude metadata from export",
    )
    export_parser.add_argument(
        "--no-conflicts",
        dest="include_conflicts",
        action="store_false",
        help="Exclude conflict analysis from export",
    )
    export_parser.add_argument(
        "--no-validation",
        dest="include_validation",
        action="store_false",
        help="Exclude validation results from export",
    )
    export_parser.add_argument(
        "--compact",
        dest="human_readable",
        action="store_false",
        help="Use compact format (no pretty printing)",
    )
    export_parser.add_argument(
        "--no-comments",
        dest="include_comments",
        action="store_false",
        help="Exclude comments from export",
    )
    export_parser.add_argument(
        "--validate", action="store_true", help="Connect to Neon CRM to validate fields"
    )

    # Import command
    import_parser = subparsers.add_parser("import", help="Import a migration plan")
    import_parser.add_argument("--input", "-i", required=True, help="Input file path")
    import_parser.add_argument(
        "--validate",
        action="store_true",
        help="Validate imported plan against Neon CRM",
    )

    # Template command
    template_parser = subparsers.add_parser(
        "template", help="Create a migration plan template"
    )
    template_parser.add_argument(
        "--output", "-o", required=True, help="Output file path"
    )

    # Info command
    info_parser = subparsers.add_parser(
        "info", help="Show information about a migration plan"
    )
    info_parser.add_argument("--input", "-i", required=True, help="Input file path")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    try:
        if args.command == "export":
            export_migration_plan(args)
        elif args.command == "import":
            import_migration_plan(args)
        elif args.command == "template":
            create_template(args)
        elif args.command == "info":
            show_plan_info(args)
    except KeyboardInterrupt:
        print(f"\n⏹️  Operation cancelled by user")
    except Exception as e:
        print(f"❌ Error: {e}")
        logger.exception("Unexpected error occurred")


if __name__ == "__main__":
    main()
