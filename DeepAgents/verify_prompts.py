"""
Script to VERIFY that prompts can be successfully pulled from LangSmith Hub.
This ensures the 'Pull' side of the workflow is functional.
"""
import os
import sys
from dotenv import load_dotenv
from langsmith import Client

# Add Repo Root to Path
root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if root_path not in sys.path:
    sys.path.insert(0, root_path)

# Load Env
load_dotenv(os.path.abspath(os.path.join(os.path.dirname(__file__), ".env")))

def verify_pull(handle: str):
    """Attempts to pull a prompt and verify its content."""
    print(f"Testing Pull: [{handle}]...")
    try:
        client = Client()
        prompt_obj = client.pull_prompt(handle)
        
        # Check if it has content
        # Depending on type (ChatPromptTemplate), it might be prompt_obj.messages...
        if not prompt_obj:
            print(f"❌ Failed: object is empty.")
            return False
            
        print(f"✅ Success: Retrieved {type(prompt_obj).__name__}")
        return True
    except Exception as e:
        print(f"❌ Failed: {e}")
        return False

if __name__ == "__main__":
    print("--- Verifying DeepAgents LangSmith Prompts ---")
    
    handles = [
        "director-system-main",
        "researcher-system-main",
        "confidence-system-main",
        "composer-system-main",
        "cinematographer-system-main"
    ]
    
    results = []
    for h in handles:
        success = verify_pull(h)
        results.append(success)
    
    if all(results):
        print("\n🎉 ALL PROMPTS VERIFIED.")
        sys.exit(0)
    else:
        print("\n⚠️ SOME PROMPTS FAILED TO DOWNLOAD.")
        sys.exit(1)
