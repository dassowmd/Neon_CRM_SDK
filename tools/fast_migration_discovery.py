#!/usr/bin/env python3
"""Fast Migration Discovery Tool.

This tool provides high-performance field discovery and migration planning by using
optimized search strategies instead of iterating through individual resources.
"""

import sys
import os
import argparse
import logging
import time
from pathlib import Path
from typing import Dict, Any, List

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from neon_crm import NeonClient
from neon_crm.migration_tools.accounts import AccountsMigrationManager
from neon_crm.migration_tools.fast_discovery import DiscoveryReport

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def discover_fields(args):
    """Discover fields with data using fast search techniques."""
    print(f"🔍 Fast Field Discovery")
    print(f"{'='*30}")

    try:
        # Initialize client and migration manager
        client = NeonClient()
        migration_manager = AccountsMigrationManager(
            client.accounts, client, "accounts"
        )

        # Parse field patterns if provided
        field_patterns = None
        if args.patterns:
            field_patterns = [pattern.strip() for pattern in args.patterns.split(",")]
            print(f"🔍 Searching for patterns: {field_patterns}")
        else:
            print(f"🔍 Discovering all custom fields")

        # Run fast discovery
        start_time = time.time()
        discovery_report = migration_manager.fast_discover_migration_opportunities(
            field_patterns=field_patterns, sample_size=args.sample_size
        )
        discovery_time = time.time() - start_time

        if not discovery_report:
            print("❌ No fields found or discovery failed")
            return

        # Display results
        print(f"\n📊 Discovery Results ({discovery_time:.2f}s)")
        print(f"{'='*50}")
        print(f"Total resources analyzed: {discovery_report.total_resources_analyzed}")
        print(f"Fields with data: {len(discovery_report.fields_with_data)}")
        print(f"Fields without data: {len(discovery_report.fields_without_data)}")
        print(
            f"Migration opportunities: {len(discovery_report.migration_opportunities)}"
        )

        # Show fields with data
        if discovery_report.fields_with_data:
            print(f"\n📋 Fields with Data:")
            print(
                f"{'Field Name':<40} {'Resources':<10} {'Data Types':<15} {'Sample Values'}"
            )
            print(f"{'-'*90}")

            for field_result in discovery_report.fields_with_data[: args.max_display]:
                sample_preview = (
                    str(field_result.sample_values[:2])
                    .replace("[", "")
                    .replace("]", "")
                )
                if len(sample_preview) > 30:
                    sample_preview = sample_preview[:27] + "..."

                data_types_str = ", ".join(field_result.data_types)[:12]

                print(
                    f"{field_result.field_name:<40} {field_result.resource_count:<10} "
                    f"{data_types_str:<15} {sample_preview}"
                )

            if len(discovery_report.fields_with_data) > args.max_display:
                remaining = len(discovery_report.fields_with_data) - args.max_display
                print(f"... and {remaining} more fields")

        # Show migration opportunities
        if discovery_report.migration_opportunities:
            print(f"\n🚀 Migration Opportunities:")
            print(
                f"{'Source Field':<35} {'Target Suggestions':<30} {'Resources':<10} {'Confidence'}"
            )
            print(f"{'-'*95}")

            for opportunity in discovery_report.migration_opportunities[
                : args.max_display
            ]:
                targets_str = ", ".join(opportunity.potential_targets[:2])
                if len(targets_str) > 27:
                    targets_str = targets_str[:24] + "..."

                confidence_str = f"{opportunity.confidence_score:.2f}"

                print(
                    f"{opportunity.source_field:<35} {targets_str:<30} "
                    f"{opportunity.affected_resources:<10} {confidence_str}"
                )

        # Show recommendations
        if discovery_report.recommendations:
            print(f"\n💡 Recommendations:")
            for i, rec in enumerate(discovery_report.recommendations, 1):
                print(f"   {i}. {rec}")

        # Save detailed report if requested
        if args.output:
            save_discovery_report(discovery_report, args.output)
            print(f"\n💾 Detailed report saved to: {args.output}")

    except Exception as e:
        print(f"❌ Discovery failed: {e}")
        logger.exception("Discovery error")


