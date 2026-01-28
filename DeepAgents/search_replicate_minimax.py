import json
import os

import replicate
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

print("Searching for 'minimax' on Replicate...")

try:
    # Most recent Replicate Python client uses client.models.search()
    # Check if search exists
    if hasattr(replicate.models, "search"):
        results = replicate.models.search("minimax")
        for model in results:
            print(f"FOUND: {model.owner}/{model.name}")
            latest = model.latest_version
            if latest:
                print(f"  ID: {latest.id}")
                print(
                    f"  Schema: {json.dumps(latest.openapi_schema['components']['schemas']['Input'], indent=2) if 'components' in latest.openapi_schema else 'N/A'}"
                )
    else:
        # Fallback: Try specific known owners
        candidates = [
            "cjwbw/minimax-speech-01",
            "replicate/minimax",
            "minimax/speech-01",
        ]
        for c in candidates:
            try:
                m = replicate.models.get(c)
                print(f"FOUND: {m.owner}/{m.name}")
                print(
                    f"  Inputs: {json.dumps(m.latest_version.openapi_schema, indent=2)}"
                )
            except:
                pass

except Exception as e:
    print(f"Error during search: {e}")
