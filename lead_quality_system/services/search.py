import requests
import logging
from urllib.parse import urlparse
from ..config import Config

logger = logging.getLogger(__name__)

class WebsiteFinder:
    BASE_URL = "https://www.googleapis.com/customsearch/v1"
    
    # Blocklist of directory sites to ignore when looking for "Official" websites
    DIRECTORY_DOMAINS = {
        "yelp.com", "facebook.com", "instagram.com", "linkedin.com", "angi.com", 
        "homeadvisor.com", "thumbtack.com", "bbb.org", "yellowpages.com", 
        "porch.com", "houzz.com", "mapquest.com", "superpages.com"
    }

    @classmethod
    def find_website(cls, business_name: str, city: str, zip_code: str) -> str:
        if Config.MOCK_MODE:
            safe_name = business_name.replace(" ", "").lower()
            return f"https://www.{safe_name}.com"

        if not Config.GOOGLE_SEARCH_API_KEY or not Config.GOOGLE_SEARCH_CX:
            return None

        # Logic: Search for the business and try to find a non-directory URL
        query = f"{business_name} {city} {zip_code}"
        params = {
            "key": Config.GOOGLE_SEARCH_API_KEY,
            "cx": Config.GOOGLE_SEARCH_CX,
            "q": query,
            "num": 3  # Check top 3 results
        }

        try:
            resp = requests.get(cls.BASE_URL, params=params)
            resp.raise_for_status()
            data = resp.json()
            
            if "items" not in data:
                return None

            for item in data["items"]:
                link = item.get("link")
                if cls._is_valid_candidate(link, business_name):
                    return link
                    
        except Exception as e:
            logger.error(f"Website Search Error: {e}")
        
        return None

    @classmethod
    def _is_valid_candidate(cls, url: str, business_name: str) -> bool:
        """
        Check if URL is likely the business website (not a directory).
        """
        try:
            domain = urlparse(url).netloc.lower()
            # 1. Remove 'www.'
            if domain.startswith("www."):
                domain = domain[4:]
            
            # 2. Check blocklist
            for blocked in cls.DIRECTORY_DOMAINS:
                if blocked in domain:
                    return False
            
            return True
        except:
            return False
