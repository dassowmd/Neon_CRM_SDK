#!/usr/bin/env python3
"""Basic usage examples for the Neon CRM SDK."""

import os

from neon_crm import NeonClient, UserType
from neon_crm.exceptions import NeonAPIError


def main():
    """Demonstrate basic SDK usage."""
    # Initialize client (make sure to set NEON_ORG_ID and NEON_API_KEY env vars)
    try:
        client = NeonClient(
            org_id=os.getenv("NEON_ORG_ID"),
            api_key=os.getenv("NEON_API_KEY"),
        )
    except ValueError as e:
        print(f"Configuration error: {e}")
        print("Please set NEON_ORG_ID and NEON_API_KEY environment variables")
        return

    try:
        # Example 1: List accounts
        print("=== Listing Accounts ===")
        account_count = 0
        for account in client.accounts.list(
            page_size=10, user_type=UserType.INDIVIDUAL
        ):
            account_count += 1
            print(
                f"Account {account_count}: {account.get('firstName', '')} {account.get('lastName', '')}"
            )
            if account_count >= 5:  # Limit to first 5 for demo
                break

        # Example 2: Search for accounts
        print("\n=== Searching Accounts ===")
        search_request = {
            "searchFields": [
                {"field": "Account Type", "operator": "EQUAL", "value": "Individual"}
            ],
            "outputFields": ["Account ID", "First Name", "Last Name", "Email"],
        }

        search_count = 0
        for result in client.accounts.search(search_request):
            search_count += 1
            print(f"Search result {search_count}: {result}")
            if search_count >= 3:  # Limit for demo
                break

        # Example 3: Get search fields for accounts
        print("\n=== Available Search Fields ===")
        search_fields = client.accounts.get_search_fields()
        for field in search_fields[:5]:  # Show first 5
            print(f"- {field.get('displayName', field.get('name', 'Unknown'))}")

        # Example 4: Custom fields demonstration
        print("\n=== Custom Fields Example ===")
        try:
            # List first few custom fields
            custom_fields = list(client.accounts.list_custom_fields())
            if custom_fields:
                print(f"Found {len(custom_fields)} custom fields. First few:")
                for field in custom_fields[:3]:
                    field_id = field.get("id")
                    field_name = field.get("name", "Unknown")
                    print(f"  ID: {field_id}, Name: '{field_name}'")

                # Example search by custom field (using first field)
                first_field = custom_fields[0]
                field_id = first_field["id"]
                field_name = first_field["name"]

                print(f"\n  Searching accounts with non-blank '{field_name}' values...")
                custom_search = {
                    "searchFields": [{"field": field_id, "operator": "NOT_BLANK"}],
                    "outputFields": ["Account ID", "First Name", "Last Name", field_id],
                    "pagination": {"currentPage": 0, "pageSize": 3},
                }

                results = list(client.accounts.search(custom_search))
                if results:
                    print(f"  Found {len(results)} accounts:")
                    for account in results:
                        account_id = account.get("Account ID")
                        first_name = account.get("First Name", "")
                        last_name = account.get("Last Name", "")
                        custom_value = account.get(field_name, "N/A")
                        print(
                            f"    Account {account_id}: {first_name} {last_name} = '{custom_value}'"
                        )
                else:
                    print("  No accounts found with non-blank values")
            else:
                print("No custom fields found for accounts")
        except Exception as custom_error:
            print(f"Custom fields example failed: {custom_error}")

        # Example 5: List donations
        print("\n=== Listing Donations ===")
        donation_count = 0
        for donation in client.donations.list(page_size=5):
            donation_count += 1
            amount = donation.get("amount", 0)
            date = donation.get("date", "Unknown")
            print(f"Donation {donation_count}: ${amount} on {date}")
            if donation_count >= 3:  # Limit for demo
                break

    except NeonAPIError as e:
        print(f"API Error: {e.message}")
        print(f"Status Code: {e.status_code}")
        if e.response_data:
            print(f"Response: {e.response_data}")

    except Exception as e:
        print(f"Unexpected error: {e}")

    finally:
        # Clean up
        client.close()


if __name__ == "__main__":
    main()
