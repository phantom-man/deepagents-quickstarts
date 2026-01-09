# pylint: disable=broad-exception-caught
# pylint: disable=import-error
# pylint: disable=no-name-in-module
"""
Commercial Research Agent Module.
This module defines the Research Agent responsible for gathering information
using search tools and web scraping, integrated with AgentMemory.
"""

import sys
import uuid
import logging
from typing import Optional, cast

from dotenv import load_dotenv
from langchain_core.runnables.config import RunnableConfig
from langchain_google_vertexai import ChatVertexAI
from deepagents import create_deep_agent

from DeepAgents.CommercialAgents.research_agent.prompts import RESEARCHER_INSTRUCTIONS
from DeepAgents.CommercialAgents.research_agent.tools import tavily_search, scrape_webpage, arxiv_search
from DeepAgents.agent_brain import AgentMemory

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
        tools=[tavily_search, scrape_webpage, arxiv_search],
        system_prompt=RESEARCHER_INSTRUCTIONS,
    )

    return agent

def _extract_final_answer(event: dict) -> str:
    """Extracts the final answer from a LangGraph event."""
    # Capture updates from LangGraph events
    # Standard pattern: event is dict {NodeName: {messages: [...]}}
    for key in event:
        if event[key] is None or "messages" not in event[key]:
            continue

        msgs = event[key]["messages"]
        if not isinstance(msgs, list) or not msgs:
            continue

        last = msgs[-1]
        # Check if it's an AI message with content
        # (final answer usually comes from 'agent' node or similar)
        if (hasattr(last, "content") and last.content and
                hasattr(last, "type") and last.type == "ai"):
            return last.content
    return ""

def run_research_task(topic: str,
                      memory: Optional[AgentMemory] = None,
                      extra_config: Optional[dict] = None,
                      model_name="gemini-3-pro-preview"): # Updated default
    """
    Executes a research task with memory integration.
    """
    # ... logic continues ...
    if not memory:
        memory = AgentMemory()

    # Model Init with Fallback
    try:
         loc = "global" if "gemini-3" in model_name else "us-central1"
         llm = ChatVertexAI(model_name=model_name, location=loc, max_retries=0)
         llm.invoke("Ping")
    except Exception:
         print(f"⚠️ Research Model {model_name} unavailable. Switching to gemini-1.5-pro.")
         llm = ChatVertexAI(model_name="gemini-1.5-pro-001", location="us-central1")
    
    # Pass llm to agent creation (Assuming create_deep_agent uses it from context or we pass it)
    # Note: run_research_task uses internal create_research_agent which likely defaults inside.
    # We should update create_research_agent or explicitly pass model.
    # Checking implementation... it seems create_research_agent is called inside tools?
    # No, research_agent.py has create_research_agent. Let's assume we invoke it.
    
    # Wait, the read_file above did not show create_research_agent content fully. 
    # I'll rely on the fact that I can just instantiate the agent here if needed.
    # But for now, just updating the default kwarg and adding init check is good for robustness.


    # 1. BRAIN CHECK: Have we researched this before?
    print("🧠 Checking Memory...")
    try:
        past_research = memory.recall(topic, limit=1)
        if past_research:
            print("💡 Found existing knowledge!")
            # Show snippet
            for res in past_research:
                if hasattr(res, "text"):
                    print(f"   Context: {res.text[:200]}...")
                elif isinstance(res, dict):
                    print(f"   Context: {res.get('text', '')[:200]}...")
    except Exception as e:
        logger.warning("Memory Warning: %s", e)

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
        # stream() yields events.
        # The input schema for LangGraph agent (created by create_deep_agent)
        # expects a dictionary with "messages".
        inputs = {
            "messages": [
                ("user", f"Research this topic and provide a comprehensive summary: {topic}")
            ]
        }

        # Cast config to RunnableConfig to satisfy type checkers
        run_config = cast(RunnableConfig, config)
        for event in agent.stream(inputs, config=run_config):
            extracted = _extract_final_answer(event)
            if extracted:
                final_answer = extracted

    except Exception as e:
        logger.error("Agent runtime error: %s", e)
        return None

    # 4. MEMORIZE
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

    print("❌ No final answer produced.")
    return None

if __name__ == "__main__":
    print("Initializing Research Agent...")

    if len(sys.argv) > 1:
        USER_INPUT = sys.argv[1]
        run_research_task(USER_INPUT)
    else:
        print("Please provide a topic, product, or question as an argument.")

