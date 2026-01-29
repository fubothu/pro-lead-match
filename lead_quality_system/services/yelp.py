import requests
import logging
from ..config import Config

logger = logging.getLogger(__name__)

class YelpMatcher:
    BASE_URL = "https://api.yelp.com/v3/businesses/search"
    PHONE_SEARCH_URL = "https://api.yelp.com/v3/businesses/search/phone"

    @staticmethod
    def _headers():
        return {
            "Authorization": f"Bearer {Config.YELP_API_KEY}"
        }

    @classmethod
    def search_by_phone(cls, phone: str):
        if Config.MOCK_MODE:
            return {"name": "Mock Yelp Business", "rating": 4.0, "review_count": 50}

        if not Config.YELP_API_KEY:
            return None
        
        # Yelp expects +15555555555 format
        # Clean input
        raw_digits = "".join(filter(str.isdigit, phone))
        formatted_phone = phone # Fallback
        
        if len(raw_digits) == 10:
            formatted_phone = f"+1{raw_digits}"
        elif len(raw_digits) == 11 and raw_digits.startswith("1"):
            formatted_phone = f"+{raw_digits}"
            
        params = {"phone": formatted_phone}
        try:
            resp = requests.get(cls.PHONE_SEARCH_URL, headers=cls._headers(), params=params)
            resp.raise_for_status()
            data = resp.json()
            if "businesses" in data and data["businesses"]:
                return data["businesses"][0]
        except Exception as e:
            logger.error(f"Yelp Phone Search Error: {e}")
        return None

    @classmethod
    def search_by_term(cls, business_name: str, location: str):
        if Config.MOCK_MODE:
            return {"name": business_name, "rating": 3.5, "review_count": 20}

        if not Config.YELP_API_KEY:
             return None

        params = {
            "term": business_name,
            "location": location,
            "limit": 1
        }
        try:
            resp = requests.get(cls.BASE_URL, headers=cls._headers(), params=params)
            resp.raise_for_status()
            data = resp.json()
            if "businesses" in data and data["businesses"]:
                return data["businesses"][0]
        except Exception as e:
            logger.error(f"Yelp Term Search Error: {e}")
        return None
