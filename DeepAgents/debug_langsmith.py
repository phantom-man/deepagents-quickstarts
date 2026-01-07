import os
from langsmith import Client
from dotenv import load_dotenv

load_dotenv("DeepAgents/.env")

print("🔍 Debugging LangSmith Connection...")
api_key = os.getenv("LANGCHAIN_API_KEY")
print(f"API Key present: {'Yes' if api_key else 'No'} ({api_key[:10]}...)")

try:
    client = Client()
    print("✅ Client initialized.")
    
    # Try to list projects to verify connection
    print("Attempting to list projects...")
    projects = list(client.list_projects(limit=5))
    print(f"✅ Successfully listed {len(projects)} projects.")
    for p in projects:
        print(f"   - {p.name} (ID: {p.id})")
        
except Exception as e:
    print(f"❌ LangSmith Error: {e}")
    if "workspace" in str(e).lower():
        print("\nPossible Solution: You need to set LANGSMITH_WORKSPACE_ID.")
