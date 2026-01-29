import os
from dotenv import load_dotenv

# Force reload environment variables to ensure we get the latest .env changes
load_dotenv(override=True)

# Debug prints for server log
print(f"Loading Config... CWD: {os.getcwd()}")
print(f"Checking for .env: {os.path.exists('.env')}")
key_debug = os.getenv("YELP_API_KEY")
print(f"Yelp Key Loaded: {'Yes' if key_debug else 'No'} (Len: {len(key_debug) if key_debug else 0})")

class Config:
    GOOGLE_PLACES_API_KEY = os.getenv("GOOGLE_PLACES_API_KEY")
    GOOGLE_SEARCH_API_KEY = os.getenv("GOOGLE_SEARCH_API_KEY")
    GOOGLE_SEARCH_CX = os.getenv("GOOGLE_SEARCH_CX")
    YELP_API_KEY = os.getenv("YELP_API_KEY")
    MOCK_MODE = os.getenv("MOCK_MODE", "false").lower() == "true"

    @classmethod
    def validate(cls):
        if cls.MOCK_MODE:
            print("Status: MOCK_MODE is enabled. API keys will be ignored.")
            return

        missing = []
        if not cls.GOOGLE_PLACES_API_KEY:
            missing.append("GOOGLE_PLACES_API_KEY")
        if not cls.YELP_API_KEY:
            missing.append("YELP_API_KEY")
        
        # Search keys are optional fallback
        if not cls.GOOGLE_SEARCH_API_KEY or not cls.GOOGLE_SEARCH_CX:
            print("Info: Google Search keys missing. Website Discovery fallback will be disabled.")

        if missing:
            print(f"Warning: Missing API keys: {', '.join(missing)}. System will run in degraded mode.")
