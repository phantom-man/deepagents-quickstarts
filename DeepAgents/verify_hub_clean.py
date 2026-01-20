import os
from dotenv import load_dotenv
from langsmith import Client
from langchain_core.prompts import ChatPromptTemplate

# Force load the .env file in the same directory
env_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(env_path, override=True)

print("--- Verify Hub Clean ---")
api_key = os.getenv("LANGCHAIN_API_KEY")
ws_id = os.getenv("LANGSMITH_WORKSPACE_ID")
handle = os.getenv("LANGCHAIN_HUB_HANDLE")
print(f"Key: {api_key[:5]}...")
print(f"Workspace: {ws_id}")
print(f"Handle: {handle}")

client = Client()

prompt = ChatPromptTemplate.from_messages([("system", "Verification Test Prompt")])

# Test 1: Simple Name
print("\n--- Test 1: Simple Name ('verify-clean-simple') ---")
try:
    url = client.push_prompt("verify-clean-simple", object=prompt)
    print(f"✅ Simple Name Push Success: {url}")
except Exception as e:
    print(f"❌ Simple Name Push Failed: {e}")

# Test 2: FQDN
print(f"\n--- Test 2: FQDN ('{handle}/verify-clean-fqdn') ---")
if handle:
    fqdn = f"{handle}/verify-clean-fqdn"
    try:
        url = client.push_prompt(fqdn, object=prompt)
        print(f"✅ FQDN Push Success: {url}")
    except Exception as e:
        print(f"❌ FQDN Push Failed: {e}")
else:
    print("⚠️ Skipping Test 2 (No handle)")
