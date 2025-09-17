"""
Custom Fields Example

This example demonstrates how to work with custom fields in the Neon CRM SDK:
- Finding custom fields by name and ID
- Searching accounts by custom field values
- Including custom field values in search results
- Best practices for custom field operations
"""

from typing import Dict, Optional

from neon_crm import NeonClient

# Initialize the client
client = NeonClient()


def list_all_custom_fields():
    """List all custom fields for accounts."""
    print("📋 Available Custom Fields for Accounts:")
    print("=" * 50)

    custom_fields = list(client.accounts.list_custom_fields())

    for field in custom_fields[:10]:  # Show first 10
        field_id = field.get("id")
        field_name = field.get("name", "Unknown")
        field_type = field.get("fieldType", "Unknown")

        print(f"  ID: {field_id:3} | {field_name} ({field_type})")

    if len(custom_fields) > 10:
        print(f"  ... and {len(custom_fields) - 10} more fields")

    print(f"\n✅ Found {len(custom_fields)} total custom fields\n")
    return custom_fields


def find_custom_field_by_name(field_name: str) -> Optional[Dict]:
    """Find a custom field by its name."""
    print(f"🔍 Looking for custom field: '{field_name}'")

    field = client.accounts.find_custom_field_by_name(field_name)

    if field:
        field_id = field.get("id")
        field_type = field.get("fieldType")
        print(f"  ✅ Found: ID {field_id}, Type: {field_type}")
        return field
    else:
        print(f"  ❌ Custom field '{field_name}' not found")
        return None


def search_by_custom_field(field_id: int, field_name: str):
    """Search for accounts with non-blank values in a custom field."""
    print(f"🔍 Searching accounts with non-blank '{field_name}' (ID: {field_id})")

    try:
        search_request = {
            "searchFields": [
                {"field": field_id, "operator": "NOT_BLANK"}  # Use integer field ID
            ],
            "outputFields": [
                "Account ID",
                "First Name",
                "Last Name",
                field_id,  # Include custom field in output (integer ID)
            ],
            "pagination": {"currentPage": 0, "pageSize": 10},  # Limit results for demo
        }

        results = list(client.accounts.search(search_request))

        print(f"  ✅ Found {len(results)} accounts with non-blank values")

        # Show sample results
        for i, account in enumerate(results[:5]):
            account_id = account.get("Account ID")
            first_name = account.get("First Name", "")
            last_name = account.get("Last Name", "")

            # Custom field values are returned with display name as key
            custom_value = account.get(field_name, "N/A")

            name = f"{first_name} {last_name}".strip()
            print(f"    Account {account_id}: {name} = '{custom_value}'")

            if i >= 4 and len(results) > 5:
                print(f"    ... and {len(results) - 5} more accounts")
                break

        return results

    except Exception as e:
        print(f"  ❌ Error searching by custom field: {e}")
        return []


def search_by_custom_field_value(field_id: int, field_name: str, search_value: str):
    """Search for accounts with specific custom field values."""
    print(f"🔍 Searching accounts where '{field_name}' contains '{search_value}'")

    try:
        search_request = {
            "searchFields": [
                {"field": field_id, "operator": "CONTAIN", "value": search_value}
            ],
            "outputFields": [
                "Account ID",
                "First Name",
                "Last Name",
                "Email 1",
                field_id,  # Include the custom field value
            ],
            "pagination": {"currentPage": 0, "pageSize": 5},
        }

        results = list(client.accounts.search(search_request))

        print(f"  ✅ Found {len(results)} accounts matching '{search_value}'")

        for account in results:
            account_id = account.get("Account ID")
            first_name = account.get("First Name", "")
            last_name = account.get("Last Name", "")
            email = account.get("Email 1", "No email")
            custom_value = account.get(field_name, "N/A")

            name = f"{first_name} {last_name}".strip()
            print(f"    Account {account_id}: {name} ({email})")
            print(f"      {field_name}: '{custom_value}'")

        return results

    except Exception as e:
        print(f"  ❌ Error searching by custom field value: {e}")
        return []