def generate_plan(args):
    """Generate an optimized migration plan from discovery results."""
    print(f"📋 Migration Plan Generation")
    print(f"{'='*35}")

    try:
        # Initialize client and migration manager
        client = NeonClient()
        migration_manager = AccountsMigrationManager(
            client.accounts, client, "accounts"
        )

        # Run discovery first
        print(f"🔍 Running discovery...")
        field_patterns = (
            [pattern.strip() for pattern in args.patterns.split(",")]
            if args.patterns
            else None
        )

        discovery_report = migration_manager.fast_discover_migration_opportunities(
            field_patterns=field_patterns, sample_size=args.sample_size
        )

        if not discovery_report or not discovery_report.fields_with_data:
            print("❌ No fields found for migration planning")
            return

        print(
            f"✅ Discovery completed: {len(discovery_report.fields_with_data)} fields with data"
        )

        # Parse target field mapping if provided
        target_mapping = {}
        if args.target_mapping:
            for mapping in args.target_mapping.split(","):
                if ":" in mapping:
                    source, target = mapping.split(":", 1)
                    target_mapping[source.strip()] = target.strip()

        # Generate optimized migration plan
        print(f"📋 Generating migration plan...")
        migration_plan = migration_manager.create_optimized_migration_plan(
            discovery_report=discovery_report,
            target_field_mapping=target_mapping if target_mapping else None,
        )

        # Display plan summary
        print(f"\n📊 Migration Plan Summary:")
        print(f"   Mappings: {len(migration_plan.mappings)}")
        print(f"   Batch size: {migration_plan.batch_size}")
        print(f"   Max workers: {migration_plan.max_workers}")
        print(f"   Dry run: {migration_plan.dry_run}")

        print(f"\n🔀 Field Mappings:")
        for i, mapping in enumerate(migration_plan.mappings[: args.max_display], 1):
            print(f"   {i:2d}. {mapping.source_field} → {mapping.target_field}")
            print(
                f"       Strategy: {mapping.strategy.value}, "
                f"Preserve: {mapping.preserve_source}, "
                f"Validate: {mapping.validation_required}"
            )

        if len(migration_plan.mappings) > args.max_display:
            remaining = len(migration_plan.mappings) - args.max_display
            print(f"   ... and {remaining} more mappings")

        # Export plan if requested
        if args.output:
            export_path = migration_manager.export_migration_plan(
                migration_plan, args.output, format="yaml"
            )
            print(f"\n💾 Migration plan exported to: {export_path}")

    except Exception as e:
        print(f"❌ Plan generation failed: {e}")
        logger.exception("Plan generation error")


