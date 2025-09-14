"""
Examples of handling pagination with the Neon CRM SDK.

This file demonstrates various pagination patterns and best practices
for working with large datasets in the Neon CRM API.
"""

from neon_crm import NeonClient, UserType
from neon_crm.types import SearchRequest


def basic_pagination_example():
    """Basic pagination using the list method."""
    client = NeonClient(org_id=None, api_key=None, environment="production")

    print("Basic Pagination Example")
    print("=" * 30)

    # The list method automatically handles pagination
    # It yields items one by one across all pages
    try:
        count = 0
        page_count = 1
        items_in_page = 0

        for account in client.accounts.list(
            page_size=5, user_type=UserType.INDIVIDUAL
        ):  # Small page size for demo
            count += 1
            items_in_page += 1

            print(
                f"Account {count}: {account.get('firstName', '')} {account.get('lastName', '')}"
            )

            # Track page boundaries (this is just for demonstration)
            if items_in_page >= 5:
                print(f"--- End of Page {page_count} ---")
                page_count += 1
                items_in_page = 0

            # Limit total results for demo
            if count >= 15:
                print(f"... (stopped at {count} items)")
                break

        print(f"\nTotal items processed: {count}")

    except Exception as e:
        print(f"Error in basic pagination: {e}")


def manual_pagination_example():
    """Manual pagination control."""
    client = NeonClient(org_id=None, api_key=None, environment="production")

    print("Manual Pagination Example")
    print("=" * 30)

    current_page = 0
    page_size = 10
    total_processed = 0

    try:
        while current_page <= 2:  # Process first 3 pages (0, 1, 2)
            print(f"\nProcessing page {current_page}...")

            # Get one page of results
            page_items = []
            items_this_page = 0

            for account in client.accounts.list(
                current_page=current_page,
                page_size=page_size,
                user_type=UserType.INDIVIDUAL,
            ):
                page_items.append(account)
                items_this_page += 1

                # Break after getting the expected page size
                if items_this_page >= page_size:
                    break

            if not page_items:
                print("No more results")
                break

            # Process the page
            for i, account in enumerate(page_items, 1):
                total_processed += 1
                account_type = account.get("userType", "Unknown")
                if account_type == "INDIVIDUAL":
                    name = (
                        f"{account.get('firstName', '')} {account.get('lastName', '')}"
                    )
                else:
                    name = account.get("companyName", "Unknown Company")

                print(f"  {i}. [{account_type}] {name}")

            print(f"Items on this page: {len(page_items)}")
            current_page += 1

        print(f"\nTotal items processed across all pages: {total_processed}")

    except Exception as e:
        print(f"Error in manual pagination: {e}")


def search_pagination_example():
    """Pagination with search requests."""
    client = NeonClient(org_id=None, api_key=None, environment="production")

    print("Search Pagination Example")
    print("=" * 30)

    # Search with custom pagination settings
    search_request: SearchRequest = {
        "searchFields": [
            {"field": "userType", "operator": "EQUAL", "value": "INDIVIDUAL"}
        ],
        "outputFields": ["accountId", "firstName", "lastName", "email", "dateCreated"],
        "pagination": {"currentPage": 0, "pageSize": 8},  # Small page size for demo
    }

    try:
        print("Searching for individual accounts...")
        count = 0

        # The search method handles pagination automatically
        for account in client.accounts.search(search_request):
            count += 1
            print(
                f"{count}. {account.get('firstName')} {account.get('lastName')} ({account.get('email')})"
            )

            # Limit results for demo
            if count >= 20:
                print("... (showing first 20 results)")
                break

        print(f"\nTotal search results processed: {count}")

    except Exception as e:
        print(f"Error in search pagination: {e}")


def pagination_with_filtering():
    """Pagination combined with filtering."""
    client = NeonClient(org_id=None, api_key=None, environment="production")

    print("Pagination with Filtering Example")
    print("=" * 35)

    try:
        print("Individual accounts with email addresses:")
        individual_count = 0

        # Filter by user type and page through results
        for account in client.accounts.list(user_type=UserType.INDIVIDUAL, page_size=5):
            # Additional filtering - only show accounts with email
            if account.get("email"):
                individual_count += 1
                print(
                    f"  {individual_count}. {account.get('firstName')} {account.get('lastName')} - {account.get('email')}"
                )

                if individual_count >= 10:
                    print("  ... (showing first 10 with emails)")
                    break

        print("\nCompany accounts:")
        company_count = 0

        for account in client.accounts.list(user_type=UserType.COMPANY, page_size=5):
            company_count += 1
            company_name = account.get("companyName", "Unknown Company")
            email = account.get("email", "No email")
            print(f"  {company_count}. {company_name} - {email}")

            if company_count >= 5:
                print("  ... (showing first 5 companies)")
                break

    except Exception as e:
        print(f"Error in filtered pagination: {e}")


