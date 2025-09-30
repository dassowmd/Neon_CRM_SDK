#!/usr/bin/env python3
"""Generate JSON schemas and API documentation from SDK code."""

import inspect
import json
import sys
from pathlib import Path
from typing import Any, Dict, Union

# Add the src directory to the path so we can import the SDK
sdk_root = Path(__file__).parent.parent
sys.path.insert(0, str(sdk_root / "src"))

try:
    from neon_crm import types
    from neon_crm.client import NeonClient
    from neon_crm.resources import *  # noqa
except ImportError as e:
    print(f"Failed to import SDK modules: {e}")
    print("Make sure you're running this from the SDK root directory")
    sys.exit(1)


def extract_type_info(type_hint) -> Dict[str, Any]:
    """Extract JSON schema info from a type hint."""
    if type_hint is str:
        return {"type": "string"}
    elif type_hint is int:
        return {"type": "integer"}
    elif type_hint is float:
        return {"type": "number"}
    elif type_hint is bool:
        return {"type": "boolean"}
    elif hasattr(type_hint, "__origin__"):
        if type_hint.__origin__ is list:
            item_type = extract_type_info(type_hint.__args__[0])
            return {"type": "array", "items": item_type}
        elif type_hint.__origin__ is dict:
            return {"type": "object"}
        elif type_hint.__origin__ is Union:
            # Handle Optional types
            args = type_hint.__args__
            if len(args) == 2 and type(None) in args:
                non_none_type = next(arg for arg in args if arg is not type(None))
                schema = extract_type_info(non_none_type)
                schema["nullable"] = True
                return schema

    # Default to string for unknown types
    return {"type": "string"}


def generate_typed_dict_schema(typed_dict_class) -> Dict[str, Any]:
    """Generate JSON schema from a TypedDict class."""
    if not hasattr(typed_dict_class, "__annotations__"):
        return {"type": "object"}

    schema = {
        "type": "object",
        "title": typed_dict_class.__name__,
        "properties": {},
        "required": [],
    }

    # Get required and optional fields
    required_keys = getattr(typed_dict_class, "__required_keys__", set())
    optional_keys = getattr(typed_dict_class, "__optional_keys__", set())

    # Add all annotated fields
    for field_name, field_type in typed_dict_class.__annotations__.items():
        schema["properties"][field_name] = extract_type_info(field_type)

        # Add to required if not optional
        if field_name in required_keys or (
            not required_keys and field_name not in optional_keys
        ):
            schema["required"].append(field_name)

    # Add description if available
    if hasattr(typed_dict_class, "__doc__") and typed_dict_class.__doc__:
        schema["description"] = typed_dict_class.__doc__.strip()

    return schema


def discover_resources() -> Dict[str, Any]:
    """Discover all resources and their capabilities."""
    client = NeonClient(org_id="dummy", api_key="dummy")  # Won't make actual requests

    resources = {}

    # Iterate through all attributes on the client
    for attr_name in dir(client):
        if attr_name.startswith("_"):
            continue

        attr = getattr(client, attr_name)

        # Skip non-resource attributes
        if not hasattr(attr, "_endpoint"):
            continue

        resource_info = {
            "class_name": attr.__class__.__name__,
            "endpoint": attr._endpoint,
            "operations": [],
            "relationships": [],
            "custom_fields": False,
            "fuzzy_search": False,
            "specialized_methods": {},
        }

        # Analyze methods to determine capabilities
        for method_name in dir(attr):
            if method_name.startswith("_"):
                continue

            method = getattr(attr, method_name)
            if not callable(method):
                continue

            # Standard CRUD operations
            if method_name in ["list", "get", "create", "update", "patch", "delete"]:
                resource_info["operations"].append(method_name)

            # Search operations
            elif method_name == "search":
                resource_info["operations"].append("search")
                resource_info["fuzzy_search"] = True

            # Field operations
            elif "field" in method_name.lower():
                resource_info["custom_fields"] = True
                if "fuzzy" in method_name or "suggest" in method_name:
                    resource_info["fuzzy_search"] = True

            # Relationship methods
            elif method_name.startswith("get_") and method_name != "get":
                resource_info["relationships"].append(method_name)

            # Specialized methods
            elif method_name not in [
                "list",
                "get",
                "create",
                "update",
                "patch",
                "delete",
                "search",
            ]:
                try:
                    sig = inspect.signature(method)
                    resource_info["specialized_methods"][method_name] = {
                        "parameters": list(sig.parameters.keys())[1:],  # Skip 'self'
                        "doc": method.__doc__.strip() if method.__doc__ else None,
                    }
                except Exception:
                    pass

        # Determine resource type
        resource_type = "crud"
        if "search" in resource_info["operations"]:
            resource_type = "searchable"
        if resource_info["specialized_methods"]:
            resource_type = "specialized"

        resource_info["type"] = resource_type

        resources[attr_name] = resource_info

    return resources


