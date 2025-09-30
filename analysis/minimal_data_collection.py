#!/usr/bin/env python3
"""
MINIMAL DATA COLLECTION - Uses only CONFIRMED working fields
Copy this into your notebook to replace the existing data collection function.
"""

import pandas as pd
from datetime import datetime


def collect_minimal_data(client, years_back=3):
    """
    Collect data using ONLY confirmed working field names from field discovery.

    Returns:
        dict: Contains dataframes for accounts and donations with minimal fields
    """

    print(f"📥 Collecting minimal data ({years_back} years) - CONFIRMED FIELDS ONLY...")

    # Calculate date range
    end_date = datetime.now()
    start_date = end_date.replace(year=end_date.year - years_back)
    date_filter = start_date.strftime("%Y-%m-%d")

    data = {}

    # 1. Collect accounts with CONFIRMED working fields only
    print("\n👥 Collecting account data (minimal fields)...")
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
                # CORE FIELDS - These definitely work
                "Account ID",
                "Account Type",
                "First Name",
                "Last Name",
                "Company Name",
                "Email 1",
                "City",
                "State/Province",
                # CONFIRMED from field discovery
                "Phone 1 Area Code",  # We know this exists
                "Full Zip Code (F)",  # We know this exists
                "Account Created Date/Time",  # We know this exists
                "Account Last Modified Date/Time",  # We know this exists
                # Current year donation fields (using 2024 as discovered)
                "2024 Donation Amount",
                "2024 Donation Count",
                "2023 Donation Amount",
                "2023 Donation Count",
            ],
        }

        accounts = list(client.accounts.search(account_search, limit=5000))
        data["accounts"] = pd.DataFrame(accounts)
        print(f"✅ Collected {len(accounts):,} accounts")

        # Show what columns we actually got
        if not data["accounts"].empty:
            print(f"   Columns received: {list(data['accounts'].columns)}")

    except Exception as e:
        print(f"❌ Error with minimal account fields: {e}")

        # Ultra-minimal fallback
        try:
            print("🔄 Trying ultra-minimal fields...")
            account_search_ultra = {
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
                    "Email 1",
                ],
            }
            accounts = list(client.accounts.search(account_search_ultra, limit=5000))
            data["accounts"] = pd.DataFrame(accounts)
            print(f"✅ Collected {len(accounts):,} accounts (ultra-minimal)")

        except Exception as e2:
            print(f"❌ Ultra-minimal failed too: {e2}")
            data["accounts"] = pd.DataFrame()

    # 2. Collect donations with minimal fields
    print("\n💰 Collecting donation data (minimal fields)...")
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
                # CORE donation fields that should definitely work
                "Donation ID",
                "Account ID",
                "Donation Amount",
                "Donation Date",
            ],
        }

        donations = list(client.donations.search(donation_search, limit=10000))
        data["donations"] = pd.DataFrame(donations)
        print(f"✅ Collected {len(donations):,} donations")

        if not data["donations"].empty:
            print(f"   Columns received: {list(data['donations'].columns)}")

    except Exception as e:
        print(f"❌ Error collecting donations: {e}")
        data["donations"] = pd.DataFrame()

    # Skip other data types for now
    data["events"] = pd.DataFrame()
    data["attendees"] = pd.DataFrame()
    data["memberships"] = pd.DataFrame()
    data["activities"] = pd.DataFrame()

    print(f"\n🎯 Minimal data collection complete!")
    print(f"📊 Data summary:")
    for key, df in data.items():
        if not df.empty:
            print(f"   {key}: {len(df):,} records with {len(df.columns)} columns")
            print(f"      Columns: {list(df.columns)}")
        else:
            print(f"   {key}: 0 records")

    return data


print("✅ MINIMAL DATA COLLECTION FUNCTION READY")
print("📋 INSTRUCTIONS:")
print("1. Copy this function into your Jupyter notebook")
print("2. Replace the call with: raw_data = collect_minimal_data(client, years_back=3)")
print("3. Run to test with only confirmed working fields")
print("4. Once this works, we can gradually add more fields")
