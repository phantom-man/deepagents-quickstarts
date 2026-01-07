import os
import requests
from dotenv import load_dotenv

# Robustly load .env from the script's directory
current_dir = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(current_dir, ".env")
load_dotenv(env_path)

api_key = os.getenv("LANGCHAIN_API_KEY")

if not api_key:
    print(f"❌ Error: LANGCHAIN_API_KEY not found in environment or at {env_path}")
    exit(1)
url = "https://api.smith.langchain.com/orgs/current/workspaces"  # Attempt to list workspaces for current org
# Alternatively tried /tenants or /workspaces

headers = {
    "x-api-key": api_key
}

print(f"Querying LangSmith API with Key: {api_key[:10]}...")

try:
    # First try listing workspaces for the organization
    response = requests.get("https://api.smith.langchain.com/workspaces", headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        print("✅ Success! Found Workspaces:")
        for w in data:
            print(f"   Name: {w.get('display_name', 'Unknown')} | ID: {w.get('id')} | Tenant Handle: {w.get('tenant_handle')}")
    else:
        print(f"❌ Request failed: {response.status_code} - {response.text}")
        
        # Try finding the organization itself if workspaces fails
        print("Trying /orgs/current...")
        resp2 = requests.get("https://api.smith.langchain.com/orgs/current", headers=headers)
        print(f"Org Status: {resp2.status_code} - {resp2.text}")

except Exception as e:
    print(f"❌ Error: {e}")
