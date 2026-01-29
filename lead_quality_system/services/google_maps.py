import requests
import logging
from ..config import Config

logger = logging.getLogger(__name__)

class GooglePlacesVerifier:
    BASE_URL = "https://places.googleapis.com/v1/places:searchText"

    @staticmethod
    def _headers():
        return {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": Config.GOOGLE_PLACES_API_KEY,
            "X-Goog-FieldMask": "places.displayName,places.formattedAddress,places.id,places.nationalPhoneNumber,places.rating,places.userRatingCount,places.websiteUri"
        }

    @classmethod
    def search_by_phone(cls, phone: str):
        """
        Attempt to find a business strictly by phone number.
        Uses a single standardized E.164 format with region biasing for efficiency.
        """
        if Config.MOCK_MODE:
            return {
                "displayName": {"text": "Mock Business Verification"},
                "formattedAddress": "123 Mock Lane, Test City, 90210",
                "nationalPhoneNumber": phone,
                "rating": 4.8,
                "userRatingCount": 150,
                "websiteUri": "https://mock-business.com"
            }

        if not Config.GOOGLE_PLACES_API_KEY:
             return None

        # Best Practice: Normalize to E.164 (e.g. +14155552671)
        # This is the single most accepted format for Text Search.
        raw_digits = "".join(filter(str.isdigit, phone))
        
        formatted_query = phone # Default fallthrough
        if len(raw_digits) == 10:
             formatted_query = f"+1{raw_digits}"
        elif len(raw_digits) == 11 and raw_digits.startswith("1"):
             formatted_query = f"+{raw_digits}"

        # API Request
        # We add 'regionCode': 'US' to hint that we are looking for US businesses
        # even if the phone format is ambiguous.
        payload = {
            "textQuery": formatted_query,
            "regionCode": "US"
        }
        
        try:
            resp = requests.post(cls.BASE_URL, headers=cls._headers(), json=payload)
            resp.raise_for_status()
            data = resp.json()
            if "places" in data and data["places"]:
                return data["places"][0] # Return best match
        except Exception as e:
            logger.error(f"Google Places Phone Search Error: {e}")
                
        return None

    @classmethod
    def search_by_text(cls, query: str):
        """
        Fallback search by Name + City/Zip.
        """
        if Config.MOCK_MODE:
            return {
                "displayName": {"text": "Mock Business Verification"},
                "formattedAddress": "123 Mock Lane, Test City, 90210",
                "nationalPhoneNumber": "(555) 123-4567",
                "rating": 4.5,
                "userRatingCount": 85,
                "websiteUri": "https://mock-fallback.com"
            }

        if not Config.GOOGLE_PLACES_API_KEY:
             return None

        payload = {"textQuery": query}
        try:
            resp = requests.post(cls.BASE_URL, headers=cls._headers(), json=payload)
            resp.raise_for_status()
            data = resp.json()
            if "places" in data and data["places"]:
                return data["places"][0]
        except Exception as e:
            logger.error(f"Google Places Text Search Error: {e}")
        return None
