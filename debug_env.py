import os
from dotenv import load_dotenv

# Force reload
load_dotenv(override=True)

print(f"CWD: {os.getcwd()}")
print(f"Content of .env exists: {os.path.exists('.env')}")

yelp_key = os.getenv("YELP_API_KEY")
google_key = os.getenv("GOOGLE_PLACES_API_KEY")

print(f"Yelp Key Found: {'Yes' if yelp_key else 'No'}")
if yelp_key:
    print(f"Yelp Key Length: {len(yelp_key)}")
    print(f"Yelp Key Preview: {yelp_key[:5]}...")

print(f"Google Key Found: {'Yes' if google_key else 'No'}")