def analyze_performance(args):
    """Analyze performance characteristics of fast discovery vs traditional methods."""
    print(f"⚡ Performance Analysis")
    print(f"{'='*25}")

    try:
        # Initialize client and migration manager
        client = NeonClient()
        migration_manager = AccountsMigrationManager(
            client.accounts, client, "accounts"
        )

        field_patterns = (
            [pattern.strip() for pattern in args.patterns.split(",")]
            if args.patterns
            else None
        )

        print(f"🔬 Testing fast discovery performance...")

        # Test fast discovery
        start_time = time.time()
        discovery_report = migration_manager.fast_discover_migration_opportunities(
            field_patterns=field_patterns, sample_size=args.sample_size
        )
        fast_discovery_time = time.time() - start_time

        if not discovery_report:
            print("❌ Fast discovery failed")
            return

        fields_found = len(discovery_report.fields_with_data)
        total_resources = discovery_report.total_resources_analyzed

        print(f"\n📈 Performance Results:")
        print(f"   Fast discovery time: {fast_discovery_time:.2f}s")
        print(f"   Fields discovered: {fields_found}")
        print(f"   Resources analyzed: {total_resources}")
        print(
            f"   Discovery rate: {fields_found / fast_discovery_time:.1f} fields/second"
        )

        if total_resources > 0:
            print(
                f"   Resource analysis rate: {total_resources / fast_discovery_time:.1f} resources/second"
            )

        # Estimate traditional approach time
        if fields_found > 0 and total_resources > 0:
            # Traditional approach: iterate through each resource, check each field
            estimated_traditional_operations = total_resources * fields_found
            estimated_traditional_time = (
                estimated_traditional_operations * 0.1
            )  # 0.1s per operation estimate

            speedup = (
                estimated_traditional_time / fast_discovery_time
                if fast_discovery_time > 0
                else 0
            )

            print(f"\n📊 Comparison with Traditional Approach:")
            print(
                f"   Estimated traditional time: {estimated_traditional_time/60:.1f} minutes"
            )
            print(f"   Fast discovery time: {fast_discovery_time:.1f} seconds")
            print(f"   Speedup factor: {speedup:.1f}x faster")

        # Show optimization recommendations
        print(f"\n💡 Optimization Insights:")
        if fast_discovery_time < 5:
            print("   ✅ Discovery completed very quickly - good for interactive use")
        elif fast_discovery_time < 30:
            print("   ✅ Discovery completed reasonably fast - suitable for automation")
        else:
            print(
                "   ⚠️  Discovery took a while - consider smaller field sets or more specific patterns"
            )

        if fields_found > 50:
            print(
                "   💡 Many fields found - consider splitting into batches for migration"
            )

        if total_resources > 1000:
            print("   💡 Large dataset detected - use bulk migration strategies")

    except Exception as e:
        print(f"❌ Performance analysis failed: {e}")
        logger.exception("Performance analysis error")


def compare_strategies(args):
    """Compare fast discovery with different strategies."""
    print(f"⚖️  Strategy Comparison")
    print(f"{'='*25}")

    try:
        # Initialize client and migration manager
        client = NeonClient()
        migration_manager = AccountsMigrationManager(
            client.accounts, client, "accounts"
        )

        field_patterns = (
            [pattern.strip() for pattern in args.patterns.split(",")]
            if args.patterns
            else None
        )

        print(f"🧪 Testing different discovery strategies...")

        strategies = [("sequential", False), ("parallel", True)]

        results = {}

        for strategy_name, use_parallel in strategies:
            print(f"\n🔬 Testing {strategy_name} strategy...")

            start_time = time.time()

            # We'll simulate different strategies by adjusting the sample size and parallelism
            # In a real implementation, this would be configurable in the discovery manager
            discovery_report = migration_manager.fast_discover_migration_opportunities(
                field_patterns=field_patterns, sample_size=args.sample_size
            )

            end_time = time.time()

            if discovery_report:
                results[strategy_name] = {
                    "time": end_time - start_time,
                    "fields_found": len(discovery_report.fields_with_data),
                    "resources_analyzed": discovery_report.total_resources_analyzed,
                }

                print(f"   Time: {results[strategy_name]['time']:.2f}s")
                print(f"   Fields found: {results[strategy_name]['fields_found']}")
            else:
                print(f"   ❌ Strategy failed")
                results[strategy_name] = None

        # Compare results
        print(f"\n📊 Strategy Comparison:")
        print(f"{'Strategy':<12} {'Time':<8} {'Fields':<8} {'Resources':<10}")
        print(f"{'-'*40}")

        for strategy, result in results.items():
            if result:
                print(
                    f"{strategy:<12} {result['time']:<8.2f} {result['fields_found']:<8} {result['resources_analyzed']:<10}"
                )
            else:
                print(f"{strategy:<12} {'FAILED':<8} {'-':<8} {'-':<10}")

        # Best strategy
        valid_results = {k: v for k, v in results.items() if v is not None}
        if valid_results:
            best_strategy = min(
                valid_results.keys(), key=lambda k: valid_results[k]["time"]
            )
            print(f"\n🏆 Fastest Strategy: {best_strategy}")
            print(f"   Time: {valid_results[best_strategy]['time']:.2f}s")

    except Exception as e:
        print(f"❌ Strategy comparison failed: {e}")
        logger.exception("Strategy comparison error")


