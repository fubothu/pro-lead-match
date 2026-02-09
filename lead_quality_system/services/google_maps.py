import requests
import logging
import threading
import time
from collections import deque
from typing import Optional, Callable

from ..config import Config

logger = logging.getLogger(__name__)

# Google Places API rate limit: 600 requests per minute (sliding window)
GOOGLE_RATE_LIMIT_PER_MIN = 600
GOOGLE_RATE_WINDOW_SEC = 60.0
_google_request_times: deque = deque()
_google_rate_lock = threading.Lock()

# Retry config for failed API calls
GOOGLE_API_MAX_RETRIES = 3
GOOGLE_API_RETRY_BACKOFF_BASE_SEC = 1.0  # 1s, 2s, 4s


def _wait_for_google_rate_limit() -> None:
    """Block until we are under the 600/min limit; thread-safe."""
    while True:
        with _google_rate_lock:
            now = time.monotonic()
            while _google_request_times and _google_request_times[0] < now - GOOGLE_RATE_WINDOW_SEC:
                _google_request_times.popleft()
            if len(_google_request_times) < GOOGLE_RATE_LIMIT_PER_MIN:
                _google_request_times.append(now)
                return
            sleep_until = _google_request_times[0] + GOOGLE_RATE_WINDOW_SEC - now
        time.sleep(max(0.01, sleep_until))


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
    def search_by_phone(cls, phone: str, error_callback: Optional[Callable[[str, int], None]] = None):
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

        _wait_for_google_rate_limit()
        last_error = None
        for attempt in range(GOOGLE_API_MAX_RETRIES):
            try:
                resp = requests.post(cls.BASE_URL, headers=cls._headers(), json=payload)
                # Retry on rate limit (429) or server errors (5xx)
                if resp.status_code in (429,) or 500 <= resp.status_code < 600:
                    raise requests.RequestException(f"HTTP {resp.status_code}")
                resp.raise_for_status()
                data = resp.json()
                if "places" in data and data["places"]:
                    return data["places"][0]
                return None
            except requests.RequestException as e:
                last_error = e
                resp = getattr(e, "response", None)
                if resp is not None:
                    status = resp.status_code
                    if status in (400, 429) and error_callback:
                        error_callback("google", status)
                    if 400 <= status < 500 and status != 429:
                        logger.error(f"Google Places Phone Search Error: {e}")
                        return None
                if attempt < GOOGLE_API_MAX_RETRIES - 1:
                    sleep_sec = GOOGLE_API_RETRY_BACKOFF_BASE_SEC * (2 ** attempt)
                    logger.warning(f"Google Places Phone Search attempt {attempt + 1} failed: {e}. Retrying in {sleep_sec}s...")
                    time.sleep(sleep_sec)
                else:
                    logger.error(f"Google Places Phone Search Error (after {GOOGLE_API_MAX_RETRIES} attempts): {e}")
        return None

    @classmethod
    def search_by_text(cls, query: str, error_callback: Optional[Callable[[str, int], None]] = None):
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
        _wait_for_google_rate_limit()
        last_error = None
        for attempt in range(GOOGLE_API_MAX_RETRIES):
            try:
                resp = requests.post(cls.BASE_URL, headers=cls._headers(), json=payload)
                if resp.status_code in (429,) or 500 <= resp.status_code < 600:
                    raise requests.RequestException(f"HTTP {resp.status_code}")
                resp.raise_for_status()
                data = resp.json()
                if "places" in data and data["places"]:
                    return data["places"][0]
                return None
            except requests.RequestException as e:
                last_error = e
                resp = getattr(e, "response", None)
                if resp is not None:
                    status = resp.status_code
                    if status in (400, 429) and error_callback:
                        error_callback("google", status)
                    if 400 <= status < 500 and status != 429:
                        logger.error(f"Google Places Text Search Error: {e}")
                        return None
                if attempt < GOOGLE_API_MAX_RETRIES - 1:
                    sleep_sec = GOOGLE_API_RETRY_BACKOFF_BASE_SEC * (2 ** attempt)
                    logger.warning(f"Google Places Text Search attempt {attempt + 1} failed: {e}. Retrying in {sleep_sec}s...")
                    time.sleep(sleep_sec)
                else:
                    logger.error(f"Google Places Text Search Error (after {GOOGLE_API_MAX_RETRIES} attempts): {e}")
        return None
