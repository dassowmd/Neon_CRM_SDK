#!/usr/bin/env python3
"""Simple field discovery to get exact field names."""

import os
import sys

sys.path.append("../src")
from neon_crm import NeonClient


def check_key_fields():
    """Find the key fields we need for donor analysis."""

    client = NeonClient(
        org_id=os.getenv("NEON_ORG_ID"),
        api_key=os.getenv("NEON_API_KEY"),
        environment="production",
    )

    print("🔍 FINDING KEY FIELDS FOR DONOR ANALYSIS")
    print("=" * 50)

    # Check account fields
    print("\n📊 ACCOUNT FIELDS - Looking for donor-related fields...")
    try:
        output_fields = client.accounts.get_output_fields()
        standard_fields = output_fields.get("standardFields", [])

        # Look for key patterns
        key_patterns = {
            "phone": ["phone", "Phone"],
            "postal/zip": ["zip", "postal", "Zip", "Postal"],
            "donation_amount": ["donation amount", "giving", "Donation", "Lifetime"],
            "donation_count": ["donation count", "Number of Donations", "Count"],
            "create_date": ["create", "Create", "created", "Created"],
            "activity_date": ["activity", "Activity", "modified", "Modified"],
        }

        found_fields = {}

        for category, patterns in key_patterns.items():
            print(f"\n  🔍 Looking for {category} fields:")
            found = []

            for field in standard_fields:
                if any(pattern in field for pattern in patterns):
                    found.append(field)

            if found:
                print(f"     Found {len(found)} matches:")
                for f in found[:5]:  # Show top 5
                    print(f"       • {f}")
                if len(found) > 5:
                    print(f"       ... and {len(found) - 5} more")

                found_fields[category] = found
            else:
                print(f"     ❌ No matches found")

        # Show recommended fields
        print(f"\n✅ RECOMMENDED ACCOUNT FIELDS:")
        recommended = [
            "Account ID",
            "Account Type",
            "First Name",
            "Last Name",
            "Company Name",
            "Email 1",
            "City",
            "State/Province",
        ]

        # Add best matches for other fields
        if "phone" in found_fields:
            recommended.append(found_fields["phone"][0])
        if "postal/zip" in found_fields:
            recommended.append(found_fields["postal/zip"][0])
        if "donation_amount" in found_fields:
            recommended.append(found_fields["donation_amount"][0])
        if "donation_count" in found_fields:
            recommended.append(found_fields["donation_count"][0])

        for field in recommended:
            print(f"  • {field}")

    except Exception as e:
        print(f"❌ Error checking account fields: {e}")

    # Check donation fields
    print(f"\n💰 DONATION FIELDS - Core fields...")
    try:
        output_fields = client.donations.get_output_fields()
        standard_fields = output_fields.get("standardFields", [])

        # Look for essential donation fields
        essential_donation = []
        for field in standard_fields:
            if any(
                key in field for key in ["Donation ID", "Account ID", "Amount", "Date"]
            ):
                essential_donation.append(field)

        print(f"  Essential donation fields found:")
        for field in essential_donation[:10]:
            print(f"    • {field}")

    except Exception as e:
        print(f"❌ Error checking donation fields: {e}")


if __name__ == "__main__":
    check_key_fields()