def generate_enum_schemas() -> Dict[str, Any]:
    """Generate schemas for all enum types."""
    enum_schemas = {}

    # Get all enum classes from the types module
    for name in dir(types):
        obj = getattr(types, name)
        if inspect.isclass(obj) and hasattr(obj, "__members__"):
            # This is an enum
            schema = {
                "type": "string",
                "enum": list(obj.__members__.keys()),
                "description": (
                    obj.__doc__.strip() if obj.__doc__ else f"{name} enumeration"
                ),
            }
            enum_schemas[name] = schema

    return enum_schemas


def generate_typed_dict_schemas() -> Dict[str, Any]:
    """Generate schemas for all TypedDict classes."""
    typed_dict_schemas = {}

    # Get all TypedDict classes from the types module
    for name in dir(types):
        obj = getattr(types, name)
        if inspect.isclass(obj) and hasattr(obj, "__annotations__"):
            # Check if it's a TypedDict by looking for required/optional keys
            if hasattr(obj, "__required_keys__") or hasattr(obj, "__optional_keys__"):
                schema = generate_typed_dict_schema(obj)
                typed_dict_schemas[name] = schema

    return typed_dict_schemas


def generate_complete_schemas() -> Dict[str, Any]:
    """Generate complete machine-readable schemas."""
    return {
        "version": "1.0.0",
        "generated_at": "auto-generated",
        "sdk_info": {
            "name": "Neon CRM Python SDK",
            "version": "1.0.0",
            "description": "Python SDK for Neon CRM with intelligent field discovery",
        },
        "resources": discover_resources(),
        "enums": generate_enum_schemas(),
        "typed_dicts": generate_typed_dict_schemas(),
        "capabilities": {
            "fuzzy_search": True,
            "semantic_search": True,
            "custom_fields": True,
            "relationship_traversal": True,
            "intelligent_validation": True,
            "auto_suggestion": True,
            "caching": True,
        },
    }


def main():
    """Generate all schemas and save to files."""
    output_dir = Path(__file__).parent.parent / "docs" / "api"
    output_dir.mkdir(parents=True, exist_ok=True)

    print("Generating machine-readable schemas...")

    # Generate complete schemas
    schemas = generate_complete_schemas()

    # Save main schemas file
    schemas_file = output_dir / "schemas.json"
    with open(schemas_file, "w") as f:
        json.dump(schemas, f, indent=2, default=str)

    print(f"✅ Generated schemas.json with {len(schemas['resources'])} resources")

    # Generate separate files for different schema types

    # Resource metadata
    resource_metadata_file = output_dir / "resource_metadata.json"
    with open(resource_metadata_file, "w") as f:
        json.dump(
            {"version": schemas["version"], "resources": schemas["resources"]},
            f,
            indent=2,
        )

    print("✅ Generated resource_metadata.json")

    # Type definitions
    types_file = output_dir / "types.json"
    with open(types_file, "w") as f:
        json.dump(
            {"enums": schemas["enums"], "typed_dicts": schemas["typed_dicts"]},
            f,
            indent=2,
        )

    print("✅ Generated types.json")

    # Capabilities matrix (JSON version of YAML)
    capabilities_file = output_dir / "capabilities.json"
    capabilities_data = {
        "version": schemas["version"],
        "sdk_capabilities": schemas["capabilities"],
        "resources": {},
    }

    # Convert resource info to capabilities format
    for resource_name, resource_info in schemas["resources"].items():
        capabilities_data["resources"][resource_name] = {
            "type": resource_info["type"],
            "endpoint": resource_info["endpoint"],
            "operations": resource_info["operations"],
            "relationships": resource_info["relationships"],
            "custom_fields": resource_info["custom_fields"],
            "fuzzy_search": resource_info["fuzzy_search"],
            "specialized_methods": list(resource_info["specialized_methods"].keys()),
        }

    with open(capabilities_file, "w") as f:
        json.dump(capabilities_data, f, indent=2)

    print("✅ Generated capabilities.json")

    print(f"\nGenerated files in {output_dir}:")
    print("  📄 schemas.json - Complete SDK schemas")
    print("  📄 resource_metadata.json - Resource capabilities and operations")
    print("  📄 types.json - Enum and TypedDict definitions")
    print("  📄 capabilities.json - Machine-readable capabilities matrix")
    print("  📄 openapi.yaml - OpenAPI 3.0 specification")
    print("  📄 capabilities.yaml - Human-readable capabilities matrix")
    print("  📄 field_discovery.yaml - Field discovery documentation")


if __name__ == "__main__":
    main()
