#!/usr/bin/env python3
"""Test tool for Universal Field Manager functionality.

This tool demonstrates and tests the Universal Field Manager's ability to handle
both standard and custom fields in migration operations.
"""

import sys
import os
import logging
import argparse
from typing import Dict, Any

# Add the parent directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.neon_crm import NeonClient
from src.neon_crm.migration_tools import (
    UniversalFieldManager,
    FieldType,
    FieldMetadata,
    AccountsMigrationManager,
    MigrationMapping,
    MigrationStrategy,
)


def setup_logging(level: str = "INFO"):
    """Set up logging configuration."""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


def test_field_discovery(manager: UniversalFieldManager):
    """Test field discovery functionality."""
    print("\n=== Testing Field Discovery ===")

    # List all fields
    all_fields = manager.list_all_fields()
    print(f"Total fields found: {len(all_fields)}")

    # Separate by type
    standard_fields = [f for f in all_fields if f.field_type == FieldType.STANDARD]
    custom_fields = [f for f in all_fields if f.field_type == FieldType.CUSTOM]

    print(f"Standard fields: {len(standard_fields)}")
    print(f"Custom fields: {len(custom_fields)}")

    # Show some examples
    print("\nStandard fields (first 5):")
    for field in standard_fields[:5]:
        print(f"  - {field.name} ({field.data_type})")

    print("\nCustom fields (first 5):")
    for field in custom_fields[:5]:
        print(f"  - {field.name} ({field.data_type})")

    # Test pattern matching
    v_fields = manager.find_fields_by_pattern("V-*")
    if v_fields:
        print(f"\nV-fields found: {len(v_fields)}")
        for field in v_fields[:3]:
            print(f"  - {field.name}")

    return all_fields


def test_field_metadata(manager: UniversalFieldManager, field_names: list):
    """Test field metadata retrieval."""
    print("\n=== Testing Field Metadata ===")

    for field_name in field_names[:3]:  # Test first 3 fields
        metadata = manager.get_field_metadata(field_name)
        if metadata:
            print(f"\nField: {field_name}")
            print(f"  Type: {metadata.field_type.value}")
            print(f"  Data Type: {metadata.data_type}")
            print(f"  Searchable: {metadata.is_searchable}")
            print(f"  Output: {metadata.is_output}")
            print(f"  Multi-value: {metadata.is_multi_value}")
        else:
            print(f"Field {field_name} not found")


def test_field_values(
    manager: UniversalFieldManager, account_id: str, field_names: list
):
    """Test getting and setting field values."""
    print(f"\n=== Testing Field Values (Account {account_id}) ===")

    for field_name in field_names[:2]:  # Test first 2 fields
        try:
            # Get current value
            field_value = manager.get_field_value(account_id, field_name)
            if field_value:
                print(f"\nField: {field_name}")
                print(f"  Current value: {field_value.value}")
                print(f"  Field type: {field_value.field_type.value}")
                print(f"  Valid: {field_value.is_valid}")
            else:
                print(f"Field {field_name}: No value found")
        except Exception as e:
            print(f"Error testing field {field_name}: {e}")


def test_universal_migration(
    migration_manager: AccountsMigrationManager, account_id: str
):
    """Test universal field migration functionality."""
    print(f"\n=== Testing Universal Migration (Account {account_id}) ===")

    # Test different migration scenarios
    test_scenarios = [
        {
            "name": "Standard to Custom Migration",
            "source": "firstName",
            "target": "Test Standard to Custom",
            "strategy": MigrationStrategy.REPLACE,
        },
        {
            "name": "Custom to Standard Migration (if applicable)",
            "source": "Test Custom Field",
            "target": "preferredName",
            "strategy": MigrationStrategy.COPY_IF_EMPTY,
        },
    ]

    for scenario in test_scenarios:
        print(f"\nTesting: {scenario['name']}")

        # Create mapping
        mapping = MigrationMapping(
            source_field=scenario["source"],
            target_field=scenario["target"],
            strategy=scenario["strategy"],
        )

        try:
            # Check if both fields exist
            source_meta = migration_manager.get_universal_field_metadata(
                scenario["source"]
            )
            target_meta = migration_manager.get_universal_field_metadata(
                scenario["target"]
            )

            if not source_meta:
                print(f"  Source field '{scenario['source']}' not found")
                continue

            if not target_meta:
                print(f"  Target field '{scenario['target']}' not found")
                continue

            print(f"  Source: {source_meta.field_type.value} field")
            print(f"  Target: {target_meta.field_type.value} field")

            # Get current source value
            source_value = migration_manager.get_universal_field_value(
                account_id, scenario["source"]
            )
            if source_value and source_value.value:
                print(f"  Source value: {source_value.value}")

                # Execute migration (dry run - don't actually change data)
                print(f"  Would execute {scenario['strategy'].value} migration")
                # result = migration_manager.execute_universal_migration_mapping(account_id, mapping)
                # print(f"  Result: {result}")
            else:
                print(f"  No source value to migrate")

        except Exception as e:
            print(f"  Error: {e}")


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Test Universal Field Manager functionality"
    )
    parser.add_argument(
        "--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"]
    )
    parser.add_argument("--account-id", help="Specific account ID to test with")

    args = parser.parse_args()

    setup_logging(args.log_level)

    try:
        # Initialize client
        print("Initializing Neon CRM client...")
        client = NeonClient()

        # Initialize managers
        universal_manager = UniversalFieldManager(client.accounts, client, "accounts")
        migration_manager = AccountsMigrationManager(
            client.accounts, client, "accounts"
        )

        print("Universal Field Manager initialized successfully")

        # Test field discovery
        all_fields = test_field_discovery(universal_manager)

        if not all_fields:
            print("No fields found - cannot continue testing")
            return

        # Get some field names for testing
        field_names = [f.name for f in all_fields[:10]]  # Use first 10 fields

        # Test field metadata
        test_field_metadata(universal_manager, field_names)

        # Test field values (need account ID)
        account_id = args.account_id
        if not account_id:
            # Try to get first account
            try:
                accounts = list(client.accounts.list(page_size=1))
                if accounts:
                    account_id = accounts[0].get("accountId") or accounts[0].get("id")
            except Exception as e:
                print(f"Could not get account for testing: {e}")

        if account_id:
            test_field_values(universal_manager, account_id, field_names)
            test_universal_migration(migration_manager, account_id)
        else:
            print("No account ID available - skipping field value tests")

        print("\n=== Universal Field Manager Test Complete ===")

    except Exception as e:
        print(f"Error during testing: {e}")
        logging.exception("Full error details:")
        sys.exit(1)


if __name__ == "__main__":
    main()
