import os
import requests
from dotenv import load_dotenv

load_dotenv("DeepAgents/.env")

api_key = os.getenv("LANGCHAIN_API_KEY")
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
