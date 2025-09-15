"""
Examples of retrieving and searching accounts with the Neon CRM SDK.

This file demonstrates various ways to find, search, and retrieve account
information including related data like donations, memberships, etc.
"""

from neon_crm import NeonClient, UserType
from neon_crm.types import SearchRequest


def list_all_accounts():
    """List all accounts with basic pagination."""
    client = NeonClient(org_id=None, api_key=None, environment="production")

    try:
        print("Fetching all accounts...")
        count = 0
        for account in client.accounts.list(
            page_size=10, user_type=UserType.INDIVIDUAL
        ):
            count += 1
            account_type = account.get("userType", "Unknown")
            if account_type == "INDIVIDUAL":
                name = f"{account.get('firstName', '')} {account.get('lastName', '')}"
            else:
                name = account.get("companyName", "Unknown Company")

            print(
                f"{count}. [{account_type}] {name} ({account.get('email', 'No email')})"
            )

            # Limit output for demo
            if count >= 20:
                print("... (showing first 20 accounts)")
                break

    except Exception as e:
        print(f"Error listing accounts: {e}")


def search_accounts_by_email():
    """Search for accounts by email address."""
    client = NeonClient(org_id=None, api_key=None, environment="production")

    # Search using the list method with email filter
    try:
        print("Searching accounts by email...")
        for account in client.accounts.list(
            email="john.doe@example.com", user_type=UserType.INDIVIDUAL
        ):
            account_type = account.get("userType", "Unknown")
            name = f"{account.get('firstName', '')} {account.get('lastName', '')}"
            print(f"Found: [{account_type}] {name} - {account.get('email')}")

    except Exception as e:
        print(f"Error searching by email: {e}")


def advanced_account_search():
    """Perform advanced search using the search endpoint."""
    client = NeonClient(org_id=None, api_key=None, environment="production")

    # Advanced search with multiple criteria
    search_request: SearchRequest = {
        "searchFields": [
            {"field": "First Name", "operator": "CONTAIN", "value": "Testy"},
            {"field": "Account Type", "operator": "EQUAL", "value": "INDIVIDUAL"},
        ],
        "outputFields": [
            "Account ID",
            "First Name",
            "Last Name",
            "Email 1",
            "Account Type",
        ],
        "pagination": {"currentPage": 0, "pageSize": 25},
    }

    try:
        print("Performing advanced search...")
        results = client.accounts.search(search_request)

        for account in results:
            print(f"Account ID: {account.get('Account ID')}")
            print(f"Name: {account.get('First Name')} {account.get('Last Name')}")
            print(f"Email: {account.get('Email 1')}")
            print("-" * 40)

    except Exception as e:
        print(f"Error in advanced search: {e}")


def get_account_details():
    """Get detailed information about a specific account."""
    client = NeonClient(org_id=None, api_key=None, environment="production")

    # Replace with an actual account ID
    account_id = "12345"

    try:
        print(f"Getting details for account {account_id}...")
        account_res = client.accounts.get(account_id)

        if account_res.get("individualAccount"):
            account = account_res.get("individualAccount")
        elif account_res.get("companyAccount"):
            account = account_res.get("companyAccount")
        else:
            raise Exception(f"Could not get account details for account {account_id}")
        print("Account Details:")
        print(f"ID: {account.get('accountId')}")

        if account.get("individualAccount"):
            print(f"Name: {account.get('firstName')} {account.get('lastName')}")
        else:
            print(f"Company: {account.get('name')}")

        print(f"Email: {account.get('email')}")
        print(f"Phone: {account.get('phone')}")
        print(f"Created: {account.get('dateCreated')}")

    except Exception as e:
        print(f"Error getting account details: {e}")


def get_account_donations():
    """Get donation history for a specific account."""
    client = NeonClient(org_id=None, api_key=None, environment="production")

    # Replace with an actual account ID
    account_id = "12345"

    try:
        print(f"Getting donations for account {account_id}...")
        count = 0
        total_amount = 0.0

        for donation in client.accounts.get_donations(account_id):
            count += 1
            amount = float(donation.get("amount", 0))
            total_amount += amount

            print(f"Donation {count}:")
            print(f"  Amount: ${amount:.2f}")
            print(f"  Date: {donation.get('date')}")
            print(f"  Campaign: {donation.get('campaign', {}).get('name', 'N/A')}")
            print(f"  Fund: {donation.get('fund', {}).get('name', 'N/A')}")
            print()

            # Limit output for demo
            if count >= 10:
                print("... (showing first 10 donations)")
                break

        if count > 0:
            print(f"Total donations shown: {count}")
            print(f"Total amount: ${total_amount:.2f}")
        else:
            print("No donations found for this account")

    except Exception as e:
        print(f"Error getting donations: {e}")


