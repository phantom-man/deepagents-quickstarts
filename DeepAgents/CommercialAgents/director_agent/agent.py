import os
import sys
from dotenv import load_dotenv
# from langchain_anthropic import ChatAnthropic
# from langchain_google_vertexai import ChatVertexAI
from langchain_google_genai import ChatGoogleGenerativeAI
from deepagents import create_deep_agent

# Add parent directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

from DeepAgents.CommercialAgents.director_agent.prompts import DIRECTOR_INSTRUCTIONS

# Load environment variables
env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.env"))
load_dotenv(env_path)

def create_director_agent():
    """Creates and returns the Director Agent (Veo Fast Specialist)."""
    
    # Initialize the model 
    # Switching to 'gemini-3-pro-preview' with High Thinking as requested
    model = ChatGoogleGenerativeAI(
        model="gemini-3-pro-preview",
        temperature=0.7,
        model_kwargs={"thinking_mode": "high"} # Enabling high reasoning level
    )
    
    # Create the Deep Agent
    agent = create_deep_agent(
        model=model,
        tools=[], # No external tools needed for pure creative direction
        system_prompt=DIRECTOR_INSTRUCTIONS,
    )
    
    return agent

if __name__ == "__main__":
    print("Initializing Director Agent (Veo Fast Specialist)...")
    agent = create_director_agent()
    
    if len(sys.argv) > 1:
        concept = sys.argv[1]
        print(f"Directing commercial for concept: {concept}")
        
        config = {"configurable": {"thread_id": "director_session_1"}}
        for event in agent.stream(
            {"messages": [("user", f"Create a Veo Fast shot list for this commercial concept: {concept}")]}, 
            config=config
        ):
            pass # Output is handled by the stream
    else:
        print("Please provide a commercial concept as an argument.")
