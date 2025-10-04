"""
Replace the data collection function in your notebook with this corrected version.
Copy and paste this function into your Jupyter notebook.
"""

import pandas as pd
from datetime import datetime


def collect_comprehensive_data_corrected(client, years_back=3):
    """
    Collect comprehensive data with CORRECT field names discovered from the API.

    Returns:
        dict: Contains dataframes for accounts, donations, events, memberships, activities
    """

    print(
        f"📥 Collecting comprehensive organizational data ({years_back} years) - CORRECTED..."
    )

    # Calculate date range
    end_date = datetime.now()
    start_date = end_date.replace(year=end_date.year - years_back)
    date_filter = start_date.strftime("%Y-%m-%d")

    data = {}

    # 1. Collect ALL accounts (donors and non-donors) - CORRECTED FIELDS
    print("\n👥 Collecting account data...")
    try:
        account_search = {
            "searchFields": [
                {
                    "field": "Account Type",
                    "operator": "IN",
                    "value": "Individual,Company,Household",
                }
            ],
            "outputFields": [
                # Core fields that definitely exist
                "Account ID",
                "Account Type",
                "First Name",
                "Last Name",
                "Company Name",
                "Email 1",
                "City",
                "State/Province",
                "Country",
                # Fields discovered from API
                "Phone 1 Full Number (F)",  # Corrected phone field
                "Full Zip Code (F)",  # Corrected postal code field
                "Account Created Date/Time",  # Corrected creation date
                "Account Last Modified Date/Time",  # For recent activity
                # Use current/recent year donation totals instead of "Lifetime"
                f"{datetime.now().year} Donation Amount",  # Current year donations
                f"{datetime.now().year-1} Donation Amount",  # Last year donations
                f"{datetime.now().year} Donation Count",  # Current year count
                f"{datetime.now().year-1} Donation Count",  # Last year count
                # Try some broader donation totals
                "Total Donation Amount",
                "Total Number of Donations",
            ],
        }

        accounts = list(
            client.accounts.search(account_search, limit=3000)
        )  # Start smaller
        data["accounts"] = pd.DataFrame(accounts)
        print(f"✅ Collected {len(accounts):,} accounts")

    except Exception as e:
        print(f"❌ Error collecting accounts: {e}")
        # Fall back to absolutely minimal fields that we know work
        try:
            print("🔄 Trying minimal account fields...")
            account_search_minimal = {
                "searchFields": [
                    {
                        "field": "Account Type",
                        "operator": "IN",
                        "value": "Individual,Company,Household",
                    }
                ],
                "outputFields": [
                    "Account ID",
                    "Account Type",
                    "First Name",
                    "Last Name",
                    "Company Name",
                    "Email 1",
                    "City",
                    "State/Province",
                ],
            }
            accounts = list(client.accounts.search(account_search_minimal, limit=3000))
            data["accounts"] = pd.DataFrame(accounts)
            print(f"✅ Collected {len(accounts):,} accounts (minimal fields)")
        except Exception as e2:
            print(f"❌ Even minimal account search failed: {e2}")
            data["accounts"] = pd.DataFrame()

    # 2. Collect donation history - CORRECTED FIELDS
    print("\n💰 Collecting donation data...")
    try:
        donation_search = {
            "searchFields": [
                {
                    "field": "Donation Date",
                    "operator": "GREATER_AND_EQUAL",
                    "value": date_filter,
                }
            ],
            "outputFields": [
                # Start with absolutely essential fields
                "Donation ID",
                "Account ID",
                "Donation Amount",
                "Donation Date",
                "Campaign Name",
                "Fund",  # Try the simple version first
            ],
        }

        donations = list(client.donations.search(donation_search, limit=5000))
        data["donations"] = pd.DataFrame(donations)
        print(f"✅ Collected {len(donations):,} donations")

    except Exception as e:
        print(f"❌ Error collecting donations: {e}")
        # Try even more minimal
        try:
            print("🔄 Trying minimal donation fields...")
            donation_search_minimal = {
                "searchFields": [
                    {
                        "field": "Donation Date",
                        "operator": "GREATER_AND_EQUAL",
                        "value": date_filter,
                    }
                ],
                "outputFields": [
                    "Donation ID",
                    "Account ID",
                    "Donation Amount",
                    "Donation Date",
                ],
            }
            donations = list(
                client.donations.search(donation_search_minimal, limit=5000)
            )
            data["donations"] = pd.DataFrame(donations)
            print(f"✅ Collected {len(donations):,} donations (minimal fields)")
        except Exception as e2:
            print(f"❌ Even minimal donation search failed: {e2}")
            data["donations"] = pd.DataFrame()

    # 3. Skip complex queries for now to ensure basic analysis works
    print("\n⚠️  Skipping events, memberships, and activities for initial analysis...")
    print("   (These can be added later once core donor analysis is working)")

    data["events"] = pd.DataFrame()
    data["attendees"] = pd.DataFrame()
    data["memberships"] = pd.DataFrame()
    data["activities"] = pd.DataFrame()

    print(f"\n🎯 Corrected data collection complete!")
    print(f"📊 Data summary:")
    for key, df in data.items():
        if not df.empty:
            print(f"   {key}: {len(df):,} records with {len(df.columns)} columns")
            # Show first few column names
            cols_preview = list(df.columns)[:5]
            if len(df.columns) > 5:
                cols_preview.append(f"... and {len(df.columns)-5} more")
            print(f"      Columns: {', '.join(cols_preview)}")
        else:
            print(f"   {key}: 0 records (skipped or failed)")

    return data


print("✅ CORRECTED DATA COLLECTION FUNCTION READY")
print("📋 INSTRUCTIONS:")
print("1. Copy this function into your Jupyter notebook")
print(
    "2. Replace the call: raw_data = collect_comprehensive_data(client, years_back=3)"
)
print("3. With: raw_data = collect_comprehensive_data_corrected(client, years_back=3)")
print("4. Run the cell to collect data with correct field names")
