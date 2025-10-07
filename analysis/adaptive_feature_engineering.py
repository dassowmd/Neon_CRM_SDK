#!/usr/bin/env python3
"""
ADAPTIVE FEATURE ENGINEERING - Works with whatever columns are actually available
Copy this into your notebook to replace the existing feature engineering function.
"""

import pandas as pd
import numpy as np
from datetime import datetime
import re


def engineer_adaptive_features(raw_data):
    """
    Create features using whatever columns are actually available.
    Discovers and uses any columns that exist instead of hardcoding field names.

    Features include:
    - All discovered donation-related fields
    - All discovered engagement metrics
    - All discovered demographic indicators
    - All discovered timing factors
    """

    print("🔧 Engineering features with ADAPTIVE column discovery...")

    # Start with accounts as base
    accounts_df = raw_data["accounts"].copy()
    if accounts_df.empty:
        print("❌ No account data available")
        return None

    print(
        f"📊 Processing {len(accounts_df):,} accounts with {len(accounts_df.columns)} columns..."
    )

    # === COLUMN DISCOVERY ===
    print("\n🔍 Discovering available columns...")

    available_cols = list(accounts_df.columns)

    # Find columns by pattern matching
    def find_columns_by_pattern(patterns, description):
        found = []
        for pattern in patterns:
            matches = [
                col for col in available_cols if re.search(pattern, col, re.IGNORECASE)
            ]
            found.extend(matches)
        found = list(set(found))  # Remove duplicates
        print(f"   {description}: {len(found)} columns found")
        if found:
            print(f"      Examples: {found[:3]}")
        return found

    # Discover column categories
    donation_amount_cols = find_columns_by_pattern(
        [r"donation.*amount", r"giving", r"gift", r"contributed"],
        "💰 Donation Amount Fields",
    )

    donation_count_cols = find_columns_by_pattern(
        [r"donation.*count", r"number.*donation", r"gift.*count"],
        "🔢 Donation Count Fields",
    )

    phone_cols = find_columns_by_pattern(
        [r"phone", r"mobile", r"cell"], "📞 Phone Fields"
    )

    find_columns_by_pattern(
        [r"address", r"street", r"city", r"state", r"zip", r"postal", r"country"],
        "🏠 Address Fields",
    )

    email_cols = find_columns_by_pattern([r"email"], "📧 Email Fields")

    date_cols = find_columns_by_pattern(
        [r"date", r"time", r"created", r"modified", r"updated"], "📅 Date Fields"
    )

    event_cols = find_columns_by_pattern(
        [r"event", r"registration", r"attendance"], "🎪 Event Fields"
    )

    membership_cols = find_columns_by_pattern(
        [r"membership", r"member"], "🎫 Membership Fields"
    )

    activity_cols = find_columns_by_pattern(
        [r"activity", r"volunteer", r"engagement"], "🤝 Activity Fields"
    )

    # === DATA TYPE CONVERSION ===
    print("\n🔄 Converting data types...")

    # Convert Account ID to numeric
    if "Account ID" in accounts_df.columns:
        accounts_df["Account ID"] = pd.to_numeric(
            accounts_df["Account ID"], errors="coerce"
        )

    # Convert all date columns
    for col in date_cols:
        if col in accounts_df.columns:
            try:
                accounts_df[col] = pd.to_datetime(accounts_df[col], errors="coerce")
                print(f"   ✅ Converted date column: {col}")
            except Exception:
                print(f"   ⚠️  Could not convert date column: {col}")

    # === TARGET VARIABLE CREATION ===
    print("\n🎯 Creating target variables...")

    # Use the first available donation amount field
    for col in donation_amount_cols:
        if col in accounts_df.columns:
            accounts_df["lifetime_donation_amount"] = pd.to_numeric(
                accounts_df[col], errors="coerce"
            ).fillna(0)
            print(f"   Using donation amount field: {col}")
            break
    else:
        accounts_df["lifetime_donation_amount"] = 0
        print("   ⚠️  No donation amount field found, using zeros")

    # Use the first available donation count field
    for col in donation_count_cols:
        if col in accounts_df.columns:
            accounts_df["donation_count"] = pd.to_numeric(
                accounts_df[col], errors="coerce"
            ).fillna(0)
            print(f"   Using donation count field: {col}")
            break
    else:
        accounts_df["donation_count"] = 0
        print("   ⚠️  No donation count field found, using zeros")

    # Target variables
    accounts_df["is_donor"] = (
        (accounts_df["donation_count"] > 0)
        | (accounts_df["lifetime_donation_amount"] > 0)
    ).astype(int)

    accounts_df["is_major_donor"] = (
        accounts_df["lifetime_donation_amount"] >= 1000
    ).astype(int)

    print(
        f"   Donors: {accounts_df['is_donor'].sum():,} ({accounts_df['is_donor'].mean()*100:.1f}%)"
    )
    print(
        f"   Major donors: {accounts_df['is_major_donor'].sum():,} ({accounts_df['is_major_donor'].mean()*100:.1f}%)"
    )

    # === DEMOGRAPHIC FEATURES ===
    print("\n👥 Creating demographic features...")

    # Account type
    if "Account Type" in accounts_df.columns:
        accounts_df["is_individual"] = (
            accounts_df["Account Type"] == "Individual"
        ).astype(int)
        accounts_df["is_company"] = (accounts_df["Account Type"] == "Company").astype(
            int
        )
        accounts_df["is_household"] = (
            accounts_df["Account Type"] == "Household"
        ).astype(int)

    # Contact completeness
    contact_score = 0
    contact_components = 0

    # Email completeness
    for col in email_cols:
        if col in accounts_df.columns:
            accounts_df["has_email"] = (~accounts_df[col].isna()).astype(int)
            contact_score += accounts_df["has_email"]
            contact_components += 1
            break
    else:
        accounts_df["has_email"] = 0

    # Phone completeness
    for col in phone_cols:
        if col in accounts_df.columns:
            accounts_df["has_phone"] = (~accounts_df[col].isna()).astype(int)
            contact_score += accounts_df["has_phone"]
            contact_components += 1
            break
    else:
        accounts_df["has_phone"] = 0

    # Address completeness
    address_score = 0
    address_components = 0
    for col in ["City", "State/Province", "Country"]:  # Try common address fields
        if col in accounts_df.columns:
            has_field = (~accounts_df[col].isna()).astype(int)
            address_score += has_field
            address_components += 1

    if address_components > 0:
        accounts_df["has_address"] = (address_score >= 1).astype(int)
        contact_score += accounts_df["has_address"]
        contact_components += 1
    else:
        accounts_df["has_address"] = 0

    # Overall contact completeness
    if contact_components > 0:
        accounts_df["contact_completeness"] = contact_score / contact_components
    else:
        accounts_df["contact_completeness"] = 0

    # === TEMPORAL FEATURES ===
    print("\n⏰ Creating temporal features...")

    # Account age
    create_date_col = None
    for col in date_cols:
        if "creat" in col.lower() and col in accounts_df.columns:
            create_date_col = col
            break

    if create_date_col:
        accounts_df["account_age_days"] = (
            datetime.now() - accounts_df[create_date_col]
        ).dt.days
        accounts_df["account_age_years"] = accounts_df["account_age_days"] / 365.25
        print(f"   Using creation date: {create_date_col}")
    else:
        accounts_df["account_age_days"] = 365
        accounts_df["account_age_years"] = 1
        print("   ⚠️  No creation date found, using default")

    # Recent activity
    activity_date_col = None
    for col in date_cols:
        if "modif" in col.lower() and col in accounts_df.columns:
            activity_date_col = col
            break

    if activity_date_col:
        accounts_df["days_since_last_activity"] = (
            datetime.now() - accounts_df[activity_date_col]
        ).dt.days
        accounts_df["has_recent_activity"] = (
            accounts_df["days_since_last_activity"] <= 180
        ).astype(int)
        print(f"   Using activity date: {activity_date_col}")
    else:
        accounts_df["days_since_last_activity"] = 365
        accounts_df["has_recent_activity"] = 0
        print("   ⚠️  No activity date found, using default")

    # === ENGAGEMENT FEATURES ===
    print("\n🚀 Creating engagement features...")

    # Event engagement
    event_score = 0
    for col in event_cols:
        if col in accounts_df.columns:
            try:
                event_values = pd.to_numeric(accounts_df[col], errors="coerce").fillna(
                    0
                )
                event_score += (event_values > 0).astype(int)
            except Exception:
                pass

    accounts_df["event_engagement"] = (event_score > 0).astype(int)

    # Membership engagement
    membership_score = 0
    for col in membership_cols:
        if col in accounts_df.columns:
            try:
                membership_values = pd.to_numeric(
                    accounts_df[col], errors="coerce"
                ).fillna(0)
                membership_score += (membership_values > 0).astype(int)
            except Exception:
                pass

    accounts_df["membership_engagement"] = (membership_score > 0).astype(int)

    # Activity engagement
    activity_score = 0
    for col in activity_cols:
        if col in accounts_df.columns:
            try:
                activity_values = pd.to_numeric(
                    accounts_df[col], errors="coerce"
                ).fillna(0)
                activity_score += (activity_values > 0).astype(int)
            except Exception:
                pass

    accounts_df["activity_engagement"] = (activity_score > 0).astype(int)

    # === COMPOSITE SCORES ===
    print("\n📊 Creating composite scores...")

    # Overall engagement score
    engagement_components = [
        "contact_completeness",
        "has_recent_activity",
        "event_engagement",
        "membership_engagement",
        "activity_engagement",
    ]

    valid_components = [
        c
        for c in engagement_components
        if c in accounts_df.columns and accounts_df[c].var() > 0
    ]

    if valid_components:
        accounts_df["engagement_score"] = accounts_df[valid_components].mean(axis=1)
    else:
        accounts_df["engagement_score"] = accounts_df["contact_completeness"]

    accounts_df["high_engagement"] = (accounts_df["engagement_score"] >= 0.6).astype(
        int
    )

    # === WEALTH INDICATORS ===
    print("\n💎 Creating wealth indicators...")

    # Company indicator
    if "is_company" in accounts_df.columns:
        accounts_df["potential_high_capacity"] = accounts_df["is_company"]
    else:
        accounts_df["potential_high_capacity"] = 0

    # === ADDITIONAL DISCOVERED FEATURES ===
    print("\n🔍 Creating features from ALL discovered numeric columns...")

    # Find all numeric columns that might be predictive
    numeric_cols = accounts_df.select_dtypes(include=[np.number]).columns.tolist()

    # Exclude our created features and ID columns
    exclude_patterns = [
        "is_",
        "has_",
        "engagement",
        "account_age",
        "days_since",
        "contact_",
        "Account ID",
    ]
    potential_features = []

    for col in numeric_cols:
        if not any(pattern in col for pattern in exclude_patterns):
            if accounts_df[col].var() > 0:  # Has variation
                potential_features.append(col)

    print(
        f"   Found {len(potential_features)} additional numeric features with variation"
    )
    if potential_features:
        print(f"   Examples: {potential_features[:5]}")

    # Create binary indicators for non-zero values in these columns
    for col in potential_features[:20]:  # Limit to top 20 to avoid too many features
        try:
            accounts_df[f'has_{col.lower().replace(" ", "_").replace("/", "_")}'] = (
                accounts_df[col] > 0
            ).astype(int)
        except Exception:
            pass

    print("\n🎯 Adaptive feature engineering complete!")
    print(
        f"📊 Final dataset: {len(accounts_df):,} records with {len(accounts_df.columns)} features"
    )
    print(f"   - Non-donors: {(~accounts_df['is_donor'].astype(bool)).sum():,}")
    print(f"   - Donors: {accounts_df['is_donor'].sum():,}")
    print(f"   - Major donors: {accounts_df['is_major_donor'].sum():,}")
    print(f"   - High engagement: {accounts_df['high_engagement'].sum():,}")

    return accounts_df


print("✅ ADAPTIVE FEATURE ENGINEERING FUNCTION READY")
print("📋 INSTRUCTIONS:")
print("1. Copy this function into your Jupyter notebook")
print("2. Replace the call with: donor_features = engineer_adaptive_features(raw_data)")
print("3. This will work with whatever columns you actually have")
print("4. It will discover and use unexpected predictive columns automatically")
