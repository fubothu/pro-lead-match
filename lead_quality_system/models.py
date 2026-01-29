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