def get_account_memberships():
    """Get membership history for a specific account."""
    client = NeonClient(org_id=None, api_key=None, environment="production")

    # Replace with an actual account ID
    account_id = "12345"

    try:
        print(f"Getting memberships for account {account_id}...")
        count = 0

        for membership in client.accounts.get_memberships(account_id):
            count += 1

            print(f"Membership {count}:")
            print(f"  Type: {membership.get('membershipType', {}).get('name', 'N/A')}")
            print(
                f"  Level: {membership.get('membershipLevel', {}).get('name', 'N/A')}"
            )
            print(f"  Status: {membership.get('status', 'N/A')}")
            print(f"  Enrollment: {membership.get('enrollmentDate', 'N/A')}")
            print(f"  Expiration: {membership.get('expirationDate', 'N/A')}")
            print()

            # Limit output for demo
            if count >= 5:
                print("... (showing first 5 memberships)")
                break

        if count == 0:
            print("No memberships found for this account")

    except Exception as e:
        print(f"Error getting memberships: {e}")


def get_account_orders():
    """Get order history for a specific account."""
    client = NeonClient(org_id=None, api_key=None, environment="production")

    # Replace with an actual account ID
    account_id = "12345"

    try:
        print(f"Getting orders for account {account_id}...")
        count = 0

        for order in client.accounts.get_orders(account_id):
            count += 1

            print(f"Order {count}:")
            print(f"  Order ID: {order.get('orderId', 'N/A')}")
            print(f"  Date: {order.get('orderDate', 'N/A')}")
            print(f"  Status: {order.get('status', 'N/A')}")
            print(f"  Total: ${order.get('total', 0):.2f}")
            print()

            # Limit output for demo
            if count >= 5:
                print("... (showing first 5 orders)")
                break

        if count == 0:
            print("No orders found for this account")

    except Exception as e:
        print(f"Error getting orders: {e}")


def get_account_pledges():
    """Get pledge information for a specific account."""
    client = NeonClient(org_id=None, api_key=None, environment="production")

    # Replace with an actual account ID
    account_id = "12345"

    try:
        print(f"Getting pledges for account {account_id}...")
        count = 0

        for pledge in client.accounts.get_pledges(account_id):
            count += 1

            print(f"Pledge {count}:")
            print(f"  Pledge ID: {pledge.get('pledgeId', 'N/A')}")
            print(f"  Amount: ${pledge.get('amount', 0):.2f}")
            print(f"  Date: {pledge.get('pledgeDate', 'N/A')}")
            print(f"  Status: {pledge.get('status', 'N/A')}")
            print(f"  Campaign: {pledge.get('campaign', {}).get('name', 'N/A')}")
            print()

            # Limit output for demo
            if count >= 5:
                print("... (showing first 5 pledges)")
                break

        if count == 0:
            print("No pledges found for this account")

    except Exception as e:
        print(f"Error getting pledges: {e}")


def filter_accounts_by_type():
    """Filter accounts by type (INDIVIDUAL vs COMPANY)."""
    client = NeonClient(org_id=None, api_key=None, environment="production")

    # Get individual accounts only
    try:
        print("Individual accounts:")
        individual_count = 0
        for account in client.accounts.list(user_type=UserType.INDIVIDUAL, page_size=5):
            individual_count += 1
            name = f"{account.get('firstName', '')} {account.get('lastName', '')}"
            print(f"  {individual_count}. {name} ({account.get('email', 'No email')})")

        print("\nCompany accounts:")
        company_count = 0
        for account in client.accounts.list(user_type=UserType.COMPANY, page_size=5):
            company_count += 1
            name = account.get("companyName", "Unknown Company")
            print(f"  {company_count}. {name} ({account.get('email', 'No email')})")

    except Exception as e:
        print(f"Error filtering accounts: {e}")


if __name__ == "__main__":
    print("Neon CRM SDK - Account Retrieval Examples")
    print("=" * 50)

    # Note: Replace with your actual credentials and account IDs
    print("Note: Update the org_id and api_key with your actual credentials")
    print("      Update account_id variables with real account IDs from your system")
    print("      Set the appropriate environment (production/trial)")
    print()

    # Uncomment the examples you want to run:

    # print("Listing all accounts...")
    # list_all_accounts()

    # print("\nSearching accounts by email...")
    # search_accounts_by_email()

    print("\nPerforming advanced search...")
    advanced_account_search()

    print("\nGetting account details...")
    get_account_details()

    # print("\nGetting account donations...")
    # get_account_donations()

    # print("\nGetting account memberships...")
    # get_account_memberships()

    # print("\nGetting account orders...")
    # get_account_orders()

    # print("\nGetting account pledges...")
    # get_account_pledges()

    # print("\nFiltering accounts by type...")
    # filter_accounts_by_type()

    print(
        "Examples ready to run. Uncomment the desired examples and add your credentials."
    )