def search_multiple_custom_fields(field_mapping: Dict[str, int]):
    """Search by multiple custom fields and include all in output."""
    print("🔍 Searching by multiple custom fields")

    # Build search fields for all custom fields
    search_fields = []
    output_fields = ["Account ID", "First Name", "Last Name", "Email 1"]

    for _, field_id in field_mapping.items():
        search_fields.append({"field": field_id, "operator": "NOT_BLANK"})
        output_fields.append(field_id)  # Add to output

    try:
        search_request = {
            "searchFields": search_fields,
            "outputFields": output_fields,
            "pagination": {"currentPage": 0, "pageSize": 5},
        }

        results = list(client.accounts.search(search_request))

        print(f"  ✅ Found {len(results)} accounts with all specified custom fields")

        for account in results:
            account_id = account.get("Account ID")
            first_name = account.get("First Name", "")
            last_name = account.get("Last Name", "")

            name = f"{first_name} {last_name}".strip()
            print(f"    Account {account_id}: {name}")

            # Show all custom field values
            for field_name in field_mapping.keys():
                custom_value = account.get(field_name, "N/A")
                print(f"      {field_name}: '{custom_value}'")

        return results

    except Exception as e:
        print(f"  ❌ Error in multi-field search: {e}")
        return []


def custom_field_migration_example():
    """Example of analyzing custom fields for migration (like your V-fields)."""
    print("📊 Custom Field Migration Analysis Example")
    print("=" * 50)

    # Fields to analyze (example V-fields)
    target_fields = [
        "V-Annual Fundraising Event Committee",
        "V-Canvassing",
        "V-Coffee Klatch Interest",
        "V-Communications Team - website, newsletter, blog, messaging, graphic design",
        "V-Data Entry",
    ]

    results_summary = {}

    for field_name in target_fields:
        print(f"\n🔍 Analyzing: {field_name}")

        # Find the field
        field = client.accounts.find_custom_field_by_name(field_name)
        if not field:
            print("  ❌ Field not found")
            continue

        field_id = field["id"]
        print(f"  Field ID: {field_id}")

        try:
            # Count accounts with non-blank values
            search_request = {
                "searchFields": [{"field": field_id, "operator": "NOT_BLANK"}],
                "outputFields": ["Account ID"],
                "pagination": {"currentPage": 0, "pageSize": 1},
            }

            # Get first page to see total count
            results = list(client.accounts.search(search_request))
            count = len(results)

            print(f"  ✅ {count} accounts have non-blank values")
            results_summary[field_name] = {"field_id": field_id, "count": count}

        except Exception as e:
            print(f"  ❌ Error: {e}")
            results_summary[field_name] = {
                "field_id": field_id,
                "count": 0,
                "error": str(e),
            }

    # Print summary
    print("\n📊 MIGRATION SUMMARY")
    print("=" * 30)
    total_records = sum(data.get("count", 0) for data in results_summary.values())

    for field_name, data in results_summary.items():
        count = data.get("count", 0)
        if "error" in data:
            print(f"❌ {field_name}: ERROR")
        elif count == 0:
            print(f"⭕ {field_name}: No data")
        else:
            print(f"✅ {field_name}: {count} records")

    print(f"\n🎯 Total records across all fields: {total_records}")


def main():
    """Run all custom field examples."""
    print("🎯 Neon CRM SDK - Custom Fields Examples")
    print("=" * 60)

    try:
        # 1. List all custom fields
        custom_fields = list_all_custom_fields()

        if not custom_fields:
            print(
                "❌ No custom fields found. Make sure your organization has custom fields set up."
            )
            return

        # 2. Find a specific field (use the first one as example)
        example_field = custom_fields[0]
        field_name = example_field.get("name", "Unknown Field")
        field_id = example_field.get("id")

        print(f"📝 Using '{field_name}' (ID: {field_id}) for examples\n")

        # 3. Search by custom field
        search_by_custom_field(field_id, field_name)
        print()

        # 4. Search by custom field value (example)
        if len(custom_fields) > 0:
            search_by_custom_field_value(field_id, field_name, "volunteer")
            print()

        # 5. Multiple custom fields example
        if len(custom_fields) >= 2:
            field_mapping = {
                custom_fields[0]["name"]: custom_fields[0]["id"],
                custom_fields[1]["name"]: custom_fields[1]["id"],
            }
            search_multiple_custom_fields(field_mapping)
            print()

        # 6. Migration analysis example
        custom_field_migration_example()

    except Exception as e:
        print(f"❌ Error running examples: {e}")
        print("Make sure you have valid Neon CRM credentials configured.")


if __name__ == "__main__":
    main()
