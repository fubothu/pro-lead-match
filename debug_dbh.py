import os
from dotenv import load_dotenv
load_dotenv(override=True)

from lead_quality_system.services.google_maps import GooglePlacesVerifier
from lead_quality_system.services.yelp import YelpMatcher

lead_name = "DBH design studio"
lead_phone = "+12152379319"
lead_zip = "19477"

print(f"--- Debugging: {lead_name} ---")

# 1. Google Phone Search
print(f"\n1. Google Phone Search ({lead_phone})...")
g_phone = GooglePlacesVerifier.search_by_phone(lead_phone)
if g_phone:
    print(f"   ✅ FOUND: {g_phone.get('displayName', {}).get('text')}")
    print(f"      Website: {g_phone.get('websiteUri')}")
else:
    print("   ❌ NOT FOUND by Phone.")

# 2. Google Text Search
print(f"\n2. Google Text Search ('{lead_name} {lead_zip}')...")
g_text = GooglePlacesVerifier.search_by_text(f"{lead_name} {lead_zip}")
if g_text:
    print(f"   ✅ FOUND: {g_text.get('displayName', {}).get('text')}")
    print(f"      Address: {g_text.get('formattedAddress')}")
    print(f"      Website: {g_text.get('websiteUri')}")
else:
    print("   ❌ NOT FOUND by Text.")

# 3. Yelp Search
print(f"\n3. Yelp Phone Search...")
y_phone = YelpMatcher.search_by_phone(lead_phone)
if y_phone:
    print(f"   ✅ FOUND: {y_phone.get('name')}")
    print(f"      URL: {y_phone.get('url')}")
else:
    print("   ❌ NOT FOUND by Phone.")

# 4. Yelp Text Search
print(f"\n4. Yelp Name Search...")
y_text = YelpMatcher.search_by_term(lead_name, lead_zip)
if y_text:
    print(f"   ✅ FOUND: {y_text.get('name')}")
    print(f"      URL: {y_text.get('url')}")
else:
    print("   ❌ NOT FOUND by Name.")
