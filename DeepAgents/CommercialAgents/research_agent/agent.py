import os
import sys
import uuid
from dotenv import load_dotenv
# from langchain_anthropic import ChatAnthropic
from langchain_google_vertexai import ChatVertexAI
from deepagents import create_deep_agent

# Add the parent directory to sys.path to allow importing from sibling modules if needed
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

# Load environment variables
env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.env"))
load_dotenv(env_path)

from DeepAgents.CommercialAgents.research_agent.prompts import RESEARCHER_INSTRUCTIONS
from DeepAgents.CommercialAgents.research_agent.tools import tavily_search, scrape_webpage
from DeepAgents.agent_brain import AgentMemory

def create_research_agent(model_name="gemini-2.0-flash-exp"):
    """Creates and returns the Commercial Research Agent."""
    
    # Initialize the model
    # Switching to Vertex AI due to Auth issues with Anthropic
    model = ChatVertexAI(
        model=model_name,
        temperature=0.0
    )
    
    # Create the Deep Agent
    agent = create_deep_agent(
        model=model,
        tools=[tavily_search, scrape_webpage],
        system_prompt=RESEARCHER_INSTRUCTIONS,
    )
    
    return agent

def run_research_task(topic: str, memory: AgentMemory = None, extra_config: dict = None, model_name="gemini-2.0-flash-exp"):
    """Executes a research task with memory integration."""
    if not memory:
        memory = AgentMemory()

    print(f"\\n🔎 Research Agent Task: '{topic}'")
    
    # 1. BRAIN CHECK: Have we researched this before?
    print("🧠 Checking Memory...")
    try:
        past_research = memory.recall(topic, limit=1)
        if past_research:
            print(f"💡 Found existing knowledge!")        
            # Show snippet
            for res in past_research:
                if hasattr(res, "text"):
                     print(f"   Context: {res.text[:200]}...")
                elif isinstance(res, dict):
                     print(f"   Context: {res.get('text', '')[:200]}...")
    except Exception as e:
        print(f"⚠️ Memory Warning: {e}")

    # 2. CREATE AGENT
    agent = create_research_agent(model_name=model_name)
    
    # 3. RUN AGENT
    config = {"configurable": {"thread_id": f"research_{uuid.uuid4()}"}}
    if extra_config:
        config.update(extra_config)
    print("🚀 Starting Research Stream...")
    
    final_answer = ""
    
    # We need to iterate the stream to drive execution
    try:
        print("   (Agent thinking... output suppressed to keep terminal clean)")
        for event in agent.stream(
            {"messages": [("user", f"Research this topic and provide a comprehensive summary: {topic}")]}, 
            config=config
        ):
            # Capture updates from LangGraph events
            # Standard pattern: event is dict {NodeName: {messages: [...]}}
            for key in event:
                 if event[key] is not None and "messages" in event[key]:
                     msgs = event[key]["messages"]
                     if isinstance(msgs, list) and msgs:
                         last = msgs[-1]
                         # Check if it's an AI message with content (final answer usually comes from 'agent' node or similar)
                         if hasattr(last, "content") and last.content and hasattr(last, "type") and last.type == "ai":
                             final_answer = last.content
    except Exception as e:
        print(f"❌ Agent runtime error: {e}")
        return None
        
    # 4. CAPTURE RESULT (Capture loop logic above replaces get_state)
    pass
                
    # 5. MEMORIZE
    if final_answer:
        print("\n📝 --- FINAL REPORT ---")
        print(final_answer)
        print("-----------------------")
        print(f"\n🧠 Memorizing Findings ({len(final_answer)} chars)...")
        memory.memorize(
            f"Research on '{topic}': {final_answer}", 
            "ResearchAgent",
            tags=["research_report"]
        )
        print("✅ Findings stored in Long-Term Memory (LanceDB).")
        return final_answer
    else:
        print("❌ No final answer produced.")
        return None

if __name__ == "__main__":
    print("Initializing Research Agent...")
    
    if len(sys.argv) > 1:
        user_input = sys.argv[1]
        run_research_task(user_input)
    else:
        print("Please provide a topic, product, or question as an argument.")

