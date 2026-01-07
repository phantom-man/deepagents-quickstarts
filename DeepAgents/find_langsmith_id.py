import os
import requests
from dotenv import load_dotenv

load_dotenv("DeepAgents/.env")
api_key = os.getenv("LANGCHAIN_API_KEY")

headers = {"x-api-key": api_key}
print("🔍 Searching for LangSmith Workspaces associated with Org-Scoped Key...")

# Checking common endpoints
endpoints = [
    "https://api.smith.langchain.com/workspaces",
    "https://api.smith.langchain.com/tenants",
    "https://api.smith.langchain.com/orgs/current/workspaces"
]

found_id = None

for url in endpoints:
    try:
        resp = requests.get(url, headers=headers)
        if resp.status_code == 200:
            data = resp.json()
            # Depending on format (list of dicts)
            if isinstance(data, list) and len(data) > 0:
                print(f"✅ Found Workspaces at {url}")
                for w in data:
                    print(f"   - Name: {w.get('display_name') or w.get('name')} | ID: {w.get('id')}")
                    if not found_id: found_id = w.get('id')
            else:
                print(f"⚠️ {url} returned 200 but empty/unknown format: {str(data)[:100]}")
        else:
            print(f"❌ {url}: {resp.status_code}")
    except Exception as e:
        print(f"❌ {url}: {e}")

if found_id:
    print(f"\n✨ First Workspace ID found: {found_id}")
else:
    print("\n❌ Could not automatically discover Workspace ID. Please copy it from your LangSmith URL (e.g. app.langsmith.com/o/<org>/w/<this-guid>).")
