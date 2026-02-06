import os
import sys

from dotenv import load_dotenv
from langsmith import Client

# Load environment variables from .env
env_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(env_path)

api_key = os.getenv("LANGCHAIN_API_KEY")
print(f"Testing API Key: {api_key[:10] if api_key else 'None'}...{api_key[-4:] if api_key else 'None'}")

if not api_key:
    sys.exit(1)

client = Client()
repo_name = "director-system-prompt"
uuid_handle = os.getenv("LANGCHAIN_HUB_HANDLE") or os.getenv("LANGSMITH_WORKSPACE_ID")
print(f"UUID Handle from Env: {uuid_handle}")

print("\n--- TEST 1: Pull without prefix ---")
try:
    obj = client.pull_prompt(repo_name)
    print(f"✅ Pull '{repo_name}' Success!")
    # Use standard attribute access instead of checking internals if possible, but for debugging we look at repr
    print(f"Object: {obj}")
except Exception as e:
    print(f"❌ Pull '{repo_name}' Failed: {e}")

if uuid_handle:
    print(f"\n--- TEST 2: Pull with UUID prefix ({uuid_handle}/{repo_name}) ---")
    try:
        full_repo = f"{uuid_handle}/{repo_name}"
        obj = client.pull_prompt(full_repo)
        print(f"✅ Pull '{full_repo}' Success!")
    except Exception as e:
        print(f"❌ Pull '{full_repo}' Failed: {e}")

print("\n--- TEST 3: Settings Access ---")
try:
    settings = client._get_settings()
    print("✅ Settings Access Success")
except Exception as e:
    print(f"❌ Settings Access Failed: {e}")
