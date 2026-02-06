import json
import os

import replicate
from dotenv import load_dotenv

# Load Env
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

try:
    print("Attempting to fetch minimax/music-01")
    model = replicate.models.get("minimax/music-01")
    print(f"FOUND: {model.name}")
    print("--- SCHEMA ---")
    versions = list(model.versions.list())
    for version in versions[:1]:
        if version.openapi_schema:
            print(json.dumps(version.openapi_schema, indent=2))

except Exception as e:
    print(f"General Error: {e}")
