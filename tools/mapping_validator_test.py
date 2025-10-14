#!/usr/bin/env python3
"""Test tool for Mapping Dictionary Validator functionality.

This tool demonstrates and tests the comprehensive mapping validation system.
"""

import sys
import os
import logging
import argparse
import json
from typing import Dict, Any, List

# Add the parent directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.neon_crm import NeonClient
from src.neon_crm.migration_tools import (
    AccountsMigrationManager,
    MigrationStrategy,
    ValidationSeverity,
)


def setup_logging(level: str = "INFO"):
    """Set up logging configuration."""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


def test_mapping_validation(migration_manager: AccountsMigrationManager):
    """Test mapping validation functionality."""
    print("\n=== Testing Mapping Validation ===")

    # Test mapping dictionary with various scenarios
    test_mappings = {
        # Valid mappings
        "firstName": "preferredName",
        "lastName": "companyName",
        # Invalid mappings (non-existent fields)
        "NonExistentSource": "lastName",
        "email2": "NonExistentTarget",  # Changed to avoid duplicate firstName
        # Self-mapping
        "email1": "email1",
        # Type compatibility issues
        "accountId": "firstName",  # number to text
        "dateCreated": "accountType",  # date to enum
    }

    print(f"Testing validation with {len(test_mappings)} mappings:")
    for source, target in test_mappings.items():
        print(f"  {source} -> {target}")

    # Validate the mapping dictionary
    validation_result = migration_manager.validate_mapping_dictionary(
        test_mappings, default_strategy=MigrationStrategy.REPLACE
    )

    print(f"\nValidation Results:")
    print(f"  Overall valid: {validation_result.is_valid}")
    print(f"  Total issues: {len(validation_result.issues)}")
    print(f"  Errors: {validation_result.get_error_count()}")
    print(f"  Warnings: {validation_result.get_warning_count()}")

    # Show detailed issues
    print(f"\nDetailed Issues:")
    for issue in validation_result.issues:
        severity_symbol = (
            "❌"
            if issue.severity == ValidationSeverity.ERROR
            else "⚠️"
            if issue.severity == ValidationSeverity.WARNING
            else "ℹ️"
        )
        print(f"  {severity_symbol} {issue.severity.value.upper()}: {issue.message}")
        if issue.suggestion:
            print(f"    💡 Suggestion: {issue.suggestion}")

    # Show suggestions
    if validation_result.suggestions:
        print(f"\nGeneral Suggestions:")
        for suggestion in validation_result.suggestions:
            print(f"  • {suggestion}")

    return validation_result


def test_field_suggestions(migration_manager: AccountsMigrationManager):
    """Test field suggestion functionality."""
    print("\n=== Testing Field Suggestions ===")

    # Test with V-fields pattern - using standardized field names
    source_fields = [
        "V-Canvassing",
        "V-Data Entry",
        "V-Phone Banking",
        "V-Event Planning",
    ]

    print(f"Finding suggestions for source fields: {source_fields}")

    # Get suggestions for V-fields targeting other V-fields
    v_suggestions = migration_manager.suggest_field_mappings(
        source_fields, target_pattern="V-*"
    )

    print(f"\nV-field to V-field suggestions:")
    for source, targets in v_suggestions.items():
        if targets:
            print(f"  {source}:")
            for target in targets:
                print(f"    -> {target}")
        else:
            print(f"  {source}: No suggestions found")

    # Get suggestions for general fields
    general_suggestions = migration_manager.suggest_field_mappings(
        ["firstName", "email", "phone"], target_pattern=None
    )

    print(f"\nGeneral field suggestions:")
    for source, targets in general_suggestions.items():
        if targets:
            print(f"  {source}:")
            for target in targets[:3]:  # Show top 3
                print(f"    -> {target}")


