import os
import sys
from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic
from langchain_google_vertexai import ChatVertexAI
# from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.tools import tool
from deepagents import create_deep_agent

# Add parent directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

from DeepAgents.CommercialAgents.director_agent.prompts import DIRECTOR_INSTRUCTIONS
from DeepAgents.CommercialAgents.research_agent.agent import run_research_task

# Load environment variables
env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.env"))
load_dotenv(env_path)

@tool
def consult_research_agent(topic: str) -> str:
    """Consults the Research Agent to gather detailed information, facts, and context about a specific topic, product, or concept.
    Use this when you lack sufficient knowledge to direct a scene accurately.
    Returns a comprehensive report.
    """
    print(f"\n🎬 Director > 📞 Calling Research Agent about: {topic}")
    # We call the main entry point of the Research Agent
    # This will trigger the memory check, research, and memorization loop in that agent.
    # Pass context for LangSmith
    extra_config = {
        "tags": ["sub-agent-call", "agent:researcher"],
        "metadata": {"parent_agent": "Director", "trigger": "tool_call"}
    }
    result = run_research_task(topic, extra_config=extra_config)
    if result:
        return result
    return "Research Agent could not find significant information."

def create_director_agent(provider="Google", model_name="gemini-2.0-flash-exp"):
    """Creates and returns the Director Agent."""
    
    # Initialize LLM based on Provider
    if provider == "Anthropic":
        print(f"🎬 Initializing Anthropic Model: {model_name}")
        model = ChatAnthropic(
            model_name=model_name,
            temperature=0.7,
            timeout=None,
            stop=None,
            # api_key loaded from env
        )
    else:
        # Default to Google VertexAI
        print(f"🎬 Initializing Google VertexAI Model: {model_name}")
        model = ChatVertexAI(
            model=model_name,
            temperature=0.7,
            location="us-central1"
        )
    
    # Create the Deep Agent
    agent = create_deep_agent(
        model=model,
        tools=[consult_research_agent], # Equipped with Research capabilities
        system_prompt=DIRECTOR_INSTRUCTIONS,
    )
    
    return agent

if __name__ == "__main__":
    print("Initializing Director Agent...")
    # Default test runs with Google
    agent = create_director_agent("Google", "gemini-2.0-flash-exp")
    
    if len(sys.argv) > 1:
        concept = sys.argv[1]
        print(f"Directing commercial for concept: {concept}")
        
        config = {"configurable": {"thread_id": "director_session_1"}}
        print("   (Director is thinking...)")
        
        final_response = ""
        for event in agent.stream(
            {"messages": [("user", f"Create a short commercial concept: {concept}")]},
            config=config # type: ignore
        ):
            # Print tool calls
            for key in event:
                val = event[key]
                msgs = []
                
                # Robust extraction of messages
                if isinstance(val, dict) and "messages" in val:
                    msgs = val["messages"]
                    # Handle LangGraph Overwrite object if present
                    if hasattr(msgs, "value"):
                         msgs = msgs.value
                elif hasattr(val, "messages"):
                    msgs = getattr(val, "messages", [])
                
                if msgs and isinstance(msgs, list):
                    msg = msgs[-1]
                    if hasattr(msg, "tool_calls") and msg.tool_calls:
                         for tc in msg.tool_calls:
                             print(f"👉 Tool Call: {tc['name']} ({tc['args']})")
                    if hasattr(msg, "content") and msg.content:
                        final_response = msg.content

        print("\n🎬 --- DIRECTOR'S TREATMENT ---")
        print(final_response)
        print("------------------------------")
    else:
        print("Please provide a commercial concept as an argument.")
