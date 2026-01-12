
import os
import sys
from dotenv import load_dotenv
from langsmith import Client

# Force load the .env file
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"), override=True)

print("--- LangSmith Handle Discovery ---")
api_key = os.getenv("LANGCHAIN_API_KEY")
ws_id = os.getenv("LANGSMITH_WORKSPACE_ID")
print(f"Key: {api_key[:5]}... | Workspace: {ws_id}")

client = Client()

try:
    print("\n1. Querying List Repos (limit=1)...")
    repos = list(client.list_repos(limit=1))
    if repos:
        handle = repos[0].owner_handle
        print(f"✅ FOUND HANDLE: {handle}")
        print(f"   (From repo: {repos[0].repo_handle})")
    else:
        print("⚠️  No existing repos found. Creating a temporary one to discover handle...")
        # Try to push a dummy prompt to discover handle? 
        # Actually without a handle provided, push might fail like pull.
        # Let's try to get current user info.
        pass

except Exception as e:
    print(f"❌ List Repos Failed: {e}")

try:
    print("\n2. Querying Tenant Info...")
    # This is an internal method but often useful for debugging
    tid = client._get_tenant_id()
    print(f"   Tenant ID: {tid}")
except Exception as e:
    print(f"   Tenant check failed: {e}")
