#!/usr/bin/env python3
"""Script to identify correct field names for the donor propensity analysis."""

import os
import sys

sys.path.append("src")

from neon_crm import NeonClient


def discover_correct_fields():
    """Discover the correct field names for each resource type."""

    client = NeonClient(
        org_id=os.getenv("NEON_ORG_ID"),
        api_key=os.getenv("NEON_API_KEY"),
        environment="production",
    )

    print("🔍 DISCOVERING CORRECT FIELD NAMES")
    print("=" * 50)

    resources_to_check = {
        "accounts": client.accounts,
        "donations": client.donations,
        "events": client.events,
        "activities": client.activities,
    }

    suggested_fields = {}

    for resource_name, resource in resources_to_check.items():
        print(f"\n📊 {resource_name.upper()} - Available Fields:")
        print("-" * 40)

        try:
            # Get available output fields
            output_fields = resource.get_output_fields()

            # Standard fields
            if "standardFields" in output_fields:
                print("Standard Fields:")
                for field in output_fields["standardFields"][:15]:  # Show first 15
                    print(f"  • {field}")
                if len(output_fields["standardFields"]) > 15:
                    print(f"  ... and {len(output_fields['standardFields']) - 15} more")

                suggested_fields[resource_name] = {
                    "standard": output_fields["standardFields"]
                }

            # Custom fields
            if "customFields" in output_fields:
                print(f"\nCustom Fields ({len(output_fields['customFields'])} total):")
                for field in output_fields["customFields"][:10]:  # Show first 10
                    if isinstance(field, dict):
                        print(
                            f"  • {field.get('displayName', field.get('name', 'Unknown'))}"
                        )
                    else:
                        print(f"  • {field}")

                if resource_name not in suggested_fields:
                    suggested_fields[resource_name] = {}
                suggested_fields[resource_name]["custom"] = output_fields[
                    "customFields"
                ]

        except Exception as e:
            print(f"❌ Error getting fields for {resource_name}: {e}")

    # Now suggest replacements for problematic fields
    print(f"\n🎯 SUGGESTED FIELD REPLACEMENTS")
    print("=" * 50)

    problematic_fields = {
        "accounts": [
            "Phone 1",
            "Postal Code",
            "Account Create Date",
            "Last Activity Date",
            "Lifetime Donation Amount",
            "# of Donations",
        ],
        "donations": ["Solicitation Method"],
        "events": ["Event Category"],
        "activities": ["Activity Date", "Account ID", "Volunteer Hours"],
    }

    for resource_name, fields in problematic_fields.items():
        if resource_name in suggested_fields:
            print(f"\n{resource_name.upper()}:")
            standard_fields = suggested_fields[resource_name].get("standard", [])

            for problem_field in fields:
                print(f"\n  ❌ '{problem_field}' not found")

                # Look for similar field names
                similar_fields = []
                for field in standard_fields:
                    field_lower = field.lower()
                    problem_lower = problem_field.lower()

                    # Check for partial matches
                    if any(
                        word in field_lower for word in problem_lower.split()
                    ) or any(word in problem_lower for word in field_lower.split()):
                        similar_fields.append(field)

                if similar_fields:
                    print(f"  ✅ Similar fields found:")
                    for similar in similar_fields[:3]:  # Show top 3 matches
                        print(f"     • {similar}")
                else:
                    print(f"  ⚠️  No similar fields found")

    return suggested_fields


def create_corrected_search_requests(suggested_fields):
    """Create corrected search requests based on discovered fields."""

    print(f"\n🔧 CORRECTED SEARCH REQUESTS")
    print("=" * 50)

    # Accounts search - corrected
    if "accounts" in suggested_fields:
        standard_fields = suggested_fields["accounts"].get("standard", [])

        # Pick the most useful fields that actually exist
        account_output_fields = []

        # Essential fields to look for
        essential_mappings = {
            "Account ID": ["Account ID", "accountId", "id"],
            "Account Type": ["Account Type", "accountType", "type"],
            "First Name": ["First Name", "firstName", "first_name"],
            "Last Name": ["Last Name", "lastName", "last_name"],
            "Company Name": ["Company Name", "companyName", "company"],
            "Email": ["Email 1", "Email", "email", "emailAddress"],
            "City": ["City", "city"],
            "State": ["State/Province", "State", "state", "province"],
            "Country": ["Country", "country"],
        }

        print("\n📋 CORRECTED ACCOUNT SEARCH:")
        print("outputFields: [")

        for label, possible_names in essential_mappings.items():
            found_field = None
            for possible in possible_names:
                if possible in standard_fields:
                    found_field = possible
                    break

            if found_field:
                account_output_fields.append(found_field)
                print(f'    "{found_field}",  # {label}')
            else:
                print(f"    # ❌ No field found for {label} - tried: {possible_names}")

        print("]")

        # Show the corrected search request
        print(
            f"\n✅ Use these {len(account_output_fields)} confirmed fields in your account search"
        )

    # Donations search - corrected
    if "donations" in suggested_fields:
        donation_fields = suggested_fields["donations"].get("standard", [])
        print(f"\n📋 AVAILABLE DONATION FIELDS ({len(donation_fields)} total):")
        for field in donation_fields[:10]:
            print(f"  • {field}")
        if len(donation_fields) > 10:
            print(f"  ... and {len(donation_fields) - 10} more")


if __name__ == "__main__":
    suggested_fields = discover_correct_fields()
    create_corrected_search_requests(suggested_fields)
