import json
import os

import replicate
from dotenv import load_dotenv

# Load Env
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

try:
    # Try exact match first
    print("Attempting to fetch minimax/music-1.5")
    try:
        # Note: Replicate models are usually owner/name
        model = replicate.models.get("minimax/music-1.5")
        print(f"FOUND: {model.name}")
        print("--- SCHEMA ---")
        # Print schemas to understand inputs
        version = model.latest_version
        print(
            json.dumps(
                version.openapi_schema["components"]["schemas"]["Input"], indent=2
            )
        )
    except Exception as e:
        print(f"Could not find music-1.5: {e}")

    print("\nAttempting to search/list minimax models...")
    # There isn't a clean search API in the client, but we can try to find 'minimax' in collection or just guess.

    # Let's try speech-01 just in case
    try:
        model = replicate.models.get("minimax/speech-01")
        print(f"FOUND: {model.name}")
    except:
        pass

except Exception as e:
    print(f"General Error: {e}")
