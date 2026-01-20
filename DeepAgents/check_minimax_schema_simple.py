
import replicate
from dotenv import load_dotenv

load_dotenv(".env")

try:
    model = replicate.models.get("minimax/music-01")
    # Some models don't list versions publicly, try latest_version property
    version = model.latest_version
    if version:
        print("Version ID:", version.id)
        if 'openapi_schema' in dir(version):
             print("Schema Inputs:", version.openapi_schema['components']['schemas']['Input']['properties'].keys())
    else:
        print("No versions found.")
except Exception as e:
    print(f"Error: {e}")