def bulk_processing_example():
    """Example of processing large datasets with pagination."""
    client = NeonClient(org_id=None, api_key=None, environment="production")

    print("Bulk Processing Example")
    print("=" * 25)

    # Process all accounts in batches
    try:
        batch_size = 50  # Process in larger batches for efficiency
        total_accounts = 0
        accounts_with_email = 0
        accounts_without_email = 0

        print(f"Processing accounts in batches of {batch_size}...")

        for account in client.accounts.list(
            page_size=batch_size, user_type=UserType.INDIVIDUAL
        ):
            total_accounts += 1

            if account.get("email"):
                accounts_with_email += 1
            else:
                accounts_without_email += 1

            # Progress indicator
            if total_accounts % 100 == 0:
                print(f"  Processed {total_accounts} accounts so far...")

            # Stop for demo purposes
            if total_accounts >= 500:
                print(f"  Stopping at {total_accounts} accounts for demo")
                break

        print("\nBulk Processing Results:")
        print(f"Total accounts processed: {total_accounts}")
        print(f"Accounts with email: {accounts_with_email}")
        print(f"Accounts without email: {accounts_without_email}")
        print(f"Percentage with email: {(accounts_with_email/total_accounts)*100:.1f}%")

    except Exception as e:
        print(f"Error in bulk processing: {e}")


def pagination_performance_tips():
    """Tips and best practices for pagination performance."""
    print("Pagination Performance Tips")
    print("=" * 30)
    print(
        """
    1. PAGE SIZE OPTIMIZATION:
       - Use page sizes between 50-200 for best performance
       - Smaller pages (10-25) for interactive display
       - Larger pages (100-500) for bulk processing

    2. MEMORY MANAGEMENT:
       - The SDK yields items one at a time to avoid loading all data into memory
       - Process items as they come rather than collecting into lists

    3. API EFFICIENCY:
       - Use search with outputFields to get only needed fields
       - Apply filters at the API level rather than in Python
       - Cache results when possible to avoid repeated API calls

    4. ERROR HANDLING:
       - Implement retry logic for transient network errors
       - Handle rate limiting gracefully
       - Save progress periodically for long-running processes

    5. EXAMPLE PATTERNS:
    """
    )

    # Efficient pattern
    print("    # EFFICIENT: Process items one at a time")
    print(
        "    for account in client.accounts.list(page_size=100, user_type=UserType.INDIVIDUAL):"
    )
    print("        process_account(account)  # Process immediately")
    print()

    # Inefficient pattern
    print("    # INEFFICIENT: Loading all into memory first")
    print(
        "    all_accounts = list(client.accounts.list(user_type=UserType.INDIVIDUAL))  # Don't do this!"
    )
    print("    for account in all_accounts:")
    print("        process_account(account)")
    print()

    print("    # GOOD: Using search with specific fields")
    print("    search_request = {")
    print("        'outputFields': ['accountId', 'firstName', 'lastName', 'email'],")
    print("        'pagination': {'pageSize': 100}")
    print("    }")
    print("    for account in client.accounts.search(search_request):")
    print("        process_account(account)")


if __name__ == "__main__":
    print("Neon CRM SDK - Pagination Examples")
    print("=" * 50)

    # Note: Replace with your actual credentials
    print("Note: Update the org_id and api_key with your actual credentials")
    print("      Set the appropriate environment (production/trial)")
    print()

    # Performance tips (no API calls)
    pagination_performance_tips()

    # Uncomment the examples you want to run:

    # print("\n" + "="*50)
    # basic_pagination_example()

    # print("\n" + "="*50)
    # manual_pagination_example()

    # print("\n" + "="*50)
    # search_pagination_example()

    # print("\n" + "="*50)
    # pagination_with_filtering()

    # print("\n" + "="*50)
    # bulk_processing_example()

    print(
        "\nExamples ready to run. Uncomment the desired examples and add your credentials."
    )