def test_validated_plan_creation(migration_manager: AccountsMigrationManager):
    """Test creating validated migration plans."""
    print("\n=== Testing Validated Plan Creation ===")

    # Test with a mix of valid and invalid mappings
    test_mapping = {
        "firstName": "preferredName",  # Valid
        "lastName": "companyName",  # Valid but warning (type mismatch)
        "InvalidField": "email1",  # Invalid source field
    }

    print(f"Creating migration plan with mappings:")
    for source, target in test_mapping.items():
        print(f"  {source} -> {target}")

    # Create plan with validation
    migration_plan, validation_result = (
        migration_manager.create_validated_migration_plan(
            test_mapping,
            strategy=MigrationStrategy.REPLACE,
            validate_mappings=True,
            auto_fix_issues=False,
        )
    )

    print(f"\nPlan Creation Results:")
    print(f"  Plan created: {len(migration_plan.mappings)} mappings")
    print(f"  Validation passed: {validation_result.is_valid}")
    print(f"  Issues found: {len(validation_result.issues)}")

    if validation_result.issues:
        print(f"\nValidation Issues:")
        for issue in validation_result.issues:
            print(f"  {issue.severity.value}: {issue.message}")


def test_strategy_validation(migration_manager: AccountsMigrationManager):
    """Test strategy-specific validation."""
    print("\n=== Testing Strategy Validation ===")

    # Test different strategies with appropriate and inappropriate field types
    strategy_tests = [
        {
            "name": "ADD_OPTION on single-value field",
            "mapping": {"firstName": "lastName"},
            "strategy": MigrationStrategy.ADD_OPTION,
            "expected": "warning",
        },
        {
            "name": "TRANSFORM without function",
            "mapping": {"firstName": "lastName"},
            "strategy": MigrationStrategy.TRANSFORM,
            "expected": "error",
        },
        {
            "name": "REPLACE strategy",
            "mapping": {"firstName": "preferredName"},
            "strategy": MigrationStrategy.REPLACE,
            "expected": "valid",
        },
    ]

    for test in strategy_tests:
        print(f"\nTesting: {test['name']}")

        validation_result = migration_manager.validate_mapping_dictionary(
            test["mapping"], default_strategy=test["strategy"]
        )

        print(f"  Expected: {test['expected']}")
        print(f"  Result: {'valid' if validation_result.is_valid else 'invalid'}")

        if validation_result.issues:
            for issue in validation_result.issues:
                print(f"    {issue.severity.value}: {issue.message}")


def test_type_compatibility(migration_manager: AccountsMigrationManager):
    """Test type compatibility validation."""
    print("\n=== Testing Type Compatibility ===")

    # Test various type combinations
    type_tests = {
        # Compatible types
        "firstName": "preferredName",  # text -> text
        "phone1": "phone2",  # phone -> phone
        # Potentially incompatible types
        "dateCreated": "firstName",  # date -> text
        "accountId": "email1",  # number -> email
    }

    print(f"Testing type compatibility:")

    validation_result = migration_manager.validate_mapping_dictionary(type_tests)

    type_issues = [
        issue
        for issue in validation_result.issues
        if issue.issue_type == "type_incompatibility"
    ]

    if type_issues:
        print(f"\nType compatibility issues found:")
        for issue in type_issues:
            print(f"  {issue.message}")
            if issue.suggestion:
                print(f"    Suggestion: {issue.suggestion}")
    else:
        print(f"  No type compatibility issues found")


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Test Mapping Dictionary Validator")
    parser.add_argument(
        "--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"]
    )
    parser.add_argument(
        "--test",
        choices=["all", "validation", "suggestions", "plans", "strategies", "types"],
        default="all",
        help="Which test to run",
    )

    args = parser.parse_args()

    setup_logging(args.log_level)

    try:
        # Initialize client and migration manager
        print("Initializing Neon CRM client...")
        client = NeonClient()
        migration_manager = AccountsMigrationManager(
            client.accounts, client, "accounts"
        )

        print("Mapping Dictionary Validator initialized successfully")

        # Run selected tests
        if args.test in ["all", "validation"]:
            test_mapping_validation(migration_manager)

        if args.test in ["all", "suggestions"]:
            test_field_suggestions(migration_manager)

        if args.test in ["all", "plans"]:
            test_validated_plan_creation(migration_manager)

        if args.test in ["all", "strategies"]:
            test_strategy_validation(migration_manager)

        if args.test in ["all", "types"]:
            test_type_compatibility(migration_manager)

        print("\n=== Mapping Validation Tests Complete ===")

    except Exception as e:
        print(f"Error during testing: {e}")
        logging.exception("Full error details:")
        sys.exit(1)


if __name__ == "__main__":
    main()
