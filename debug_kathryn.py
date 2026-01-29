import os
from dotenv import load_dotenv
load_dotenv(override=True)

from lead_quality_system.services.google_maps import GooglePlacesVerifier

from lead_quality_system.scorer import LeadScorer
from lead_quality_system.models import Lead

lead = Lead(
    business_name="Kathryn Ivey Interiors",
    phone="+15718003084",
    zip_code="22314",
    email="info@kathrynivey.com"
)

print(f"--- Debugging: {lead.business_name} ---")

# Run full Scorer logic (which includes the new Name Guardrail)
result = LeadScorer.enrich_and_score(lead)

print("\n--- RESULT ---")
print(f"Score: {result.score}")
print(f"Verified Name: {result.verified_business_name}")
print("\n--- MATCH REASONS ---")
for r in result.match_reasons:
    print(f"- {r}")

print("\n--- SOURCES ---")
for s in result.sources:
    print(f"- {s}")