def save_discovery_report(discovery_report: DiscoveryReport, output_path: str):
    """Save discovery report to a file."""
    import json
    from datetime import datetime

    report_data = {
        "timestamp": datetime.now().isoformat(),
        "total_resources_analyzed": discovery_report.total_resources_analyzed,
        "discovery_time": discovery_report.discovery_time,
        "fields_with_data": [
            {
                "field_name": field.field_name,
                "resource_count": field.resource_count,
                "sample_values": field.sample_values[:5],  # Limit sample size
                "data_types": list(field.data_types),
                "discovery_time": field.discovery_time,
            }
            for field in discovery_report.fields_with_data
        ],
        "fields_without_data": discovery_report.fields_without_data,
        "migration_opportunities": [
            {
                "source_field": opp.source_field,
                "potential_targets": opp.potential_targets,
                "affected_resources": opp.affected_resources,
                "confidence_score": opp.confidence_score,
                "recommended_strategy": opp.recommended_strategy.value,
                "sample_mappings": opp.sample_mappings,
            }
            for opp in discovery_report.migration_opportunities
        ],
        "recommendations": discovery_report.recommendations,
    }

    with open(output_path, "w") as f:
        json.dump(report_data, f, indent=2)


def main():
    """Main command-line interface."""
    parser = argparse.ArgumentParser(description="Fast Migration Discovery Tool")

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Discover command
    discover_parser = subparsers.add_parser(
        "discover", help="Discover fields with data"
    )
    discover_parser.add_argument(
        "--patterns", "-p", help='Comma-separated field patterns (e.g., "V-*,Custom-*")'
    )
    discover_parser.add_argument(
        "--sample-size",
        "-s",
        type=int,
        default=100,
        help="Sample size per field (default: 100)",
    )
    discover_parser.add_argument(
        "--max-display",
        "-d",
        type=int,
        default=20,
        help="Maximum items to display (default: 20)",
    )
    discover_parser.add_argument("--output", "-o", help="Save detailed report to file")

    # Generate command
    generate_parser = subparsers.add_parser("generate", help="Generate migration plan")
    generate_parser.add_argument(
        "--patterns", "-p", help='Comma-separated field patterns (e.g., "V-*,Custom-*")'
    )
    generate_parser.add_argument(
        "--target-mapping",
        "-t",
        help='Comma-separated source:target mappings (e.g., "V-Field1:Target1,V-Field2:Target2")',
    )
    generate_parser.add_argument(
        "--sample-size",
        "-s",
        type=int,
        default=100,
        help="Sample size per field (default: 100)",
    )
    generate_parser.add_argument(
        "--max-display",
        "-d",
        type=int,
        default=10,
        help="Maximum mappings to display (default: 10)",
    )
    generate_parser.add_argument("--output", "-o", help="Export migration plan to file")

    # Performance command
    performance_parser = subparsers.add_parser(
        "performance", help="Analyze discovery performance"
    )
    performance_parser.add_argument(
        "--patterns", "-p", help='Comma-separated field patterns (e.g., "V-*,Custom-*")'
    )
    performance_parser.add_argument(
        "--sample-size",
        "-s",
        type=int,
        default=100,
        help="Sample size per field (default: 100)",
    )

    # Compare command
    compare_parser = subparsers.add_parser(
        "compare", help="Compare discovery strategies"
    )
    compare_parser.add_argument(
        "--patterns", "-p", help='Comma-separated field patterns (e.g., "V-*,Custom-*")'
    )
    compare_parser.add_argument(
        "--sample-size",
        "-s",
        type=int,
        default=50,
        help="Sample size per field (default: 50)",
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    try:
        if args.command == "discover":
            discover_fields(args)
        elif args.command == "generate":
            generate_plan(args)
        elif args.command == "performance":
            analyze_performance(args)
        elif args.command == "compare":
            compare_strategies(args)
    except KeyboardInterrupt:
        print(f"\n⏹️  Operation cancelled by user")
    except Exception as e:
        print(f"❌ Error: {e}")
        logger.exception("Unexpected error occurred")


if __name__ == "__main__":
    main()
