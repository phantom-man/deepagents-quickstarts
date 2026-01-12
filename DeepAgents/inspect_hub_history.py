import os
from dotenv import load_dotenv
from langsmith import Client

# Load environment variables
load_dotenv()

def list_prompt_history(repo_name):
    """Lists the commit history for a specific prompt repo."""
    try:
        api_key = os.getenv("LANGCHAIN_API_KEY")
        # We need to construct the handle: handle/repo
        # We'll assume the handle is retrieved or we search for the repo.
        
        client = Client(api_key=api_key)
        
        # We need the owner handle first. 
        # Usually it's in the LANGCHAIN_HUB_HANDLE env var or we get it from user info.
        user = client.read_current_user()
        handle = os.getenv("LANGCHAIN_HUB_HANDLE", user.handle)
        
        full_repo = f"{handle}/{repo_name}"
        print(f"--- History for {full_repo} ---")
        
        # Pull the prompt object to see metadata, but listing commits specifically 
        # might require the list_commits API if available.
        # The SDK documentation suggests we can iterate versions.
        
        # list_commits returns an iterator of Commit objects
        commits = client.list_commits(full_repo)
        
        count = 0
        for commit in commits:
            print(f"Commit: {commit.commit_hash} | Date: {commit.manifest.get('created_at', 'Unknown')} | Message: {commit.manifest.get('description', 'No description')}")
            count += 1
            if count > 5:
                print("... (truncating history)")
                break
                
        if count == 0:
            print("No commits found (or access denied).")

    except Exception as e:
        print(f"Error checking {repo_name}: {e}")

if __name__ == "__main__":
    agents = [
        "director-system-prompt",
        "cinematographer-system-prompt",
        "composer-system-prompt",
        "researcher-system-prompt",
        "confidence-system-prompt"
    ]
    
    for agent in agents:
        list_prompt_history(agent)
