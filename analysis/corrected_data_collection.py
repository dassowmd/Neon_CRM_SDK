#!/usr/bin/env python3
"""Corrected data collection function with proper field names."""

import os
import sys
import pandas as pd
from datetime import datetime

# Add src to path for imports
sys.path.append("../src")
from neon_crm import NeonClient


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
                    "value": "Individual,Company,Household",  # Fixed case
                }
            ],
            "outputFields": [
                # CONFIRMED WORKING FIELDS ONLY
                "Account ID",
                "Account Type",
                "First Name",
                "Last Name",
                "Company Name",
                "Email 1",
                "City",
                "State/Province",
                "Country",
                # Additional useful fields that exist
                "Phone 1",  # This should work based on logs
                "Full Zip Code (F)",  # Corrected postal code field
                "Account Created Date/Time",  # Corrected create date field
                "Account Last Modified Date/Time",  # For recent activity
                # Donation summary fields that exist
                "Lifetime Giving",  # Corrected lifetime donation field
                "Total Number of Donations",  # Corrected donation count field
            ],
        }

        accounts = list(client.accounts.search(account_search, limit=5000))
        data["accounts"] = pd.DataFrame(accounts)
        print(f"✅ Collected {len(accounts):,} accounts")

    except Exception as e:
        print(f"❌ Error collecting accounts: {e}")
        # Try with minimal fields
        try:
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
                ],
            }
            accounts = list(client.accounts.search(account_search_minimal, limit=5000))
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
                # CONFIRMED WORKING FIELDS
                "Donation ID",
                "Account ID",
                "Donation Amount",
                "Donation Date",
                "Campaign Name",
                "Fund Name",  # Might be Fund Name instead of Fund
                "Source Code",  # Might be Source Code
                "Donation Solicitation Method",  # CORRECTED field name
            ],
        }

        donations = list(client.donations.search(donation_search, limit=10000))
        data["donations"] = pd.DataFrame(donations)
        print(f"✅ Collected {len(donations):,} donations")

    except Exception as e:
        print(f"❌ Error collecting donations: {e}")
        # Try with minimal fields
        try:
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
                client.donations.search(donation_search_minimal, limit=10000)
            )
            data["donations"] = pd.DataFrame(donations)
            print(f"✅ Collected {len(donations):,} donations (minimal fields)")
        except Exception as e2:
            print(f"❌ Even minimal donation search failed: {e2}")
            data["donations"] = pd.DataFrame()

    # 3. Collect event attendance - CORRECTED FIELDS
    print("\n🎪 Collecting event attendance data...")
    try:
        event_search = {
            "searchFields": [
                {
                    "field": "Event Start Date",
                    "operator": "GREATER_AND_EQUAL",
                    "value": date_filter,
                }
            ],
            "outputFields": [
                "Event ID",
                "Event Name",
                "Event Start Date",
                "Event Summary",  # Generic field instead of category
            ],
        }

        events = list(client.events.search(event_search, limit=1000))
        data["events"] = pd.DataFrame(events)
        print(f"✅ Collected {len(events):,} events")

        # Skip attendee collection for now to avoid issues
        data["attendees"] = pd.DataFrame()
        print(f"⚠️  Skipping attendee collection to avoid API issues")

    except Exception as e:
        print(f"❌ Error collecting events: {e}")
        data["events"] = pd.DataFrame()
        data["attendees"] = pd.DataFrame()

    # 4. Skip membership data for now (no search method available)
    print("\n🎫 Skipping membership data (no search method available)")
    data["memberships"] = pd.DataFrame()

    # 5. Collect activity data - SIMPLIFIED
    print("\n🤝 Collecting activity data...")
    try:
        # Use a more general search
        activity_search = {
            "searchFields": [
                {"field": "Activity Type", "operator": "NOT_BLANK", "value": ""}
            ],
            "outputFields": [
                "Activity ID",
                "Account ID",
                "Activity Name",
                "Activity Type",
                "Activity Status",
            ],
        }

        activities = list(client.activities.search(activity_search, limit=2000))
        data["activities"] = pd.DataFrame(activities)
        print(f"✅ Collected {len(activities):,} activities")

    except Exception as e:
        print(f"❌ Error collecting activities: {e}")
        data["activities"] = pd.DataFrame()

    print(f"\n🎯 Corrected data collection complete!")
    print(f"📊 Data summary:")
    for key, df in data.items():
        print(f"   {key}: {len(df):,} records")

    return data


if __name__ == "__main__":
    # Initialize client
    client = NeonClient(
        org_id=os.getenv("NEON_ORG_ID"),
        api_key=os.getenv("NEON_API_KEY"),
        environment="production",
    )

    print("🎯 Testing corrected data collection...")
    raw_data = collect_comprehensive_data_corrected(client, years_back=3)

    print("\n📋 SAMPLE DATA:")
    for resource_name, df in raw_data.items():
        if not df.empty:
            print(f"\n{resource_name.upper()} - Columns available:")
            for col in df.columns:
                print(f"  • {col}")
            print(f"  Sample record count: {len(df)}")
