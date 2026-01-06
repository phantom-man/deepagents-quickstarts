import os
import sys
from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic
from deepagents import create_deep_agent

# Add the parent directory to sys.path to allow importing from sibling modules if needed
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

# Load environment variables
env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.env"))
load_dotenv(env_path)

from DeepAgents.CommercialAgents.research_agent.prompts import RESEARCHER_INSTRUCTIONS
from DeepAgents.CommercialAgents.research_agent.tools import tavily_search, scrape_webpage

def create_research_agent():
    """Creates and returns the Commercial Research Agent."""
    
    # Initialize the model
    # Switching to Anthropic Sonnet 3.5
    model = ChatAnthropic(
        model="claude-3-5-sonnet-20241022",
        temperature=0.0
    )
    
    # Create the Deep Agent
    agent = create_deep_agent(
        model=model,
        tools=[tavily_search, scrape_webpage],
        system_prompt=RESEARCHER_INSTRUCTIONS,
    )
    
    return agent

if __name__ == "__main__":
    print("Initializing Research Agent...")
    agent = create_research_agent()
    
    # Example usage if run directly
    if len(sys.argv) > 1:
        user_input = sys.argv[1]
        print(f"Starting research on: {user_input}")
        
        # Run the agent
        config = {"configurable": {"thread_id": "research_session_1"}}
        for event in agent.stream(
            {"messages": [("user", f"Research this topic: {user_input}")]}, 
            config=config
        ):
            pass # The agent prints output via middleware usually, or we can print events
            # For simple CLI usage, we rely on the agent's internal printing or middleware
    else:
        print("Please provide a topic, product, or question as an argument.")
