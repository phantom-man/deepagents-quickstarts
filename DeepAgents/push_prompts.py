"""
Script to PUSH local system prompts to LangSmith Hub.
This ensures the Hub is the source of truth for prompts, or at least mirrors the code.
"""
import os
import sys
from dotenv import load_dotenv
from langsmith import Client
from langchain_core.prompts import ChatPromptTemplate

# Add Repo Root to Path to allow imports
root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if root_path not in sys.path:
    sys.path.insert(0, root_path)

# Remove script directory from sys.path to avoid conflict with DeepAgents.py in the same folder
try:
    sys.path.remove(os.path.dirname(os.path.abspath(__file__)))
except ValueError:
    pass

# Load Env
load_dotenv(os.path.abspath(os.path.join(os.path.dirname(__file__), ".env")))

# Initialize Client
client = Client()

# Import Prompts (This executes the local construction logic)
try:
    from DeepAgents.CommercialAgents.director_agent.prompts import DEFAULT_DIRECTOR_INSTRUCTIONS
    from DeepAgents.CommercialAgents.research_agent.prompts import RESEARCHER_INSTRUCTIONS
    from DeepAgents.CommercialAgents.confidence_agent.prompts import CONFIDENCE_INSTRUCTIONS
    from DeepAgents.CommercialAgents.composer_agent.prompts import DEFAULT_COMPOSER_INSTRUCTIONS
    from DeepAgents.CommercialAgents.cinematographer_agent.prompts import DEFAULT_CINEMATOGRAPHER_INSTRUCTIONS
except ImportError as e:
    print(f"Import Error: {e}")
    sys.exit(1)

def push_system_prompt(handle: str, content: str):
    """Pushes a system prompt string as a ChatPromptTemplate."""
    print(f"Pushing {handle}...")
    
    # Create a simple generic chat template: System Message + User Input placeholder
    # This matches the typical agent flow (System Instruction + Conversation)
    prompt = ChatPromptTemplate.from_messages([
        ("system", content),
        ("placeholder", "{messages}") 
    ])
    
    # Push to Hub
    try:
        # Use LangSmith Client directly
        # Note: The ID should probably be 'deepagents/director-main'
        url = client.push_prompt(handle, object=prompt)
        print(f"✅ Successfully pushed {handle} to {url}")
    except Exception as e:
        # Handle "Nothing to commit" (409) as a success state
        if "409" in str(e) and "Nothing to commit" in str(e):
            print(f"OK: {handle} is up to date.")
        else:
            print(f"Failed to push {handle}: {e}")

if __name__ == "__main__":
    print("--- Pushing DeepAgents Prompts to LangSmith Hub ---")
    
    # 1. Director Agent
    # Note: Using simple names, hub should append owner handle if authenticated
    push_system_prompt("director-system-prompt", DEFAULT_DIRECTOR_INSTRUCTIONS)
    
    # 2. Research Agent
    push_system_prompt("researcher-system-prompt", RESEARCHER_INSTRUCTIONS)
    
    # 3. Confidence Agent
    push_system_prompt("confidence-system-prompt", CONFIDENCE_INSTRUCTIONS)
    
    # 4. Composer Agent
    push_system_prompt("composer-system-prompt", DEFAULT_COMPOSER_INSTRUCTIONS)

    # 5. Cinematographer Agent
    push_system_prompt("cinematographer-system-prompt", DEFAULT_CINEMATOGRAPHER_INSTRUCTIONS)
