import sys
from lead_quality_system.models import Lead
from lead_quality_system.scorer import LeadScorer

def main():
    if len(sys.argv) < 4:
        print("Usage: python main.py <name> <phone> <zip> [email]")
        return

    name = sys.argv[1]
    phone = sys.argv[2]
    zip_code = sys.argv[3]
    email = sys.argv[4] if len(sys.argv) > 4 else ""

    print(f"Validating lead: {name}, {phone}, {zip_code}")
    
    lead = Lead(name, phone, zip_code, email)
    result = LeadScorer.enrich_and_score(lead)
    
    print("-" * 30)
    print(f"Score: {result.score} ({result.quality_tier})")
    print(f"Verified Name: {result.verified_business_name}")
    print(f"Website: {result.website}")
    print("Reasons:")
    for r in result.match_reasons:
        print(f"- {r}")

if __name__ == "__main__":
    main()
