import os
from dotenv import load_dotenv
from langsmith import Client

# Force load the .env file in the same directory
env_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(env_path, override=True)

print("--- Verify Hub Clean (Pull Test) ---")
client = Client()

target = "verify-clean-simple"
print(f"Attempting Pull for '{target}'...")

try:
    prompt = client.pull_prompt(target)
    print("✅ Pull Success! Found prompt object.")
except Exception as e:
    print(f"❌ Pull Failed: {e}")
    # Print the full error structure if possible
    if hasattr(e, 'response'):
        print(f"Response Status: {e.response.status_code}")
        print(f"Response Text: {e.response.text}")

print("\nAttempting Pull for 'director-system-prompt' (Simple Name)...")
try:
    prompt = client.pull_prompt("director-system-prompt")
    print("✅ Pull Success for director-system-prompt!")
except Exception as e:
    print(f"❌ Pull Failed for director-system-prompt: {e}")
