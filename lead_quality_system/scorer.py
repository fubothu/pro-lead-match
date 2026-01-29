from .models import Lead, EnrichmentResult
from .services.google_maps import GooglePlacesVerifier
from .services.yelp import YelpMatcher
from .services.search import WebsiteFinder
import difflib

class LeadScorer:
    
    @staticmethod
    def _calculate_similarity(a: str, b: str) -> float:
        if not a or not b:
            return 0.0
        return difflib.SequenceMatcher(None, a.lower(), b.lower()).ratio()
    
    @classmethod
    def enrich_and_score(cls, lead: Lead) -> EnrichmentResult:
        score = 0
        match_reasons = []
        sources = []
        verified_name = None
        website = None

        # 1. Google Places Search
        google_place = GooglePlacesVerifier.search_by_phone(lead.phone)
        if google_place:
            score += 40
            match_reasons.append("Phone number matched Google Business Profile")
            sources.append("Google Maps (Phone)")
            verified_name = google_place.get('displayName', {}).get('text')
        else:
            # Fallback to Name + Zip
            query = f"{lead.business_name} {lead.zip_code}"
            google_place = GooglePlacesVerifier.search_by_text(query)
            if google_place:
                # GUARDRAIL: Verify Name Similarity (min 50% match)
                returned_name = google_place.get('displayName', {}).get('text', "")
                similarity = cls._calculate_similarity(lead.business_name, returned_name)
                
                if similarity >= 0.5:
                    score += 30
                    match_reasons.append(f"Business Name & Location matched Google Profile (Sim: {similarity:.2f})")
                    sources.append("Google Maps (Name)")
                    verified_name = verified_name or returned_name
                    if not website and google_place.get('websiteUri'):
                        website = google_place['websiteUri']
                else:
                    match_reasons.append(f"Rejected Google Match '{returned_name}' (Low Similarity: {similarity:.2f})")

        # 2. Yelp Search
        yelp_biz = YelpMatcher.search_by_phone(lead.phone)
        if yelp_biz:
            score += 20
            match_reasons.append("Phone number matched verified Yelp Business")
            sources.append("Yelp (Phone)")
        else:
            yelp_biz = YelpMatcher.search_by_term(lead.business_name, lead.zip_code)
            if yelp_biz:
                # GUARDRAIL: Verify Name Similarity
                returned_name = yelp_biz.get('name', "")
                similarity = cls._calculate_similarity(lead.business_name, returned_name)
                
                if similarity >= 0.5:
                    score += 10 # Confidence lower for fuzzy name match
                    match_reasons.append(f"Location matched Yelp Business (Sim: {similarity:.2f})")
                    sources.append("Yelp (Name)")
                    verified_name = verified_name or returned_name
                else:
                    match_reasons.append(f"Rejected Yelp Match '{returned_name}' (Low Similarity: {similarity:.2f})")

        # 3. Website Discovery (If not found yet)
        if not website:
            discovered_site = WebsiteFinder.find_website(lead.business_name, "", lead.zip_code)
            if discovered_site:
                website = discovered_site
                score += 20
                match_reasons.append("Official Website Discovered via Search")
                sources.append("Google Search")
        
        # Award points if website exists (from ANY source)
        if website:
             # Avoid double counting if we just awarded it above? 
             # Actually, simpler logic:
             # Just check if website exists at the end of discovery
             pass 

        # REFACTORING SCORING TO BE CLEANER:
        # We already added points for Google/Yelp matches.
        # Website points should be additive regardless of source.
        
        # Let's clean this up:
        # Note: Previous code added +20 ONLY if found via Search. 
        # We want +20 if found via Google/Yelp too.
        
        if website and "Official Website Discovered via Search" not in match_reasons:
             score += 20
             match_reasons.append("Website Verification (via Profile)")

        # 4. Email Check
        if lead.email:
            domain = lead.email.split('@')[-1].lower()
            if domain not in ['gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com', 'icloud.com', 'aol.com']:
                score += 10
                match_reasons.append("Business Email Domain Detected")

        # Cap score at 100
        score = min(score, 100)

        # Determine Tier
        if score >= 70:
            tier = "High"
        elif score >= 40:
            tier = "Medium"
        else:
            tier = "Low"

        return EnrichmentResult(
            score=score,
            quality_tier=tier,
            verified_business_name=verified_name,
            website=website,
            match_reasons=match_reasons,
            sources=list(set(sources)) # Unique list
        )
