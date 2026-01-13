
import os
import replicate
from dotenv import load_dotenv

load_dotenv(".env")

try:
    model = replicate.models.get("google/lyria-2")
    version = model.latest_version
    print("Version ID:", version.id)
    print("Schema:", version.openapi_schema['components']['schemas']['Input']['properties'].keys())
except Exception as e:
    print(f"Error: {e}")
