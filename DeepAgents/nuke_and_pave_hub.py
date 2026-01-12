import os
import sys
import subprocess
from dotenv import load_dotenv
from langsmith import Client

# Load Env
env_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(env_path, override=True)

# Get Handle
handle = os.getenv("LANGCHAIN_HUB_HANDLE")
if not handle:
    print("Error: LANGCHAIN_HUB_HANDLE not set in .env")
    sys.exit(1)

# Clean quotes if present
handle = handle.strip('"').strip("'")

# Agent Repos to Nuke
repos = [
    "director-system-prompt",
    "researcher-system-prompt",
    "cinematographer-system-prompt",
    "composer-system-prompt",
    "confidence-system-prompt"
]

client = Client()

print(f"--- ☢️ NUKING PROMPTS FOR: {handle} ---")

for repo in repos:
    full_name = f"{handle}/{repo}"
    print(f"Targeting: {full_name}")
    try:
        # Delete the prompt repository
        client.delete_prompt(full_name)
        print(f"✅ DELETED: {full_name}")
    except Exception as e:
        error_msg = str(e)
        if "404" in error_msg or "not found" in error_msg.lower():
            print(f"⚠️ Not Found (Already deleted?): {full_name}")
        else:
            print(f"❌ Error deleting {full_name}: {e}")

print("\n--- 🏗️ PAVING (Re-Pushing Fresh Prompts) ---")
# Invoke the push script to recreate them
try:
    result = subprocess.run([sys.executable, "DeepAgents/push_prompts.py"], capture_output=True, text=True)
    print(result.stdout)
    if result.stderr:
        print("Standard Error Output:")
        print(result.stderr)
except Exception as e:
    print(f"Failed to run push script: {e}")
