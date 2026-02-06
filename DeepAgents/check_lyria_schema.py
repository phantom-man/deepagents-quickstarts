import replicate
from dotenv import load_dotenv

load_dotenv(".env")

try:
    model = replicate.models.get("google/lyria-2")
    version = model.latest_version
    if version is not None:
        print("Version ID:", version.id)
        if version.openapi_schema:
            print(
                "Schema:",
                version.openapi_schema["components"]["schemas"]["Input"]["properties"].keys(),
            )
    else:
        print("No version available")
except Exception as e:
    print(f"Error: {e}")
