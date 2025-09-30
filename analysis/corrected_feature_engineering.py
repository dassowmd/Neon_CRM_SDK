"""
Corrected feature engineering function that works with actual field names.
Copy this into your notebook to replace the existing feature engineering function.
"""


def engineer_donor_features_corrected(raw_data):
    """
    Create comprehensive features for donor propensity modeling with CORRECTED field names.

    Features include:
    - Demographic indicators
    - Engagement metrics
    - Behavioral patterns
    - Timing factors
    """

    print("🔧 Engineering features for donor propensity analysis (CORRECTED)...")

    # Start with accounts as base
    accounts_df = raw_data["accounts"].copy()
    if accounts_df.empty:
        print("❌ No account data available")
        return None

    print(f"📊 Processing {len(accounts_df):,} accounts...")

    # Clean and convert data types - using ACTUAL column names
    accounts_df["Account ID"] = pd.to_numeric(
        accounts_df["Account ID"], errors="coerce"
    )

    # Handle date fields that might exist
    date_columns = ["Account Created Date/Time", "Account Last Modified Date/Time"]

    for col in date_columns:
        if col in accounts_df.columns:
            accounts_df[col] = pd.to_datetime(accounts_df[col], errors="coerce")
            print(f"✅ Found and converted date column: {col}")
        else:
            print(f"⚠️  Date column not found: {col}")

    # Handle donation amount fields - check what actually exists
    current_year = datetime.now().year
    donation_amount_fields = [
        f"{current_year} Donation Amount",
        f"{current_year-1} Donation Amount",
        "Total Donation Amount",
        "2024 Donation Amount",  # Hardcoded recent years as fallback
        "2023 Donation Amount",
    ]

    donation_count_fields = [
        f"{current_year} Donation Count",
        f"{current_year-1} Donation Count",
        "Total Number of Donations",
        "2024 Donation Count",
        "2023 Donation Count",
    ]

    # Find the best donation amount field
    donation_amount_col = None
    for field in donation_amount_fields:
        if field in accounts_df.columns:
            donation_amount_col = field
            accounts_df["lifetime_donation_amount"] = pd.to_numeric(
                accounts_df[field], errors="coerce"
            )
            print(f"✅ Using donation amount field: {field}")
            break

    if donation_amount_col is None:
        print("⚠️  No donation amount field found, using zeros")
        accounts_df["lifetime_donation_amount"] = 0

    # Find the best donation count field
    donation_count_col = None
    for field in donation_count_fields:
        if field in accounts_df.columns:
            donation_count_col = field
            accounts_df["donation_count"] = pd.to_numeric(
                accounts_df[field], errors="coerce"
            )
            print(f"✅ Using donation count field: {field}")
            break

    if donation_count_col is None:
        print("⚠️  No donation count field found, using zeros")
        accounts_df["donation_count"] = 0

    # Target variable: Is this account a donor?
    accounts_df["is_donor"] = (
        (accounts_df["donation_count"].fillna(0) > 0)
        | (accounts_df["lifetime_donation_amount"].fillna(0) > 0)
    ).astype(int)

    # Major donor classification ($1000+ lifetime giving)
    accounts_df["is_major_donor"] = (
        accounts_df["lifetime_donation_amount"].fillna(0) >= 1000
    ).astype(int)

    print(
        f"✅ Identified {accounts_df['is_donor'].sum():,} donors out of {len(accounts_df):,} accounts ({accounts_df['is_donor'].mean()*100:.1f}%)"
    )
    print(
        f"✅ Identified {accounts_df['is_major_donor'].sum():,} major donors ({accounts_df['is_major_donor'].mean()*100:.1f}%)"
    )

    # === DEMOGRAPHIC FEATURES ===

    # Account type
    accounts_df["is_individual"] = (accounts_df["Account Type"] == "Individual").astype(
        int
    )
    accounts_df["is_company"] = (accounts_df["Account Type"] == "Company").astype(int)
    accounts_df["is_household"] = (accounts_df["Account Type"] == "Household").astype(
        int
    )

    # Geographic features
    accounts_df["has_address"] = (~accounts_df["City"].isna()).astype(int)

    # Check for postal code field
    postal_code_col = None
    for col in ["Full Zip Code (F)", "Zip Code", "Postal Code"]:
        if col in accounts_df.columns:
            postal_code_col = col
            accounts_df["has_postal_code"] = (~accounts_df[col].isna()).astype(int)
            print(f"✅ Using postal code field: {col}")
            break

    if postal_code_col is None:
        print("⚠️  No postal code field found")
        accounts_df["has_postal_code"] = 0

    # Contact completeness
    accounts_df["has_email"] = (~accounts_df["Email 1"].isna()).astype(int)

    # Check for phone field
    phone_col = None
    for col in ["Phone 1 Full Number (F)", "Phone 1 Number", "Phone 1"]:
        if col in accounts_df.columns:
            phone_col = col
            accounts_df["has_phone"] = (~accounts_df[col].isna()).astype(int)
            print(f"✅ Using phone field: {col}")
            break

    if phone_col is None:
        print("⚠️  No phone field found")
        accounts_df["has_phone"] = 0

    accounts_df["contact_completeness"] = (
        accounts_df["has_email"] + accounts_df["has_phone"] + accounts_df["has_address"]
    ) / 3

    # Account age (relationship duration)
    if "Account Created Date/Time" in accounts_df.columns:
        accounts_df["account_age_days"] = (
            datetime.now() - accounts_df["Account Created Date/Time"]
        ).dt.days
        accounts_df["account_age_years"] = accounts_df["account_age_days"] / 365.25
        print("✅ Calculated account age from creation date")
    else:
        print("⚠️  No account creation date found")
        accounts_df["account_age_days"] = 365  # Default to 1 year
        accounts_df["account_age_years"] = 1

    # === ENGAGEMENT FEATURES ===

    # Activity recency
    if "Account Last Modified Date/Time" in accounts_df.columns:
        accounts_df["days_since_last_activity"] = (
            datetime.now() - accounts_df["Account Last Modified Date/Time"]
        ).dt.days
        accounts_df["has_recent_activity"] = (
            accounts_df["days_since_last_activity"] <= 180
        ).astype(int)
        print("✅ Calculated activity recency")
    else:
        print("⚠️  No last activity date found")
        accounts_df["days_since_last_activity"] = 365
        accounts_df["has_recent_activity"] = 0

    # Since we're skipping events/memberships/activities for now, set defaults
    print(
        "⚠️  Setting default values for engagement features (events, memberships, activities)"
    )
    accounts_df["events_attended"] = 0
    accounts_df["attends_events"] = 0
    accounts_df["has_active_membership"] = 0
    accounts_df["total_membership_fees"] = 0
    accounts_df["membership_count"] = 0
    accounts_df["volunteer_activities"] = 0
    accounts_df["total_volunteer_hours"] = 0
    accounts_df["is_volunteer"] = 0

    # === COMPOSITE ENGAGEMENT SCORE ===

    # Create overall engagement score (0-1) - simplified version
    engagement_components = [
        "contact_completeness",  # Contact info completeness
        "has_recent_activity",  # Recent activity
        # Skip other components for now since we don't have the data
    ]

    # Only use components that have variation
    valid_components = []
    for component in engagement_components:
        if component in accounts_df.columns and accounts_df[component].var() > 0:
            valid_components.append(component)

    if valid_components:
        accounts_df["engagement_score"] = accounts_df[valid_components].mean(axis=1)
    else:
        accounts_df["engagement_score"] = accounts_df["contact_completeness"]

    accounts_df["high_engagement"] = (accounts_df["engagement_score"] >= 0.6).astype(
        int
    )

    # === WEALTH INDICATORS ===

    # Company accounts may indicate higher capacity
    accounts_df["potential_high_capacity"] = (
        (accounts_df["is_company"] == 1) | (accounts_df["total_membership_fees"] > 500)
    ).astype(int)

    print(f"\n🎯 Feature engineering complete!")
    print(
        f"📊 Final dataset: {len(accounts_df):,} records with {len([c for c in accounts_df.columns if c not in ['Account ID', 'First Name', 'Last Name', 'Company Name']])} features"
    )
    print(f"   - Non-donors: {(~accounts_df['is_donor'].astype(bool)).sum():,}")
    print(f"   - Donors: {accounts_df['is_donor'].sum():,}")
    print(f"   - Major donors: {accounts_df['is_major_donor'].sum():,}")
    print(f"   - High engagement: {accounts_df['high_engagement'].sum():,}")

    # Show what fields we actually have
    print(f"\n📋 Available data fields:")
    for col in accounts_df.columns:
        if col not in [
            "First Name",
            "Last Name",
            "Company Name",
            "Email 1",
        ]:  # Skip PII
            non_null_count = accounts_df[col].count()
            print(f"   • {col}: {non_null_count:,} non-null values")

    return accounts_df


print("✅ CORRECTED FEATURE ENGINEERING FUNCTION READY")
print("📋 INSTRUCTIONS:")
print("1. Copy this function into your Jupyter notebook")
print("2. Replace the call: donor_features = engineer_donor_features(raw_data)")
print("3. With: donor_features = engineer_donor_features_corrected(raw_data)")
print("4. Run the cell to create features with correct field names")
