#!/usr/bin/env python3
"""
ALL COLUMNS DATA COLLECTION - Grabs ALL available fields automatically
Copy this into your notebook to replace the existing data collection function.
"""

import pandas as pd
from datetime import datetime


def collect_all_columns_data(client, years_back=3):
    """
    Collect data using ALL available fields from the API.
    This avoids field name errors by not specifying outputFields.

    Returns:
        dict: Contains dataframes with all available columns
    """

    print(f"📥 Collecting ALL available data ({years_back} years)...")

    # Calculate date range
    end_date = datetime.now()
    start_date = end_date.replace(year=end_date.year - years_back)
    date_filter = start_date.strftime("%Y-%m-%d")

    data = {}

    # 1. Collect ALL account data without specifying outputFields
    print("\n👥 Collecting ALL account columns...")
    try:
        account_search = {
            "searchFields": [
                {
                    "field": "Account Type",
                    "operator": "IN",
                    "value": "Individual,Company,Household",
                }
            ]
            # NO outputFields - this will return ALL available columns
        }

        accounts = list(client.accounts.search(account_search, limit=5000))
        data["accounts"] = pd.DataFrame(accounts)
        print(f"✅ Collected {len(accounts):,} accounts with ALL columns")

        if not data["accounts"].empty:
            print(f"   Total columns received: {len(data['accounts'].columns)}")
            print(f"   Sample columns: {list(data['accounts'].columns)[:10]}...")

    except Exception as e:
        print(f"❌ Error collecting all account columns: {e}")
        data["accounts"] = pd.DataFrame()

    # 2. Collect ALL donation data without specifying outputFields
    print("\n💰 Collecting ALL donation columns...")
    try:
        donation_search = {
            "searchFields": [
                {
                    "field": "Donation Date",
                    "operator": "GREATER_AND_EQUAL",
                    "value": date_filter,
                }
            ]
            # NO outputFields - this will return ALL available columns
        }

        donations = list(client.donations.search(donation_search, limit=10000))
        data["donations"] = pd.DataFrame(donations)
        print(f"✅ Collected {len(donations):,} donations with ALL columns")

        if not data["donations"].empty:
            print(f"   Total columns received: {len(data['donations'].columns)}")
            print(f"   Sample columns: {list(data['donations'].columns)[:10]}...")

    except Exception as e:
        print(f"❌ Error collecting all donation columns: {e}")
        data["donations"] = pd.DataFrame()

    # 3. Try events with ALL columns
    print("\n🎪 Collecting ALL event columns...")
    try:
        event_search = {
            "searchFields": [
                {
                    "field": "Event Start Date",
                    "operator": "GREATER_AND_EQUAL",
                    "value": date_filter,
                }
            ]
            # NO outputFields
        }

        events = list(client.events.search(event_search, limit=1000))
        data["events"] = pd.DataFrame(events)
        print(f"✅ Collected {len(events):,} events with ALL columns")

        if not data["events"].empty:
            print(f"   Total columns received: {len(data['events'].columns)}")

    except Exception as e:
        print(f"❌ Error collecting events: {e}")
        data["events"] = pd.DataFrame()

    # 4. Try activities with ALL columns
    print("\n🤝 Collecting ALL activity columns...")
    try:
        activity_search = {
            "searchFields": [
                {"field": "Activity Type", "operator": "NOT_BLANK", "value": ""}
            ]
            # NO outputFields
        }

        activities = list(client.activities.search(activity_search, limit=2000))
        data["activities"] = pd.DataFrame(activities)
        print(f"✅ Collected {len(activities):,} activities with ALL columns")

        if not data["activities"].empty:
            print(f"   Total columns received: {len(data['activities'].columns)}")

    except Exception as e:
        print(f"❌ Error collecting activities: {e}")
        data["activities"] = pd.DataFrame()

    # Skip these for now
    data["attendees"] = pd.DataFrame()
    data["memberships"] = pd.DataFrame()

    print(f"\n🎯 ALL COLUMNS data collection complete!")
    print(f"📊 Data summary:")
    for key, df in data.items():
        if not df.empty:
            print(f"   {key}: {len(df):,} records with {len(df.columns)} columns")
        else:
            print(f"   {key}: 0 records")

    # Show all actual column names for the main dataframes
    if not data["accounts"].empty:
        print(f"\n📋 ACCOUNT COLUMNS AVAILABLE:")
        for i, col in enumerate(sorted(data["accounts"].columns)):
            print(f"   {i+1:3d}. {col}")

    return data


print("✅ ALL COLUMNS DATA COLLECTION FUNCTION READY")
print("📋 INSTRUCTIONS:")
print("1. Copy this function into your Jupyter notebook")
print(
    "2. Replace the call with: raw_data = collect_all_columns_data(client, years_back=3)"
)
print("3. Run to get ALL available columns without field name errors")
print("4. Use the column list output to update the feature engineering function")
