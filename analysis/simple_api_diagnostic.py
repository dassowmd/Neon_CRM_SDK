#!/usr/bin/env python3
"""
SIMPLE API DIAGNOSTIC - Test the most basic API calls
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

print("🔍 BASIC API DIAGNOSTICS")
print("=" * 40)

# Test 1: Simple account list with minimal parameters
print("\n1️⃣ TESTING: client.accounts.list(user_type='INDIVIDUAL', limit=5)")
try:
    accounts = list(client.accounts.list(user_type="INDIVIDUAL", limit=5))
    print(f"   ✅ SUCCESS: {len(accounts)} accounts retrieved")
    if accounts:
        print(f"   📋 Sample fields: {list(accounts[0].keys())[:10]}")
    else:
        print(f"   ⚠️  No accounts returned (but no error)")
except Exception as e:
    print(f"   ❌ ERROR: {e}")

# Test 2: Try COMPANY type
print("\n2️⃣ TESTING: client.accounts.list(user_type='COMPANY', limit=5)")
try:
    accounts = list(client.accounts.list(user_type="COMPANY", limit=5))
    print(f"   ✅ SUCCESS: {len(accounts)} accounts retrieved")
    if accounts:
        print(f"   📋 Sample fields: {list(accounts[0].keys())[:10]}")
    else:
        print(f"   ⚠️  No accounts returned (but no error)")
except Exception as e:
    print(f"   ❌ ERROR: {e}")

# Test 3: Try donation search with very simple criteria
print("\n3️⃣ TESTING: client.donations.search() with basic criteria")
try:
    donation_search = {
        "searchFields": [
            {"field": "Donation ID", "operator": "GREATER_THAN", "value": "0"}
        ]
    }
    donations = list(client.donations.search(donation_search, limit=3))
    print(f"   ✅ SUCCESS: {len(donations)} donations retrieved")
    if donations:
        print(f"   📋 Sample fields: {list(donations[0].keys())[:10]}")
    else:
        print(f"   ⚠️  No donations returned (but no error)")
except Exception as e:
    print(f"   ❌ ERROR: {e}")

# Test 4: Events list (this was working)
print("\n4️⃣ TESTING: client.events.list(limit=3)")
try:
    events = list(client.events.list(limit=3))
    print(f"   ✅ SUCCESS: {len(events)} events retrieved")
    if events:
        print(f"   📋 Sample fields: {list(events[0].keys())[:8]}")
except Exception as e:
    print(f"   ❌ ERROR: {e}")

print("\n🎯 DIAGNOSTIC COMPLETE!")
