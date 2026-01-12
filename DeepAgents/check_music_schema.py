import replicate
import os
import json
from dotenv import load_dotenv

# Load Env
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

try:
    print("Attempting to fetch minimax/music-01")
    model = replicate.models.get("minimax/music-01")
    print(f"FOUND: {model.name}")
    print("--- SCHEMA ---")
    for version in model.versions.list()[:1]:
        print(json.dumps(version.openapi_schema, indent=2))

except Exception as e:
    print(f"General Error: {e}")
