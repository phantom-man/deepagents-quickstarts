import os
import sys

from dotenv import load_dotenv
from langsmith import Client

# Load environment variables from .env
env_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(env_path)

api_key = os.getenv("LANGCHAIN_API_KEY")
print(f"Testing API Key: {api_key[:10]}...{api_key[-4:] if api_key else 'None'}")

if not api_key:
    print("❌ Error: LANGCHAIN_API_KEY not found in .env")
    sys.exit(1)

try:
    client = Client()
    # 1. Test Read (Projects)
    print("Testing READ access...")
    projects = list(client.list_projects(limit=1))
    print("✅ READ Success! Found projects.")

    # 2. Test Write/Hub Access (Push Prompt)
    # This triggers the /settings call that failed earlier
    print("Testing WRITE/HUB access (Mock Push)...")
    from langchain_core.prompts import ChatPromptTemplate

    prompt = ChatPromptTemplate.from_messages([("system", "test")])
    repo = "test-key-verification"
    handle = os.getenv("LANGCHAIN_HUB_HANDLE")
    if handle:
        repo = f"{handle}/{repo}"

    import inspect

    print("Inspecting Client.create_prompt signature:")
    try:
        sig = inspect.signature(client.create_prompt)
        print(sig)
    except Exception as e:
        print(f"Could not inspect: {e}")

    # TEST: Check internal tenant info if possible
    print("Checking Tenant ID...")
    try:
        tid = client._get_tenant_id()
        print(f"Tenant ID: {tid}")

        # TEST 4: Push director-system-prompt with NO handle
        # But wait, we need to unset the handle if it's set in env for this test to be pure
        if handle:
            print(f"Note: LANGCHAIN_HUB_HANDLE is set to {handle}")

        print("Testing WRITE 'director-system-prompt' (Implicit/Simple)...")
        try:
            url = client.push_prompt("director-system-prompt", object=prompt)
            print(f"✅ HUB WRITE Success! {url}")
        except Exception as push_err:
            print(f"❌ WRITE FAILED: {push_err}")

    except Exception as e:
        print(f"Failed to get tenant ID: {e}")

    print("Done.")

except Exception as e:
    print("❌ Authentication/Hub Access Failed.")
    print(f"Error details: {e}")
    sys.exit(1)
