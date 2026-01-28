import json
import os

import replicate
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

try:
    print("Checking lucataco/xtts-v2...")
    model = replicate.models.get("lucataco/xtts-v2")
    print(f"FOUND: {model.owner}/{model.name}")
    print(f"  ID: {model.latest_version.id}")
    print(f"  Schema: {json.dumps(model.latest_version.openapi_schema, indent=2)}")
except Exception as e:
    print(f"Error: {e}")
