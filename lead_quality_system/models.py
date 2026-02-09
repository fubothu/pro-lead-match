from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class Lead:
    business_name: str
    phone: str
    zip_code: str
    email: str

@dataclass
class EnrichmentResult:
    score: int
    quality_tier: str  # "High", "Medium", "Low"
    verified_business_name: Optional[str] = None
    website: Optional[str] = None
    match_reasons: List[str] = field(default_factory=list)
    sources: List[str] = field(default_factory=list)
    raw_google: Optional[dict] = None  # Raw Google Places API response (single place)
    raw_yelp: Optional[dict] = None    # Raw Yelp API response (single business)
    api_errors: List[str] = field(default_factory=list)  # e.g. ["google_400", "yelp_429"]
    # "True" = API success and match accepted; "False" = API success, no/rejected match; "Failed" = API error
    google_validated: str = "False"
    yelp_validated: str = "False"
    # Similarity scores (we calculate them; not from API). See scorer: difflib.SequenceMatcher(lead business_name, API name).ratio()
    google_similarity: Optional[float] = None   # Set when we have Google name+zip match (vs place displayName)
    yelp_similarity: Optional[float] = None    # Set when we have Yelp term match (vs business name)
    google_similarity_matched_name: Optional[str] = None  # Google place displayName we compared to
    yelp_similarity_matched_name: Optional[str] = None   # Yelp business name we compared to
