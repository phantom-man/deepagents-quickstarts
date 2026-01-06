import os
import sys
from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic
from deepagents import create_deep_agent

# Add parent directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

from DeepAgents.CommercialAgents.confidence_agent.prompts import CONFIDENCE_INSTRUCTIONS

# Load environment variables
env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.env"))
load_dotenv(env_path)

def create_confidence_agent():
    """Creates and returns the Confidence Agent."""
    
    # Initialize the model
    model = ChatAnthropic(
        model="claude-3-5-sonnet-20241022", # Using reliable model
        temperature=0.0
    )
    
    # Create the Deep Agent
    # Note: This agent primarily needs file access to read findings and write briefs/feedback
    agent = create_deep_agent(
        model=model,
        tools=[], # Standard filesystem tools are added by default middleware
        system_prompt=CONFIDENCE_INSTRUCTIONS,
    )
    
    return agent

if __name__ == "__main__":
    print("Initializing Confidence Agent...")
    agent = create_confidence_agent()
    
    if len(sys.argv) > 1:
        findings_path = sys.argv[1]
        print(f"Evaluating findings in: {findings_path}")
        
        config = {"configurable": {"thread_id": "confidence_session_1"}}
        for event in agent.stream(
            {"messages": [("user", f"Evaluate the findings in this file: {findings_path}")]}, 
            config=config
        ):
            pass
    else:
        print("Please provide the path to raw_findings.md as an argument.")
