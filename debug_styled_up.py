import os
from dotenv import load_dotenv
load_dotenv(override=True)

from lead_quality_system.services.google_maps import GooglePlacesVerifier
from lead_quality_system.services.yelp import YelpMatcher

lead_name = "Styled Up Interior Design"
lead_phone = "+19548955793"
lead_zip = "33317"

print(f"--- Debugging: {lead_name} ---")

# 1. Google Phone Search
print(f"\n1. Google Phone Search ({lead_phone})...")
g_phone = GooglePlacesVerifier.search_by_phone(lead_phone)
if g_phone:
    print(f"   ✅ FOUND: {g_phone.get('displayName', {}).get('text')}")
    print(f"      Address: {g_phone.get('formattedAddress')}")
    print(f"      Website: {g_phone.get('websiteUri')}")
else:
    print("   ❌ NOT FOUND by Phone.")

# 2. Google Text Search (Name + Zip)
print(f"\n2. Google Text Search ('{lead_name} {lead_zip}')...")
g_text = GooglePlacesVerifier.search_by_text(f"{lead_name} {lead_zip}")
if g_text:
    print(f"   ✅ FOUND: {g_text.get('displayName', {}).get('text')}")
    print(f"      Address: {g_text.get('formattedAddress')}")
    print(f"      Website: {g_text.get('websiteUri')}")
else:
    print("   ❌ NOT FOUND by Name + Zip.")

# 4. Google Phone Search Variations
phones = [
    "+19548955793",       # E.164
    "9548955793",         # Raw
    "(954) 895-5793",     # US Standard
    "954-895-5793",       # Hyphenated
    "1-954-895-5793"      # US Code
]

print("\n4. Google Phone Search Variations...")
for p in phones:
    print(f"   Query: '{p}'")
    g_phone = GooglePlacesVerifier.search_by_text(p) # Use text search for phone query
    if g_phone:
        print(f"   ✅ FOUND: {g_phone.get('displayName', {}).get('text')}")
# 5. Yelp Search
print(f"\n5. Yelp Search...")
y_phone = YelpMatcher.search_by_phone(lead_phone)
if y_phone:
    print(f"   ✅ FOUND (Phone): {y_phone.get('name')}")
else:
    print("   ❌ NOT FOUND by Phone.")

y_text = YelpMatcher.search_by_term(lead_name, lead_zip)
if y_text:
    print(f"   ✅ FOUND (Name): {y_text.get('name')}")
    print(f"      Matched URL: {y_text.get('url')}")
else:
    print("   ❌ NOT FOUND by Name.")
