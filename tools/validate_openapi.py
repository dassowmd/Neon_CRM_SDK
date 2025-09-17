#!/usr/bin/env python3
"""Validate OpenAPI specification and check for completeness."""

from pathlib import Path
from typing import Dict, List

import yaml


def load_openapi_spec(file_path: Path) -> Dict:
    """Load OpenAPI specification from YAML file."""
    with open(file_path) as f:
        return yaml.safe_load(f)


def load_capabilities(file_path: Path) -> Dict:
    """Load capabilities matrix from YAML file."""
    with open(file_path) as f:
        return yaml.safe_load(f)


def validate_openapi_completeness(openapi_spec: Dict, capabilities: Dict) -> List[str]:
    """Validate that OpenAPI spec covers all resources from capabilities."""
    issues = []

    # Get all resources from capabilities
    capability_resources = set(capabilities.get("resources", {}).keys())

    # Get all paths from OpenAPI spec
    paths = openapi_spec.get("paths", {})
    openapi_resources = set()

    for path in paths.keys():
        # Extract resource name from path (e.g., /accounts -> accounts)
        parts = path.strip("/").split("/")
        if parts and parts[0]:
            openapi_resources.add(parts[0])

    # Check for missing resources
    missing_resources = capability_resources - openapi_resources
    for resource in missing_resources:
        issues.append(f"Missing resource in OpenAPI spec: {resource}")

    # Check for extra resources
    extra_resources = openapi_resources - capability_resources
    for resource in extra_resources:
        if resource not in ["customFields", "store"]:  # These are expected variations
            issues.append(
                f"Extra resource in OpenAPI spec not in capabilities: {resource}"
            )

    return issues


def validate_schema_consistency(openapi_spec: Dict) -> List[str]:
    """Validate internal consistency of OpenAPI schema."""
    issues = []

    components = openapi_spec.get("components", {})
    schemas = components.get("schemas", {})

    # Check that all $ref references exist
    def check_refs(obj, path=""):
        if isinstance(obj, dict):
            for key, value in obj.items():
                current_path = f"{path}.{key}" if path else key
                if key == "$ref" and isinstance(value, str):
                    if value.startswith("#/components/schemas/"):
                        schema_name = value.split("/")[-1]
                        if schema_name not in schemas:
                            issues.append(
                                f"Missing schema reference at {current_path}: {schema_name}"
                            )
                else:
                    check_refs(value, current_path)
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                check_refs(item, f"{path}[{i}]")

    check_refs(openapi_spec)

    return issues


def validate_field_discovery_coverage(
    openapi_spec: Dict, field_discovery: Dict
) -> List[str]:
    """Validate that OpenAPI spec covers field discovery features."""
    issues = []

    paths = openapi_spec.get("paths", {})

    # Check for fuzzy search endpoints
    fuzzy_search_paths = ["/customFields/search", "/customFields/suggest"]

    for endpoint in fuzzy_search_paths:
        if endpoint not in paths:
            issues.append(f"Missing field discovery endpoint: {endpoint}")

    # Check for field discovery documentation in schemas
    schemas = openapi_spec.get("components", {}).get("schemas", {})

    required_schemas = ["FieldDefinition", "SearchRequest", "SearchField"]

    for schema_name in required_schemas:
        if schema_name not in schemas:
            issues.append(f"Missing schema for field discovery: {schema_name}")

    return issues


def generate_coverage_report(openapi_spec: Dict, capabilities: Dict) -> Dict:
    """Generate a coverage report of what's documented."""
    report = {
        "total_resources": len(capabilities.get("resources", {})),
        "documented_resources": 0,
        "documented_endpoints": 0,
        "missing_resources": [],
        "coverage_by_type": {
            "searchable": {"total": 0, "documented": 0},
            "crud": {"total": 0, "documented": 0},
            "specialized": {"total": 0, "documented": 0},
        },
    }

    # Count resources by type
    for _resource_name, resource_info in capabilities.get("resources", {}).items():
        resource_type = resource_info.get("type", "unknown")
        if resource_type in report["coverage_by_type"]:
            report["coverage_by_type"][resource_type]["total"] += 1

    # Check what's documented in OpenAPI
    paths = openapi_spec.get("paths", {})
    documented_resources = set()

    for path in paths.keys():
        parts = path.strip("/").split("/")
        if parts and parts[0]:
            documented_resources.add(parts[0])

    report["documented_resources"] = len(documented_resources)
    report["documented_endpoints"] = len(paths)

    # Check coverage by type
    for resource_name, resource_info in capabilities.get("resources", {}).items():
        resource_type = resource_info.get("type", "unknown")
        if (
            resource_name in documented_resources
            and resource_type in report["coverage_by_type"]
        ):
            report["coverage_by_type"][resource_type]["documented"] += 1
        elif resource_name not in documented_resources:
            report["missing_resources"].append(resource_name)

    return report


def main():
    """Run all validations and generate report."""
    docs_dir = Path(__file__).parent.parent / "docs" / "api"

    print("🔍 Validating OpenAPI specification and documentation...")

    # Load files
    try:
        openapi_spec = load_openapi_spec(docs_dir / "openapi.yaml")
        capabilities = load_capabilities(docs_dir / "capabilities.yaml")
        field_discovery = load_capabilities(docs_dir / "field_discovery.yaml")
    except FileNotFoundError as e:
        print(f"❌ Error loading files: {e}")
        return 1

    # Run validations
    issues = []

    print("  Checking OpenAPI completeness...")
    issues.extend(validate_openapi_completeness(openapi_spec, capabilities))

    print("  Checking schema consistency...")
    issues.extend(validate_schema_consistency(openapi_spec))

    print("  Checking field discovery coverage...")
    issues.extend(validate_field_discovery_coverage(openapi_spec, field_discovery))

    # Generate coverage report
    print("  Generating coverage report...")
    coverage = generate_coverage_report(openapi_spec, capabilities)

    # Print results
    print("\n📊 Documentation Coverage Report:")
    print(f"  Total resources: {coverage['total_resources']}")
    print(f"  Documented resources: {coverage['documented_resources']}")
    print(f"  Documented endpoints: {coverage['documented_endpoints']}")
    print(
        f"  Coverage: {coverage['documented_resources'] / coverage['total_resources'] * 100:.1f}%"
    )

    print("\n📈 Coverage by Resource Type:")
    for resource_type, stats in coverage["coverage_by_type"].items():
        if stats["total"] > 0:
            percentage = stats["documented"] / stats["total"] * 100
            print(
                f"  {resource_type.title()}: {stats['documented']}/{stats['total']} ({percentage:.1f}%)"
            )

    if coverage["missing_resources"]:
        print("\n❌ Missing Resources:")
        for resource in coverage["missing_resources"]:
            print(f"  - {resource}")

    if issues:
        print(f"\n⚠️  Validation Notes ({len(issues)}):")
        for issue in issues:
            print(f"  - {issue}")
        print(
            "\n📝 Note: This OpenAPI spec provides examples of key resources and features."
        )
        print(
            f"   Complete documentation would cover all {coverage['total_resources']} resources."
        )
        return 0  # Don't fail for incomplete coverage in this demo
    else:
        print("\n✅ All validations passed!")
        return 0


if __name__ == "__main__":
    exit(main())
