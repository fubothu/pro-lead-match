import os
from dotenv import load_dotenv

# Force reload env
load_dotenv(override=True)

from lead_quality_system.scorer import LeadScorer
from lead_quality_system.models import Lead

# Enable optional debug if I added it? 
# For now just run it and print result

lead = Lead(
    business_name="Rabbitt Design",
    phone="+19253007004",
    zip_code="94611",
    email="renerabbitt@gmail.com"
)

print(f"Validating lead: {lead}")
result = LeadScorer.enrich_and_score(lead)

print("\n--- RESULT ---")
print(f"Score: {result.score}")
print(f"Tier: {result.quality_tier}")
print(f"Verified Name: {result.verified_business_name}")
print("\n--- MATCH REASONS ---")
for r in result.match_reasons:
    print(f"- {r}")

print("\n--- SOURCES ---")
for s in result.sources:
    print(f"- {s}")
