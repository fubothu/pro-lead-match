import os
from dotenv import load_dotenv
load_dotenv(override=True)

from lead_quality_system.services.google_maps import GooglePlacesVerifier

# Original Failed Name: "Richmond Hill Design + Build"
# User Suggested Name: "Richmond Hill Design-Build"
names_to_test = [
    "Richmond Hill Design + Build",
    "Richmond Hill Design-Build",
    "Richmond Hill Design Build"
]
lead_zip = "23237"
lead_phone = "+18044003694"

print(f"--- Debugging: Richmond Hill ---")

# 1. Phone Search (Should be name-agnostic)
print(f"\n1. Google Phone Search ({lead_phone})...")
g_phone = GooglePlacesVerifier.search_by_phone(lead_phone)
if g_phone:
    print(f"   ✅ FOUND: {g_phone.get('displayName', {}).get('text')}")
    print(f"      Address: {g_phone.get('formattedAddress')}")
else:
    print("   ❌ NOT FOUND by Phone.")

# 2. Text Search Variations
print(f"\n2. Testing Name Variations (Name + Zip '{lead_zip}')...")
for name in names_to_test:
    query = f"{name} {lead_zip}"
    print(f"   Query: '{query}'")
    g_text = GooglePlacesVerifier.search_by_text(query)
    if g_text:
        print(f"      ✅ MATCH: {g_text.get('displayName', {}).get('text')}")
        print(f"         Web:   {g_text.get('websiteUri')}")
    else:
        print(f"      ❌ No Match")
