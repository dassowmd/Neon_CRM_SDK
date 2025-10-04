#!/usr/bin/env python3
"""
TEST: Account search instead of list to get more fields
"""

import sys
import os

sys.path.append("../src")

from neon_crm import NeonClient

# Initialize client
client = NeonClient(
    org_id=os.getenv("NEON_ORG_ID"),
    api_key=os.getenv("NEON_API_KEY"),
    environment="production",
)

print("🔍 TESTING: Account search vs list for more fields")
print("=" * 50)

# Test 1: Account search with broad criteria (should return more fields)
print("\n1️⃣ TESTING: client.accounts.search() without outputFields")
try:
    account_search = {
        "searchFields": [
            {"field": "Account Type", "operator": "IN", "value": "Individual,Company"}
        ]
        # NO outputFields - should auto-discover and return all fields
    }

    accounts = list(client.accounts.search(account_search, limit=5))
    print(f"   ✅ SUCCESS: {len(accounts)} accounts retrieved")
    if accounts:
        print(f"   📋 Total fields: {len(accounts[0].keys())}")
        print(f"   📋 Sample fields: {list(accounts[0].keys())[:15]}...")

        # Look for donation-related fields
        donation_fields = [
            field
            for field in accounts[0].keys()
            if "donation" in field.lower() or "gift" in field.lower() or "2024" in field
        ]
        print(f"   💰 Donation-related fields: {donation_fields[:10]}")

    else:
        print("   ⚠️  No accounts returned (but no error)")
except Exception as e:
    print(f"   ❌ ERROR: {e}")

print("\n🎯 SEARCH TEST COMPLETE!")
