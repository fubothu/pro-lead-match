import os
from dotenv import load_dotenv
load_dotenv(override=True)

from lead_quality_system.services.google_maps import GooglePlacesVerifier
from lead_quality_system.services.yelp import YelpMatcher

lead_name = "Julia Vikander Decoration"
lead_phone = "+13129338359"
lead_zip = "85745"

print(f"--- Debugging: {lead_name} ---")

# 1. Google Phone Search
print(f"\n1. Google Phone Search ({lead_phone})...")
g_phone = GooglePlacesVerifier.search_by_phone(lead_phone)
if g_phone:
    print(f"FOUND: {g_phone.get('displayName', {}).get('text')}")
    print(f"Website: {g_phone.get('websiteUri')}")
else:
    print("NOT FOUND by Phone.")

# 2. Google Text Search Variations
queries = [
    f"{lead_name} {lead_zip}",           # Original: Julia Vikander Decoration 85745
    f"{lead_name} Tucson",               # City Name
    f"{lead_name} Chicago",              # Phone Area Code Location
    "Julia Vikander Decoration",         # Name Only
    "Buckingham Interiors",              # Domain Name Trace
    "Buckingham Interiors 85745"
]

print("\n2. Google Text Search Variations...")
for q in queries:
    print(f"   Query: '{q}'")
    g_text = GooglePlacesVerifier.search_by_text(q)
    if g_text:
        print(f"   ✅ FOUND: {g_text.get('displayName', {}).get('text')}")
        print(f"      Address: {g_text.get('formattedAddress')}")
    else:
        print(f"   ❌ Not Found")

# 3. Yelp Search
print(f"\n3. Yelp Phone Search...")
y_phone = YelpMatcher.search_by_phone(lead_phone)
if y_phone:
    print(f"FOUND: {y_phone.get('name')}")
else:
    print("NOT FOUND by Phone.")
