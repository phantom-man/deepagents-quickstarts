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
from langchain_google_genai import ChatGoogleGenerativeAI
# from langchain_google_vertexai import ChatVertexAI # Deprecated
from langchain_anthropic import ChatAnthropic
import json
import os
from langsmith import traceable
from DeepAgents.agent_factory import create_deep_agent
from DeepAgents.hub_manager import get_or_push_prompt

from DeepAgents.CommercialAgents.research_agent.prompts import RESEARCHER_INSTRUCTIONS
from DeepAgents.CommercialAgents.research_agent.tools import (
    tavily_search, scrape_webpage, arxiv_search, submit_finding_for_review
)
from DeepAgents.agent_brain import AgentMemory

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_research_agent(model_name="gemini-2.0-flash-001", provider="Google"):
    """Creates and returns the Commercial Research Agent."""

    # Initialize the model
    model = None
    if provider == "Anthropic":
        model = ChatAnthropic(
            model_name=model_name,
            temperature=0.0
        ) 

    elif model_name.startswith("meta/") or "llama" in model_name.lower():
        # Replicate
        from DeepAgents.replicate_adapter import ChatReplicate
        model = ChatReplicate(
            model=model_name,
            model_kwargs={"temperature": 0.0, "max_length": 2048, "top_p": 1}
        )
    
    elif provider == "Google":
        # Google Vertex AI
        model = ChatGoogleGenerativeAI(
            model=model_name,
            vertexai=True,
            project=os.getenv("GOOGLE_CLOUD_PROJECT"),
            location="us-central1",
            temperature=0.0, # Research needs precision
            max_retries=1
        )
            
    else: 
        # Default / Legacy Fallback
        model = ChatGoogleGenerativeAI(
            model=model_name,
            vertexai=True,
            project=os.getenv("GOOGLE_CLOUD_PROJECT"),
            location="us-central1",
            temperature=0.0, 
            max_retries=1
        )

    # Create the Deep Agent
    # 🔗 HUB INTEGRATION: Prompt already pulled in prompts.py
    
    agent = create_deep_agent(
        model=model,
        tools=[tavily_search, scrape_webpage, arxiv_search, submit_finding_for_review],
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

@traceable(run_type="chain", name="Research Task")
def run_research_task(topic: str,
                      memory: Optional[AgentMemory] = None,
                      extra_config: Optional[dict] = None,
                      model_name=None,
                      provider=None): 
    """
    Executes a research task with memory integration.
    """
    # Load Config if not provided
    if not model_name or not provider:
        try:
            # Path relative to this file: ../../../data/agent_config.json
            config_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../data/agent_config.json"))
            if os.path.exists(config_path):
                with open(config_path, "r") as f:
                    config = json.load(f)
                    res_config = config.get("Researcher", {})
                    if not model_name: model_name = res_config.get("model", "gemini-2.0-flash-001")
                    if not provider: provider = res_config.get("provider", "Google")
            else:
                 logger.warning("Config file not found. Using defaults.")
        except Exception as e:
            logger.warning(f"Failed to load config: {e}. using defaults.")
    
    # Defaults if still None
    if not model_name: model_name = "gemini-2.0-flash-001"
    if not provider: provider = "Google"

    if not memory:
        memory = AgentMemory()

    # Model Init with Fallback
    agent = create_research_agent(model_name=model_name, provider=provider)
    
    # Run loop logic (simplified here for brevity)
    # Note: Previous implementation did manual LLM check. create_research_agent handles fallback internally now.
    
    # Original logic below adapted?
    # Actually, create_research_agent returns a CompiledGraph.
    # We invoke it.
    
    config = RunnableConfig(recursion_limit=30)
    
    # 1. BRAIN CHECK: Have we researched this before?
    print("🧠 Checking Memory...")
    context_injection = ""
    try:
        # A. Recall Facts
        past_research = memory.recall(topic, limit=2)
        if past_research:
            print("💡 Found existing knowledge!")
            # CACHE HIT LOGIC: If we found a substantial previous report, return it immediately to save time/cost.
            for res in past_research:
                txt = res.text if hasattr(res, "text") else res.get('text', '')
                # If it looks like a full report (heuristic: length > 1000 chars or has header)
                if len(txt) > 1000 or "<h1>" in txt or "# Final Report" in txt:
                    print("⚡ CACHE HIT: Returning existing research report.")
                    return f"<!-- RECOVERED FROM MEMORY -->\n{txt}"
                
                print(f"   Context: {txt[:200]}...")
                context_injection += f"- {txt}\n"
            
            if context_injection:
                context_injection = "\n\nEXISTING KNOWLEDGE (Do not repeat, but build upon):\n" + context_injection

        # B. Negative Reinforcement (Learn from Mistakes)
        # Search for rejected findings related to this topic
        mistakes = memory.recall(f"Mistake regarding {topic}", limit=2) # Naive search, but effective if embeddings aligned
        # Filter for tags or scan text content heuristic for now since recall is generic
        # Ideally, we query by tag="rejected_finding", but generic recall is purely semantic.
        # We rely on the fact that we prefixed rejected items with "[REJECTED MISTAKE]"
        header_added = False
        if mistakes:
            for m in mistakes:
                mtxt = m.text if hasattr(m, "text") else m.get('text', '')
                if "REJECTED" in mtxt or "Assumption" in mtxt or "Critique" in mtxt: # Heuristic
                    if not header_added:
                        context_injection += "\n\n⚠️ PREVIOUS MISTAKES (AVOID THESE):\n"
                        header_added = True
                    context_injection += f"- {mtxt[:300]}...\n"
                    print(f"   ⚠️ Warning Recall: {mtxt[:100]}...")

    except Exception as e:
        logger.warning("Memory Warning: %s", e)

    # 2. CREATE AGENT
    agent = create_research_agent(model_name=model_name, provider=provider)

    # 3. RUN AGENT
    config = {"configurable": {"thread_id": f"research_{uuid.uuid4()}"}}
    if extra_config:
        config.update(extra_config)
    print("🚀 Starting Research Stream...")

    final_answer = ""

    # We need to iterate the stream to drive execution
    try:
        print("   (Agent thinking... output suppressed to keep terminal clean)")
        
        # Inject memory into the user prompt
        user_prompt = f"Research this topic and provide a comprehensive summary: {topic}\n\nOUTPUT FORMAT: HTML. Use <h1>, <h2>, <p>, <ul> tags. Do NOT use Markdown (```html)."
        if context_injection:
            user_prompt += context_injection
            
        inputs = {
            "messages": [
                ("user", user_prompt)
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
        
        # SAVE TO CLOUD (AssetManager)
        try:
            from DeepAgents.asset_manager import AssetManager
            assets = AssetManager()
            
            # Formatting as HTML
            html_content = f"""
            <html>
            <head><title>Research: {topic[:30]}</title></head>
            <body>
            <h1>Research Report</h1>
            <h3>Topic: {topic}</h3>
            <hr>
            <div style='white-space: pre-wrap;'>
            {final_answer}
            </div>
            </body>
            </html>
            """
            
            saved_doc = assets.save_text_document(
                text=html_content,
                title=f"Research_{topic[:30]}",
                session_id="research_autonomous",
                extension="html"
            )
            cloud_url = saved_doc.get("cloud_url")
            if cloud_url and "http" in cloud_url:
                print(f"✅ Uploaded to Cloud: {cloud_url}")
                # Append link to final answer so downstream agents see it
                final_answer += f"\n\nSOURCE_DOCUMENT_URL: {cloud_url}"
        except Exception as e:
            print(f"⚠️ Failed to upload report: {e}")

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

