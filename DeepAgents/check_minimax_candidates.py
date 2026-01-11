import replicate
import json
import os
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

candidates = [
    "cjwbw/minimax-speech-01",
    "minimax/speech-01", 
    "minimax/text-to-speech",
    "replicate/minimax-speech"
]

print("Checking specific candidates...")
for c in candidates:
    try:
        print(f"Checking {c}...")
        m = replicate.models.get(c)
        print(f"FOUND: {m.owner}/{m.name}")
        print(f"  ID: {m.latest_version.id}")
        print(f"  Schema: {json.dumps(m.latest_version.openapi_schema, indent=2)}")
    except Exception as e:
        print(f"  Failed: {e}")
