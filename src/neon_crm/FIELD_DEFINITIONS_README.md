# Field Definitions Management

This document explains how the Neon CRM SDK manages field definitions for validation.

## Overview

The SDK uses a hybrid approach for field validation:

1. **JSON-based standard fields**: Predefined standard fields stored in `field_definitions.json`
2. **Dynamic API queries**: Live field discovery from your Neon CRM organization
3. **Custom field support**: Automatic handling of organization-specific custom fields

## Field Definitions JSON Structure

The `field_definitions.json` file contains three main sections:

```json
{
  "valid_search_fields": {
    "accounts": ["Account ID", "First Name", ...],
    "donations": ["Donation ID", "Amount", ...],
    ...
  },
  "valid_output_fields": {
    "accounts": ["Account ID", "First Name", "Address Line 1", ...],
    "donations": ["Donation ID", "Amount", "Note", ...],
    ...
  },
  "field_types": {
    "Account ID": "number",
    "First Name": "string",
    "Date Created": "date",
    "Published": "boolean",
    ...
  }
}
```

## How Validation Works

1. **Static Validation**: The SDK first checks fields against the JSON definitions
2. **Dynamic Validation**: If a client connection is available, it queries the API for additional fields
3. **Custom Fields**: Numeric field IDs and fields matching custom field patterns are automatically allowed
4. **Fallback**: If API queries fail, the SDK falls back to JSON definitions only

## Updating Field Definitions

### When to Update

Update the JSON file when:
- New standard fields are added to Neon CRM
- Field names change in the Neon API
- Field types are modified
- New resources are added to the SDK

### How to Update

1. **Automatic Update** (Recommended):
   ```python
   # Create a script to fetch current fields from API
   from neon_crm import NeonClient
   import json

   client = NeonClient(org_id="your_org", api_key="your_key")

   # Get fields for each resource
   resources = ["accounts", "donations", "events", "activities", "memberships"]

   search_fields = {}
   output_fields = {}

   for resource_name in resources:
       resource = getattr(client, resource_name)

       # Get search fields (standard only)
       search_response = resource.get_search_fields()
       search_fields[resource_name] = [
           field["fieldName"]
           for field in search_response.get("standardFields", [])
       ]

       # Get output fields (standard only)
       output_response = resource.get_output_fields()
       output_fields[resource_name] = output_response.get("standardFields", [])

   # Update the JSON file
   field_definitions = {
       "valid_search_fields": search_fields,
       "valid_output_fields": output_fields,
       "field_types": existing_field_types  # Preserve existing types
   }

   with open("field_definitions.json", "w") as f:
       json.dump(field_definitions, f, indent=2)
   ```

2. **Manual Update**:
   Edit `field_definitions.json` directly to add/remove/modify field definitions.

### Field Type Guidelines

Use these types for the `field_types` section:

- `"string"`: Text fields (names, addresses, descriptions)
- `"number"`: Numeric fields (IDs, amounts, counts)
- `"date"`: Date fields (use YYYY-MM-DD format)
- `"boolean"`: True/false fields (flags, status indicators)
- `"enum"`: Predefined value fields (types, categories, statuses)

## Custom Field Handling

The SDK automatically detects custom fields using these patterns:

- Numeric field names (e.g., `"123"`, `456`)
- Fields starting with common prefixes (`"V-"`, `"C-"`, `"Custom"`)
- Fields containing dashes (`" - "`)
- Very long field names (>50 characters)

Custom fields are always considered valid for both search and output operations.

## Validation Benefits

This approach provides:

1. **Fast Validation**: JSON lookup is faster than API calls
2. **Offline Support**: Validation works without API connection
3. **Extensibility**: Easy to add new fields and resources
4. **Flexibility**: Supports both standard and custom fields
5. **Maintainability**: Field definitions in separate, editable file

## Troubleshooting

### Common Issues

1. **Field not found**: Check if it's in the JSON file or if it's a custom field
2. **Validation too strict**: Custom fields might need pattern updates
3. **Missing fields**: JSON file might need updating from API
4. **API errors**: Validation falls back to JSON-only mode

### Debug Tips

Enable debug logging to see validation details:

```python
import logging
logging.getLogger("neon_crm.validation").setLevel(logging.DEBUG)
```

This will show field lookup attempts and fallback behavior.
