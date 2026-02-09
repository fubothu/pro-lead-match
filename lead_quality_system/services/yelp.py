import time
import threading
from collections import deque
from typing import Optional, Callable

import requests
import logging
from ..config import Config

logger = logging.getLogger(__name__)

# Yelp free/trial: low daily limit (e.g. 300/day Starter) + QPS limit (exact not published).
# Throttle to 2 requests per second to avoid TOO_MANY_REQUESTS_PER_SECOND (429).
YELP_MAX_REQUESTS_PER_SEC = 2
YELP_RATE_WINDOW_SEC = 1.0
_yelp_request_times: deque = deque()
_yelp_rate_lock = threading.Lock()


def _wait_for_yelp_rate_limit() -> None:
    """Block until we are under the QPS limit; thread-safe."""
    while True:
        with _yelp_rate_lock:
            now = time.monotonic()
            while _yelp_request_times and _yelp_request_times[0] < now - YELP_RATE_WINDOW_SEC:
                _yelp_request_times.popleft()
            if len(_yelp_request_times) < YELP_MAX_REQUESTS_PER_SEC:
                _yelp_request_times.append(now)
                return
            sleep_until = _yelp_request_times[0] + YELP_RATE_WINDOW_SEC - now
        time.sleep(max(0.05, sleep_until))


# Retry on 429 (rate limit)
YELP_MAX_RETRIES = 3
YELP_RETRY_BACKOFF_BASE_SEC = 1.0


class YelpMatcher:
    BASE_URL = "https://api.yelp.com/v3/businesses/search"
    PHONE_SEARCH_URL = "https://api.yelp.com/v3/businesses/search/phone"

    @staticmethod
    def _headers():
        return {
            "Authorization": f"Bearer {Config.YELP_API_KEY}"
        }

    @classmethod
    def search_by_phone(cls, phone: str, error_callback: Optional[Callable[[str, int], None]] = None):
        if Config.MOCK_MODE:
            return {"name": "Mock Yelp Business", "rating": 4.0, "review_count": 50}

        if not Config.YELP_API_KEY:
            return None
        if not phone or str(phone).strip().lower() == "nan":
            return None
        raw_digits = "".join(filter(str.isdigit, phone))
        if not raw_digits:
            return None
        if len(raw_digits) == 10:
            formatted_phone = f"+1{raw_digits}"
        elif len(raw_digits) == 11 and raw_digits.startswith("1"):
            formatted_phone = f"+{raw_digits}"
        else:
            formatted_phone = f"+{raw_digits}"
        params = {"phone": formatted_phone}
        last_error = None
        for attempt in range(YELP_MAX_RETRIES):
            _wait_for_yelp_rate_limit()
            try:
                resp = requests.get(cls.PHONE_SEARCH_URL, headers=cls._headers(), params=params)
                if resp.status_code == 429:
                    raise requests.RequestException(f"429 Rate Limited")
                resp.raise_for_status()
                data = resp.json()
                if "businesses" in data and data["businesses"]:
                    return data["businesses"][0]
                return None
            except requests.HTTPError as e:
                status = e.response.status_code
                if status in (400, 429, 401) and error_callback:
                    error_callback("yelp", status)
                if status == 400:
                    return None
                if status == 401:
                    logger.error(
                        "Yelp API 401 Unauthorized. Check YELP_API_KEY in .env: "
                        "use a valid API key from https://www.yelp.com/developers/v3/manage_app (no spaces/newlines)."
                    )
                    return None
                last_error = e
                if status == 429 and attempt < YELP_MAX_RETRIES - 1:
                    sleep_sec = YELP_RETRY_BACKOFF_BASE_SEC * (2 ** attempt)
                    logger.warning(f"Yelp Phone Search 429, retrying in {sleep_sec}s (attempt {attempt + 1}/{YELP_MAX_RETRIES})")
                    time.sleep(sleep_sec)
                else:
                    logger.error(f"Yelp Phone Search Error: {e}")
                    return None
            except requests.RequestException as e:
                last_error = e
                if attempt < YELP_MAX_RETRIES - 1:
                    sleep_sec = YELP_RETRY_BACKOFF_BASE_SEC * (2 ** attempt)
                    logger.warning(f"Yelp Phone Search failed: {e}. Retrying in {sleep_sec}s...")
                    time.sleep(sleep_sec)
                else:
                    logger.error(f"Yelp Phone Search Error: {e}")
                    return None
        return None

    @classmethod
    def search_by_term(cls, business_name: str, location: str, error_callback: Optional[Callable[[str, int], None]] = None):
        if Config.MOCK_MODE:
            return {"name": business_name, "rating": 3.5, "review_count": 20}

        if not Config.YELP_API_KEY:
            return None
        if not location or str(location).strip().lower() == "nan":
            return None

        params = {
            "term": business_name,
            "location": location,
            "limit": 1
        }
        last_error = None
        for attempt in range(YELP_MAX_RETRIES):
            _wait_for_yelp_rate_limit()
            try:
                resp = requests.get(cls.BASE_URL, headers=cls._headers(), params=params)
                if resp.status_code == 429:
                    raise requests.RequestException(f"429 Rate Limited")
                resp.raise_for_status()
                data = resp.json()
                if "businesses" in data and data["businesses"]:
                    return data["businesses"][0]
                return None
            except requests.HTTPError as e:
                status = e.response.status_code
                if status in (400, 429, 401) and error_callback:
                    error_callback("yelp", status)
                if status == 400:
                    return None
                if status == 401:
                    logger.error(
                        "Yelp API 401 Unauthorized. Check YELP_API_KEY in .env: "
                        "use a valid API key from https://www.yelp.com/developers/v3/manage_app (no spaces/newlines)."
                    )
                    return None
                last_error = e
                if status == 429 and attempt < YELP_MAX_RETRIES - 1:
                    sleep_sec = YELP_RETRY_BACKOFF_BASE_SEC * (2 ** attempt)
                    logger.warning(f"Yelp Term Search 429, retrying in {sleep_sec}s (attempt {attempt + 1}/{YELP_MAX_RETRIES})")
                    time.sleep(sleep_sec)
                else:
                    logger.error(f"Yelp Term Search Error: {e}")
                    return None
            except requests.RequestException as e:
                last_error = e
                if attempt < YELP_MAX_RETRIES - 1:
                    sleep_sec = YELP_RETRY_BACKOFF_BASE_SEC * (2 ** attempt)
                    logger.warning(f"Yelp Term Search failed: {e}. Retrying in {sleep_sec}s...")
                    time.sleep(sleep_sec)
                else:
                    logger.error(f"Yelp Term Search Error: {e}")
                    return None
        return None
