#!/usr/bin/env python3
"""Migration Performance Tester and Benchmarking Tool.

This tool helps analyze and optimize migration performance by:
1. Benchmarking different migration strategies
2. Analyzing performance bottlenecks
3. Providing optimization recommendations
4. Comparing performance across different configurations
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
from neon_crm.migration_tools.base import (
    MigrationPlan,
    MigrationMapping,
    MigrationStrategy,
)
from neon_crm.migration_tools.bulk_migration import PerformanceMetrics

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def create_test_migration_plan(
    resource_ids: List[int], mapping_count: int = 3
) -> MigrationPlan:
    """Create a test migration plan for benchmarking."""

    # Create sample mappings
    test_mappings = [
        MigrationMapping(
            source_field=f"Test-Source-{i}",
            target_field=f"Test-Target-{i}",
            strategy=MigrationStrategy.ADD_OPTION,
            preserve_source=False,
            transform_function=lambda x, i=i: f"Option-{i}" if x else None,
        )
        for i in range(1, mapping_count + 1)
    ]

    return MigrationPlan(
        mappings=test_mappings,
        resource_ids=resource_ids,
        cleanup_only=False,
        smart_migration=True,
        batch_size=50,
        max_workers=3,
        dry_run=True,  # Always dry run for performance testing
    )


def benchmark_strategies(args):
    """Benchmark different migration strategies."""
    print(f"🔬 Benchmarking Migration Strategies")
    print(f"{'='*50}")

    try:
        # Initialize client and migration manager
        client = NeonClient()
        migration_manager = AccountsMigrationManager(
            client.accounts, client, "accounts"
        )

        # Get sample resource IDs
        if args.resource_ids:
            resource_ids = [int(id.strip()) for id in args.resource_ids.split(",")]
        else:
            # Get some sample resource IDs from the system
            print("🔍 Finding sample resource IDs for testing...")
            sample_accounts = list(client.accounts.list(page_size=args.sample_size))
            if not sample_accounts:
                print("❌ No accounts found for testing")
                return

            resource_ids = [
                acc.get("Account ID")
                for acc in sample_accounts
                if acc.get("Account ID")
            ][: args.sample_size]

        if len(resource_ids) < 5:
            print(
                f"⚠️  Warning: Only {len(resource_ids)} resource IDs available. Benchmarking may not be representative."
            )

        print(
            f"📊 Testing with {len(resource_ids)} resources, {args.mapping_count} mappings"
        )

        # Create test migration plan
        migration_plan = create_test_migration_plan(resource_ids, args.mapping_count)

        # Benchmark strategies
        print(f"\n🚀 Running benchmark...")
        benchmark_results = migration_manager.benchmark_migration_strategies(
            migration_plan, sample_size=len(resource_ids)
        )

        # Display results
        print(f"\n📈 Benchmark Results")
        print(f"{'='*60}")

        for strategy, metrics in benchmark_results.items():
            if metrics:
                print(f"\n🔧 {strategy.upper()} Strategy:")
                print(f"   Resources/second: {metrics.resources_per_second:.2f}")
                print(f"   API calls/second: {metrics.api_calls_per_second:.2f}")
                print(f"   Total time: {metrics.total_time:.2f}s")
                print(f"   Total API calls: {metrics.total_api_calls}")
                print(f"   Avg time/resource: {metrics.avg_time_per_resource:.3f}s")
                print(f"   Avg time/API call: {metrics.avg_time_per_api_call:.3f}s")
            else:
                print(f"\n❌ {strategy.upper()} Strategy: FAILED")

        # Find best strategy
        valid_results = {k: v for k, v in benchmark_results.items() if v is not None}
        if valid_results:
            best_strategy = max(
                valid_results.keys(),
                key=lambda k: valid_results[k].resources_per_second,
            )
            best_metrics = valid_results[best_strategy]

            print(f"\n🏆 Best Strategy: {best_strategy.upper()}")
            print(
                f"   Performance: {best_metrics.resources_per_second:.2f} resources/second"
            )

            # Calculate performance improvements
            baseline_strategy = "parallel"  # Use parallel as baseline
            if (
                baseline_strategy in valid_results
                and best_strategy != baseline_strategy
            ):
                baseline_perf = valid_results[baseline_strategy].resources_per_second
                improvement = (
                    (best_metrics.resources_per_second - baseline_perf) / baseline_perf
                ) * 100
                print(f"   Improvement over {baseline_strategy}: {improvement:.1f}%")

        # Get recommendations
        print(f"\n💡 Performance Recommendations")
        print(f"{'='*40}")
        recommendations = migration_manager.get_performance_recommendations(
            migration_plan
        )

        print(f"Recommended strategy: {recommendations['recommended_strategy']}")
        print(f"Estimated API calls: {recommendations['estimated_api_calls']}")

        for rec in recommendations["recommendations"]:
            print(f"• {rec}")

    except Exception as e:
        print(f"❌ Benchmark failed: {e}")
        logger.exception("Benchmark error")


def analyze_performance(args):
    """Analyze performance characteristics of a migration plan."""
    print(f"📊 Migration Performance Analysis")
    print(f"{'='*40}")

    try:
        # Initialize client and migration manager
        client = NeonClient()
        migration_manager = AccountsMigrationManager(
            client.accounts, client, "accounts"
        )

        # Parse resource IDs
        resource_ids = [int(id.strip()) for id in args.resource_ids.split(",")]

        print(f"🔍 Analyzing performance for {len(resource_ids)} resources")

        # Create migration plan
        migration_plan = create_test_migration_plan(resource_ids, args.mapping_count)

        # Get performance recommendations
        recommendations = migration_manager.get_performance_recommendations(
            migration_plan
        )

        print(f"\n📈 Analysis Results:")
        print(f"   Resource count: {len(resource_ids)}")
        print(f"   Mapping count: {args.mapping_count}")
        print(f"   Estimated API calls: {recommendations['estimated_api_calls']}")
        print(f"   Recommended strategy: {recommendations['recommended_strategy']}")

        # Calculate time estimates
        estimated_time_parallel = (
            recommendations["estimated_api_calls"] * 0.5
        )  # 0.5s per API call estimate
        estimated_time_bulk = (
            recommendations["estimated_api_calls"] * 0.2
        )  # Bulk operations are faster

        print(f"\n⏱️  Time Estimates:")
        print(f"   Standard approach: ~{estimated_time_parallel/60:.1f} minutes")
        print(f"   Bulk approach: ~{estimated_time_bulk/60:.1f} minutes")
        print(
            f"   Potential time savings: ~{(estimated_time_parallel-estimated_time_bulk)/60:.1f} minutes"
        )

        print(f"\n💡 Recommendations:")
        for rec in recommendations["recommendations"]:
            print(f"   • {rec}")

        # Memory usage estimates
        memory_per_resource = 2  # KB estimate per resource
        total_memory = len(resource_ids) * memory_per_resource
        print(f"\n💾 Memory Usage Estimate: ~{total_memory}KB")

        if total_memory > 10000:  # 10MB
            print(f"   ⚠️  High memory usage detected - consider smaller batch sizes")

    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        logger.exception("Analysis error")


def test_scalability(args):
    """Test how performance scales with different data sizes."""
    print(f"📈 Migration Scalability Testing")
    print(f"{'='*40}")

    try:
        # Initialize client and migration manager
        client = NeonClient()
        migration_manager = AccountsMigrationManager(
            client.accounts, client, "accounts"
        )

        # Get base resource IDs
        sample_accounts = list(client.accounts.list(page_size=100))
        if not sample_accounts:
            print("❌ No accounts found for testing")
            return

        base_resource_ids = [
            acc.get("Account ID") for acc in sample_accounts if acc.get("Account ID")
        ]

        if len(base_resource_ids) < 20:
            print(
                f"⚠️  Warning: Only {len(base_resource_ids)} resources available. Scalability testing limited."
            )

        # Test different scales
        test_sizes = (
            [5, 10, 20, 50]
            if len(base_resource_ids) >= 50
            else [5, 10, len(base_resource_ids)]
        )
        results = {}

        print(f"🧪 Testing scalability with sizes: {test_sizes}")

        for size in test_sizes:
            if size > len(base_resource_ids):
                continue

            print(f"\n📊 Testing with {size} resources...")

            resource_ids = base_resource_ids[:size]
            migration_plan = create_test_migration_plan(
                resource_ids, args.mapping_count
            )

            # Time the recommended strategy
            recommendations = migration_manager.get_performance_recommendations(
                migration_plan
            )
            strategy = recommendations["recommended_strategy"]

            start_time = time.time()
            result = migration_manager.execute_bulk_migration_plan(
                migration_plan, strategy=strategy
            )
            end_time = time.time()

            execution_time = end_time - start_time
            resources_per_sec = size / execution_time if execution_time > 0 else 0

            results[size] = {
                "time": execution_time,
                "resources_per_sec": resources_per_sec,
                "api_calls": result.detailed_results.get("api_calls", 0),
                "strategy": strategy,
            }

            print(f"   Time: {execution_time:.2f}s")
            print(f"   Speed: {resources_per_sec:.2f} resources/sec")
            print(f"   API calls: {result.detailed_results.get('api_calls', 0)}")

        # Analyze scalability
        print(f"\n📈 Scalability Analysis:")
        print(f"{'Size':<8} {'Time':<8} {'Speed':<12} {'Strategy':<12}")
        print(f"{'-'*40}")

        for size, data in results.items():
            print(
                f"{size:<8} {data['time']:<8.2f} {data['resources_per_sec']:<12.2f} {data['strategy']:<12}"
            )

        # Calculate scalability factor
        if len(results) >= 2:
            sizes = sorted(results.keys())
            small_size, large_size = sizes[0], sizes[-1]
            small_speed = results[small_size]["resources_per_sec"]
            large_speed = results[large_size]["resources_per_sec"]

            if small_speed > 0:
                scalability_factor = large_speed / small_speed
                print(f"\n🔍 Scalability Factor: {scalability_factor:.2f}")

                if scalability_factor > 0.8:
                    print(
                        f"   ✅ Good scalability - performance maintained at larger sizes"
                    )
                elif scalability_factor > 0.5:
                    print(f"   ⚠️  Moderate scalability - some performance degradation")
                else:
                    print(
                        f"   ❌ Poor scalability - significant performance loss at scale"
                    )

    except Exception as e:
        print(f"❌ Scalability test failed: {e}")
        logger.exception("Scalability test error")


def compare_configurations(args):
    """Compare performance across different configuration options."""
    print(f"⚖️  Configuration Comparison")
    print(f"{'='*35}")

    try:
        # Initialize client and migration manager
        client = NeonClient()
        migration_manager = AccountsMigrationManager(
            client.accounts, client, "accounts"
        )

        # Parse resource IDs
        resource_ids = [int(id.strip()) for id in args.resource_ids.split(",")]

        print(f"🔧 Testing different configurations with {len(resource_ids)} resources")

        base_plan = create_test_migration_plan(resource_ids, args.mapping_count)

        # Test different configurations
        configurations = [
            {"batch_size": 25, "max_workers": 1, "name": "Sequential Small Batches"},
            {"batch_size": 50, "max_workers": 3, "name": "Parallel Medium Batches"},
            {"batch_size": 100, "max_workers": 5, "name": "Parallel Large Batches"},
            {"batch_size": 10, "max_workers": 10, "name": "High Concurrency"},
        ]

        results = []

        for config in configurations:
            print(f"\n🧪 Testing: {config['name']}")
            print(
                f"   Batch size: {config['batch_size']}, Workers: {config['max_workers']}"
            )

            # Create plan with this configuration
            test_plan = MigrationPlan(
                mappings=base_plan.mappings,
                resource_ids=base_plan.resource_ids,
                cleanup_only=base_plan.cleanup_only,
                smart_migration=base_plan.smart_migration,
                batch_size=config["batch_size"],
                max_workers=config["max_workers"],
                dry_run=True,
            )

            start_time = time.time()
            result = migration_manager.execute_bulk_migration_plan(
                test_plan, strategy="auto"
            )
            end_time = time.time()

            execution_time = end_time - start_time
            resources_per_sec = (
                len(resource_ids) / execution_time if execution_time > 0 else 0
            )

            config_result = {
                "name": config["name"],
                "batch_size": config["batch_size"],
                "max_workers": config["max_workers"],
                "time": execution_time,
                "resources_per_sec": resources_per_sec,
                "api_calls": result.detailed_results.get("api_calls", 0),
                "strategy": result.detailed_results.get("strategy", "unknown"),
            }

            results.append(config_result)

            print(f"   Time: {execution_time:.2f}s")
            print(f"   Speed: {resources_per_sec:.2f} resources/sec")
            print(f"   Strategy used: {config_result['strategy']}")

        # Display comparison
        print(f"\n📊 Configuration Comparison:")
        print(
            f"{'Configuration':<25} {'Batch':<7} {'Workers':<8} {'Time':<8} {'Speed':<12} {'Strategy':<12}"
        )
        print(f"{'-'*80}")

        # Sort by performance
        results.sort(key=lambda x: x["resources_per_sec"], reverse=True)

        for result in results:
            print(
                f"{result['name']:<25} {result['batch_size']:<7} {result['max_workers']:<8} "
                f"{result['time']:<8.2f} {result['resources_per_sec']:<12.2f} {result['strategy']:<12}"
            )

        # Best configuration
        best_config = results[0]
        print(f"\n🏆 Best Configuration: {best_config['name']}")
        print(f"   Batch size: {best_config['batch_size']}")
        print(f"   Max workers: {best_config['max_workers']}")
        print(f"   Performance: {best_config['resources_per_sec']:.2f} resources/sec")

    except Exception as e:
        print(f"❌ Configuration comparison failed: {e}")
        logger.exception("Configuration comparison error")


def main():
    """Main command-line interface."""
    parser = argparse.ArgumentParser(
        description="Migration Performance Tester and Benchmarking Tool"
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Benchmark command
    benchmark_parser = subparsers.add_parser(
        "benchmark", help="Benchmark migration strategies"
    )
    benchmark_parser.add_argument(
        "--sample-size",
        "-s",
        type=int,
        default=10,
        help="Number of resources to test with (default: 10)",
    )
    benchmark_parser.add_argument(
        "--mapping-count",
        "-m",
        type=int,
        default=3,
        help="Number of field mappings to test (default: 3)",
    )
    benchmark_parser.add_argument(
        "--resource-ids",
        "-r",
        help="Comma-separated list of specific resource IDs to test",
    )

    # Analyze command
    analyze_parser = subparsers.add_parser(
        "analyze", help="Analyze migration performance"
    )
    analyze_parser.add_argument(
        "--resource-ids",
        "-r",
        required=True,
        help="Comma-separated list of resource IDs to analyze",
    )
    analyze_parser.add_argument(
        "--mapping-count",
        "-m",
        type=int,
        default=3,
        help="Number of field mappings (default: 3)",
    )

    # Scalability command
    scalability_parser = subparsers.add_parser(
        "scalability", help="Test performance scalability"
    )
    scalability_parser.add_argument(
        "--mapping-count",
        "-m",
        type=int,
        default=3,
        help="Number of field mappings (default: 3)",
    )

    # Compare command
    compare_parser = subparsers.add_parser(
        "compare", help="Compare configuration performance"
    )
    compare_parser.add_argument(
        "--resource-ids",
        "-r",
        required=True,
        help="Comma-separated list of resource IDs to test",
    )
    compare_parser.add_argument(
        "--mapping-count",
        "-m",
        type=int,
        default=3,
        help="Number of field mappings (default: 3)",
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    try:
        if args.command == "benchmark":
            benchmark_strategies(args)
        elif args.command == "analyze":
            analyze_performance(args)
        elif args.command == "scalability":
            test_scalability(args)
        elif args.command == "compare":
            compare_configurations(args)
    except KeyboardInterrupt:
        print(f"\n⏹️  Operation cancelled by user")
    except Exception as e:
        print(f"❌ Error: {e}")
        logger.exception("Unexpected error occurred")


if __name__ == "__main__":
    main()
