"""
Script to DELETE legacy *-main prompts from LangSmith Hub.
"""
import os
import sys
from dotenv import load_dotenv
from langsmith import Client

# Load Env
load_dotenv(os.path.abspath(os.path.join(os.path.dirname(__file__), ".env")))

client = Client()

LEGACY_REPOS = [
    "director-system-main",
    "researcher-system-main",
    "confidence-system-main",
    "composer-system-main",
    "cinematographer-system-main"
]

print("--- Cleaning up Legacy Prompts ---")
for repo in LEGACY_REPOS:
    print(f"Attempting to delete {repo}...")
    try:
        # Use delete_prompt to delete the repository
        client.delete_prompt(repo)
        print(f"✅ Deleted Repo {repo}")
            
    except Exception as e:
        print(f"⚠️ Could not delete {repo}: {e}")
